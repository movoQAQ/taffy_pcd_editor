//! PCD's LZF stream contains field-major (SoA) records. Decode bytes without
//! interpreting their values, so COUNT arrays and all extra fields survive.
//! Format references:
//! https://pointclouds.org/documentation/tutorials/pcd_file_format.html
//! https://github.com/PointCloudLibrary/pcl/blob/master/io/src/lzf.cpp

use crate::{invalid, Field, Result};
use std::io::Read;

pub(super) fn read<R: Read>(
    reader: &mut R,
    fields: &[Field],
    points: usize,
    record_size: usize,
    actual_bytes: usize,
) -> Result<Vec<u8>> {
    if actual_bytes < 8 {
        return Err(invalid(
            "binary_compressed payload is missing its size prefix",
        ));
    }
    let mut sizes = [0; 8];
    reader.read_exact(&mut sizes)?;
    let compressed_size = u32::from_le_bytes(sizes[..4].try_into().unwrap()) as usize;
    let uncompressed_size = u32::from_le_bytes(sizes[4..].try_into().unwrap()) as usize;
    let expected_size = points
        .checked_mul(record_size)
        .ok_or_else(|| invalid("POINTS * record size overflow"))?;
    if actual_bytes.checked_sub(8) != Some(compressed_size) {
        return Err(invalid(format!(
            "binary_compressed payload length mismatch: prefix requires {compressed_size} bytes, file has {}",
            actual_bytes - 8
        )));
    }
    if uncompressed_size != expected_size {
        return Err(invalid(format!(
            "binary_compressed uncompressed length mismatch: header requires {expected_size} bytes, prefix has {uncompressed_size}"
        )));
    }
    // Every LZF token emits at most 88 bytes per input byte (264 / 3).
    // Reject impossible expansion before reserving from untrusted lengths.
    if uncompressed_size > compressed_size.saturating_mul(88) {
        return Err(invalid(
            "binary_compressed payload has an impossible LZF expansion size",
        ));
    }
    let mut encoded = allocated_bytes(compressed_size)?;
    reader.read_exact(&mut encoded)?;
    let planar = decompress(&encoded, uncompressed_size)?;
    drop(encoded);
    interleave(&planar, fields, points, record_size)
}

fn allocated_bytes(size: usize) -> Result<Vec<u8>> {
    let mut bytes = Vec::new();
    bytes
        .try_reserve_exact(size)
        .map_err(|error| invalid(format!("cannot allocate PCD payload: {error}")))?;
    bytes.resize(size, 0);
    Ok(bytes)
}

enum Run<'a> {
    Literal(&'a [u8]),
    Backref { distance: usize, length: usize },
}

