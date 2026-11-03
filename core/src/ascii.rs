//! Streaming ASCII PCD decoding into the same little-endian records as binary PCD.

use std::io::BufRead;

use crate::{invalid, Field, Result};

pub(super) fn read<R: BufRead>(
    reader: &mut R,
    fields: &[Field],
    points: usize,
    record_size: usize,
    actual_bytes: usize,
) -> Result<Vec<u8>> {
    let columns = fields.iter().try_fold(0usize, |total, field| {
        total
            .checked_add(field.count)
            .ok_or_else(|| invalid("ASCII field count overflow"))
    })?;
    // Every value needs at least one byte, and adjacent values/records need a
    // separator. Check the file size before allocating from an untrusted header.
    let minimum_bytes = points
        .checked_mul(columns)
        .and_then(|values| values.checked_mul(2))
        .map(|bytes| bytes.saturating_sub(1))
        .ok_or_else(|| invalid("ASCII point count overflow"))?;
    if minimum_bytes > actual_bytes {
        return Err(invalid(format!(
            "ASCII payload is too short: {points} points with {columns} values each require at least {minimum_bytes} bytes, file has {actual_bytes}"
        )));
    }
    let expected_bytes = points
        .checked_mul(record_size)
        .ok_or_else(|| invalid("ASCII record byte size overflow"))?;
    let mut payload = Vec::new();
    let mut line = String::new();
    let mut parsed_points = 0usize;
    let mut consumed = 0usize;
    let mut line_number = 0usize;
    loop {
        line.clear();
        let read_bytes = reader.read_line(&mut line)?;
        if read_bytes == 0 {
            break;
        }
        consumed = consumed
            .checked_add(read_bytes)
            .ok_or_else(|| invalid("ASCII payload byte size overflow"))?;
        if consumed > actual_bytes {
            return Err(invalid("PCD file grew while reading its ASCII payload"));
        }
        line_number += 1;
        let mut values = line.split_ascii_whitespace();
        // Harmless blank lines, including a final whitespace-only line, carry
        // no point. Non-ASCII whitespace and comments are not numeric values.
        if values.clone().next().is_none() {
            continue;
        }
        if parsed_points == points {
            return Err(invalid(format!(
                "ASCII payload has more than the declared {points} points (data line {line_number})"
            )));
        }
        let value_count = values.clone().count();
        if value_count != columns {
            return Err(invalid(format!(
                "ASCII point {parsed_points} (data line {line_number}) has {value_count} values; expected {columns} from FIELDS/COUNT"
            )));
        }
        // Grow only as complete records are encountered, rather than reserving
        // POINTS * record_size before verifying the ASCII payload.
        payload
            .try_reserve(record_size)
            .map_err(|error| invalid(format!("cannot allocate ASCII PCD payload: {error}")))?;
        let record_start = payload.len();
        for field in fields {
            for component in 0..field.count {
                let value = values.next().expect("validated ASCII column count");
                append_value(&mut payload, value, field).map_err(|error| {
                    invalid(format!(
                        "ASCII point {parsed_points}, field {}[{component}]: {error}",
                        field.name
                    ))
                })?;
            }
        }
        debug_assert_eq!(payload.len() - record_start, record_size);
        parsed_points += 1;
    }
    if consumed != actual_bytes {
        return Err(invalid("PCD file shrank while reading its ASCII payload"));
    }
    if parsed_points != points {
        return Err(invalid(format!(
            "ASCII point count mismatch: header declares {points}, payload has {parsed_points}"
        )));
    }
    debug_assert_eq!(payload.len(), expected_bytes);
    Ok(payload)
}

fn append_value(payload: &mut Vec<u8>, value: &str, field: &Field) -> Result<()> {
    macro_rules! integer {
        ($type:ty) => {{
            let number = value.parse::<$type>().map_err(|_| {
                invalid(concat!(
                    "invalid or out-of-range ",
                    stringify!($type),
                    " value"
                ))
            })?;
            payload.extend_from_slice(&number.to_le_bytes());
        }};
    }
    macro_rules! float {
        ($type:ty) => {{
            // Parse directly at the declared precision, avoiding f64 -> f32
            // double rounding. Explicit NaN/infinity are valid auxiliary data;
            // the cloud reader separately rejects non-finite XYZ coordinates.
            let number = value
                .parse::<$type>()
                .map_err(|_| invalid(concat!("invalid ", stringify!($type), " value")))?;
            if number.is_infinite() && !is_infinity(value) {
                return Err(invalid(concat!(
                    "out-of-range ",
                    stringify!($type),
                    " value"
                )));
            }
            payload.extend_from_slice(&number.to_le_bytes());
        }};
    }
    match (field.kind, field.size) {
        ('I', 1) => integer!(i8),
        ('I', 2) => integer!(i16),
        ('I', 4) => integer!(i32),
        ('I', 8) => integer!(i64),
        ('U', 1) => integer!(u8),
        ('U', 2) => integer!(u16),
        ('U', 4) => integer!(u32),
        ('U', 8) => integer!(u64),
        ('F', 4) => float!(f32),
        ('F', 8) => float!(f64),
        _ => return Err(invalid("unsupported ASCII TYPE/SIZE")),
    }
    Ok(())
}