fn walk_lzf(input: &[u8], expected: usize, mut emit: impl FnMut(Run<'_>)) -> Result<()> {
    let mut cursor = 0;
    let mut produced = 0usize;
    while cursor < input.len() {
        let control = input[cursor];
        cursor += 1;
        let (length, run) = if control < 32 {
            let length = usize::from(control) + 1;
            let end = cursor
                .checked_add(length)
                .filter(|&end| end <= input.len())
                .ok_or_else(|| invalid("truncated LZF literal"))?;
            let run = Run::Literal(&input[cursor..end]);
            cursor = end;
            (length, run)
        } else {
            let mut length = usize::from(control >> 5);
            if length == 7 {
                length += usize::from(
                    *input
                        .get(cursor)
                        .ok_or_else(|| invalid("truncated LZF extended length"))?,
                );
                cursor += 1;
            }
            let low = usize::from(
                *input
                    .get(cursor)
                    .ok_or_else(|| invalid("truncated LZF back reference"))?,
            );
            cursor += 1;
            let distance = (usize::from(control & 31) << 8) + low + 1;
            length += 2;
            if distance > produced {
                return Err(invalid("LZF back reference precedes the output"));
            }
            (length, Run::Backref { distance, length })
        };
        produced = produced
            .checked_add(length)
            .filter(|&size| size <= expected)
            .ok_or_else(|| invalid("LZF output exceeds its declared size"))?;
        emit(run);
    }
    if produced != expected {
        return Err(invalid(format!(
            "LZF output length mismatch: expected {expected} bytes, decoded {produced}"
        )));
    }
    Ok(())
}

fn decompress(input: &[u8], expected: usize) -> Result<Vec<u8>> {
    // Preflight the entire stream before allocating the potentially much larger
    // output. This also rejects malformed late tokens without a large allocation.
    walk_lzf(input, expected, |_| {})?;
    let mut output = allocated_bytes(expected)?;
    let mut cursor = 0;
    walk_lzf(input, expected, |run| match run {
        Run::Literal(bytes) => {
            output[cursor..cursor + bytes.len()].copy_from_slice(bytes);
            cursor += bytes.len();
        }
        Run::Backref { distance, length } => {
            // LZF permits overlapping matches: freshly written bytes can be
            // referenced later in the same run, so memcpy/copy_within is wrong.
            for _ in 0..length {
                output[cursor] = output[cursor - distance];
                cursor += 1;
            }
        }
    })?;
    Ok(output)
}

fn interleave(planar: &[u8], fields: &[Field], points: usize, stride: usize) -> Result<Vec<u8>> {
    let mut total_width = 0usize;
    for field in fields {
        let width = field
            .size
            .checked_mul(field.count)
            .filter(|&width| width > 0)
            .ok_or_else(|| invalid("invalid compressed field width"))?;
        if field.offset != total_width {
            return Err(invalid("invalid compressed field offset"));
        }
        total_width = total_width
            .checked_add(width)
            .ok_or_else(|| invalid("compressed record byte size overflow"))?;
    }
    if total_width != stride || points.checked_mul(stride) != Some(planar.len()) {
        return Err(invalid(
            "compressed field layout does not match its payload",
        ));
    }
    let mut records = allocated_bytes(planar.len())?;
    let mut plane_offset = 0;
    for field in fields {
        let width = field.size * field.count;
        for point in 0..points {
            let source = plane_offset + point * width;
            let destination = point * stride + field.offset;
            records[destination..destination + width]
                .copy_from_slice(&planar[source..source + width]);
        }
        plane_offset += points * width;
    }
    Ok(records)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn literals(bytes: &[u8]) -> Vec<u8> {
        bytes
            .chunks(32)
            .flat_map(|chunk| std::iter::once((chunk.len() - 1) as u8).chain(chunk.iter().copied()))
            .collect()
    }

    fn prefixed(encoded: &[u8], uncompressed: u32) -> Vec<u8> {
        let mut bytes = (encoded.len() as u32).to_le_bytes().to_vec();
        bytes.extend_from_slice(&uncompressed.to_le_bytes());
        bytes.extend_from_slice(encoded);
        bytes
    }

    fn field(name: &str, size: usize, kind: char, count: usize, offset: usize) -> Field {
        Field {
            name: name.to_owned(),
            size,
            kind,
            count,
            offset,
        }
    }

    #[test]
    fn literal_and_overlapping_short_match() {
        assert_eq!(
            decompress(&[2, b'a', b'b', b'c', 0x80, 2], 9).unwrap(),
            b"abcabcabc"
        );
        let raw: Vec<_> = (0..=255).collect();
        assert_eq!(decompress(&literals(&raw), raw.len()).unwrap(), raw);
    }

    #[test]
    fn extended_match_handles_max_length_and_high_distance_bits() {
        assert_eq!(
            decompress(&[0, b'x', 0xe0, 255, 0], 265).unwrap(),
            vec![b'x'; 265]
        );
        let raw: Vec<u8> = (0..8192).map(|index| (index % 251) as u8).collect();
        let mut encoded = literals(&raw);
        encoded.extend_from_slice(&[0x3f, 255]); // Three bytes from distance 8192.
        let mut expected = raw;
        expected.extend_from_within(..3);
        assert_eq!(decompress(&encoded, expected.len()).unwrap(), expected);
    }

    #[test]
    fn preserves_count_arrays_mixed_types_and_exact_float_bits() {
        let fields = [
            field("x", 4, 'F', 1, 0),
            field("normal", 4, 'F', 3, 4),
            field("label", 2, 'I', 1, 16),
            field("stamp", 8, 'U', 1, 18),
        ];
        // Includes negative zero, infinity, and NaN payloads in non-XYZ fields;
        // decoding must preserve their bits, not parse or normalize values.
        let records: Vec<u8> = [1.0f32.to_bits(), 0x8000_0000, 0x7f80_0000, 0x7fc0_1234]
            .into_iter()
            .flat_map(u32::to_le_bytes)
            .chain((-2i16).to_le_bytes())
            .chain(u64::MAX.to_le_bytes())
            .chain(
                [
                    2.0f32.to_bits(),
                    3.0f32.to_bits(),
                    4.0f32.to_bits(),
                    5.0f32.to_bits(),
                ]
                .into_iter()
                .flat_map(u32::to_le_bytes),
            )
            .chain(123i16.to_le_bytes())
            .chain(42u64.to_le_bytes())
            .collect();
        let mut planar = Vec::new();
        for field in &fields {
            for point in 0..2 {
                let offset = point * 26 + field.offset;
                planar.extend_from_slice(&records[offset..offset + field.size * field.count]);
            }
        }
        let bytes = prefixed(&literals(&planar), planar.len() as u32);
        assert_eq!(
            read(&mut bytes.as_slice(), &fields, 2, 26, bytes.len()).unwrap(),
            records
        );
    }

    #[test]
    fn rejects_malformed_lzf_tokens_and_wrong_output_sizes() {
        for (encoded, expected) in [
            (&[3, b'a'][..], 4),                 // Truncated literal.
            (&[0xe0][..], 9),                    // Missing extended length.
            (&[0xe0, 0][..], 9),                 // Missing offset.
            (&[0x20][..], 3),                    // Missing short offset.
            (&[0x20, 0][..], 3),                 // Reference before any output.
            (&[0, b'a', 0x20, 1][..], 4),        // Distance exceeds prior output.
            (&[0, b'a'][..], 0),                 // Excess decoded data.
            (&[0, b'a'][..], 2),                 // Short decoded data.
            (&[0, b'a', 0xe0, 255, 0][..], 264), // Match overrun.
            (&[][..], 1),
        ] {
            assert!(
                decompress(encoded, expected).is_err(),
                "{encoded:?}, {expected}"
            );
        }
    }

    #[test]
    fn rejects_bad_prefix_lengths_truncation_and_impossible_expansion() {
        let fields = [field("byte", 1, 'U', 1, 0)];
        let valid = prefixed(&[0, 42], 1);
        for actual in [0, 7, valid.len() - 1, valid.len() + 1] {
            assert!(read(&mut valid.as_slice(), &fields, 1, 1, actual).is_err());
        }
        assert!(read(&mut valid[..9].as_ref(), &fields, 1, 1, valid.len()).is_err());
        assert!(read(&mut valid.as_slice(), &fields, 2, 1, valid.len()).is_err());
        let forged = prefixed(&[0, 42], u32::MAX);
        let error = read(
            &mut forged.as_slice(),
            &fields,
            u32::MAX as usize,
            1,
            forged.len(),
        )
        .unwrap_err();
        assert!(error.to_string().contains("impossible LZF expansion"));
    }

    #[test]
    fn accepts_empty_cloud_and_rejects_inconsistent_field_layout() {
        let bytes = prefixed(&[], 0);
        assert!(read(
            &mut bytes.as_slice(),
            &[field("x", 4, 'F', 1, 0)],
            0,
            4,
            bytes.len()
        )
        .unwrap()
        .is_empty());
        assert!(interleave(&[0; 4], &[field("x", 4, 'F', 1, 1)], 1, 4).is_err());
        assert!(interleave(&[0; 4], &[field("x", 4, 'F', 2, 0)], 1, 4).is_err());
        assert!(interleave(&[], &[field("x", usize::MAX, 'F', 2, 0)], 0, 4).is_err());
    }
}