fn is_infinity(value: &str) -> bool {
    let unsigned = value.strip_prefix(['+', '-']).unwrap_or(value);
    unsigned.eq_ignore_ascii_case("inf") || unsigned.eq_ignore_ascii_case("infinity")
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::{BufReader, Cursor};

    fn fields(specs: &[(char, usize, usize)]) -> Vec<Field> {
        let mut offset = 0;
        specs
            .iter()
            .enumerate()
            .map(|(index, &(kind, size, count))| {
                let field = Field {
                    name: format!("field{index}"),
                    size,
                    kind,
                    count,
                    offset,
                };
                offset += size * count;
                field
            })
            .collect()
    }

    fn decode(text: &str, fields: &[Field], points: usize) -> Result<Vec<u8>> {
        let record_size = fields.iter().map(|field| field.size * field.count).sum();
        // Deliberately split both numbers and CRLF across tiny read buffers.
        let mut reader = BufReader::with_capacity(3, Cursor::new(text.as_bytes()));
        read(&mut reader, fields, points, record_size, text.len())
    }

    #[test]
    fn parses_every_numeric_type_and_count_in_field_order() {
        let fields = fields(&[
            ('F', 4, 2),
            ('I', 1, 1),
            ('U', 1, 1),
            ('I', 2, 1),
            ('U', 2, 1),
            ('I', 4, 1),
            ('U', 4, 1),
            ('I', 8, 1),
            ('U', 8, 1),
            ('F', 8, 1),
        ]);
        let payload = decode(
            "1.25e+2\t-0 -128 255 -32768 65535 -2147483648 4294967295 -9223372036854775808 18446744073709551615 -2.5e-100\r\n",
            &fields,
            1,
        )
        .unwrap();
        let mut expected = Vec::new();
        expected.extend_from_slice(&125.0_f32.to_le_bytes());
        expected.extend_from_slice(&(-0.0_f32).to_le_bytes());
        expected.extend_from_slice(&i8::MIN.to_le_bytes());
        expected.extend_from_slice(&u8::MAX.to_le_bytes());
        expected.extend_from_slice(&i16::MIN.to_le_bytes());
        expected.extend_from_slice(&u16::MAX.to_le_bytes());
        expected.extend_from_slice(&i32::MIN.to_le_bytes());
        expected.extend_from_slice(&u32::MAX.to_le_bytes());
        expected.extend_from_slice(&i64::MIN.to_le_bytes());
        expected.extend_from_slice(&u64::MAX.to_le_bytes());
        expected.extend_from_slice(&(-2.5e-100_f64).to_le_bytes());
        assert_eq!(payload, expected);
    }

    #[test]
    fn rounds_f32_directly_without_f64_intermediate() {
        let payload = decode(
            "1.00000005960464477539062500000000000000000000000000000000000000000000000000000000001",
            &fields(&[('F', 4, 1)]),
            1,
        )
        .unwrap();
        assert_eq!(payload, (1.0_f32.to_bits() + 1).to_le_bytes());
    }

    #[test]
    fn accepts_explicit_nonfinite_auxiliary_floats() {
        let payload = decode(
            "nan +inf -Infinity NaN\n",
            &fields(&[('F', 4, 3), ('F', 8, 1)]),
            1,
        )
        .unwrap();
        assert!(f32::from_le_bytes(payload[0..4].try_into().unwrap()).is_nan());
        assert_eq!(&payload[4..8], &f32::INFINITY.to_le_bytes());
        assert_eq!(&payload[8..12], &f32::NEG_INFINITY.to_le_bytes());
        assert!(f64::from_le_bytes(payload[12..20].try_into().unwrap()).is_nan());
    }

    #[test]
    fn rejects_invalid_and_out_of_range_numbers() {
        for (kind, size, value) in [
            ('I', 1, "128"),
            ('I', 2, "-32769"),
            ('I', 4, "2147483648"),
            ('I', 8, "-9223372036854775809"),
            ('U', 1, "256"),
            ('U', 2, "65536"),
            ('U', 4, "4294967296"),
            ('U', 8, "18446744073709551616"),
            ('U', 8, "-1"),
            ('I', 4, "1.0"),
            ('I', 4, "1e2"),
            ('F', 4, "1e100"),
            ('F', 8, "-1e999"),
            ('F', 4, "garbage"),
            ('F', 4, "0x123"),
            ('F', 8, "1\u{a0}2"),
        ] {
            assert!(
                decode(value, &fields(&[(kind, size, 1)]), 1).is_err(),
                "accepted {kind}{size} value {value}"
            );
        }
    }

    #[test]
    fn validates_point_count_and_each_line_width() {
        let fields = fields(&[('F', 4, 3)]);
        for (text, points) in [
            ("0 1\n2 3 4 5\n", 2),
            ("0 1 2 3\n", 1),
            ("0 1 2\n3 4 5\n", 1),
            ("100 101 102\n", 2),
            ("0 1 2 # comment\n", 1),
        ] {
            assert!(decode(text, &fields, points).is_err());
        }
    }

    #[test]
    fn handles_blank_lines_empty_cloud_and_final_line_without_newline() {
        let fields = fields(&[('U', 1, 2)]);
        assert_eq!(
            decode("\n 1\t2\r\n\n3 4", &fields, 2).unwrap(),
            [1, 2, 3, 4]
        );
        assert!(decode("", &fields, 0).unwrap().is_empty());
        assert!(decode("\n \t\r\n", &fields, 0).unwrap().is_empty());
        assert!(decode("1 2", &fields, 0).is_err());
    }

    #[test]
    fn rejects_forged_point_counts_before_reading_or_allocating() {
        struct Unreadable;
        impl std::io::Read for Unreadable {
            fn read(&mut self, _: &mut [u8]) -> std::io::Result<usize> {
                panic!("must reject metadata before reading");
            }
        }
        impl BufRead for Unreadable {
            fn fill_buf(&mut self) -> std::io::Result<&[u8]> {
                panic!("must reject metadata before reading");
            }
            fn consume(&mut self, _: usize) {
                panic!("must reject metadata before reading");
            }
        }
        let fields = fields(&[('F', 4, 3)]);
        assert!(read(&mut Unreadable, &fields, usize::MAX, 12, 8).is_err());
        assert!(read(&mut Unreadable, &fields, 1_000_000_000, 12, 8).is_err());
    }

    #[test]
    fn detects_payload_size_changes_and_invalid_utf8() {
        let fields = fields(&[('U', 1, 1)]);
        assert!(read(&mut Cursor::new(b"1\n"), &fields, 1, 1, 1).is_err());
        assert!(read(&mut Cursor::new(b"1\n"), &fields, 1, 1, 3).is_err());
        assert!(read(&mut Cursor::new(b"\xff\n"), &fields, 1, 1, 2).is_err());
    }
}
