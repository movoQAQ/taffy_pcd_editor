//! Small binary PCD core. Records stay in their original little-endian layout;
//! filtering changes only their order and selection, including extra fields.

use std::collections::{HashMap, HashSet};
use std::fmt;
use std::fs::{self, File, OpenOptions};
use std::io::{BufRead, BufReader, BufWriter, Read, Write};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

const MAX_HEADER_BYTES: usize = 1024 * 1024;
static TEMP_COUNTER: AtomicU64 = AtomicU64::new(0);

#[derive(Debug)]
pub struct Error(String);

impl fmt::Display for Error {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.0.fmt(formatter)
    }
}

impl std::error::Error for Error {}

impl From<std::io::Error> for Error {
    fn from(error: std::io::Error) -> Self {
        Self(error.to_string())
    }
}

pub type Result<T> = std::result::Result<T, Error>;

fn invalid(message: impl Into<String>) -> Error {
    Error(message.into())
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Field {
    pub name: String,
    pub size: usize,
    pub kind: char,
    pub count: usize,
    pub offset: usize,
}

#[derive(Debug)]
pub struct Selection {
    /// Outside-range records first, then the first in-range record per voxel.
    /// Each group retains its input order.
    pub indices: Vec<usize>,
    pub in_range: usize,
}

#[derive(Debug)]
pub struct PointCloud {
    fields: Vec<Field>,
    xyz_fields: [usize; 3],
    record_size: usize,
    points: usize,
    payload: Vec<u8>,
    bounds: Option<[[f32; 2]; 3]>,
    version: String,
    viewpoint: String,
    source: PathBuf,
    #[cfg(unix)]
    source_identity: (u64, u64),
}

impl PointCloud {
    pub fn read(path: &Path) -> Result<Self> {
        let file = File::open(path)?;
        let metadata = file.metadata()?;
        if !metadata.is_file() {
            return Err(invalid("PCD input must be a regular file"));
        }
        let file_size = usize::try_from(metadata.len())
            .map_err(|_| invalid("PCD file is too large for this platform"))?;
        let mut reader = BufReader::new(file);
        let (header, header_size) = read_header(&mut reader)?;
        let data = header_values(&header, "DATA")?;
        if data.as_slice() != ["binary"] {
            return Err(invalid(
                "only DATA binary is supported; ASCII and binary_compressed are not supported",
            ));
        }
        let version = match header.get("VERSION") {
            Some(values) if values.len() == 1 && matches!(values[0].as_str(), ".7" | "0.7") => {
                values[0].clone()
            }
            Some(_) => return Err(invalid("VERSION must be .7 or 0.7")),
            None => "0.7".to_owned(),
        };
        let names = header_values(&header, "FIELDS")?;
        let sizes = header_values(&header, "SIZE")?;
        let kinds = header_values(&header, "TYPE")?;
        let counts = header.get("COUNT");
        if names.is_empty()
            || sizes.len() != names.len()
            || kinds.len() != names.len()
            || counts.is_some_and(|values| values.len() != names.len())
        {
            return Err(invalid(
                "FIELDS, SIZE, TYPE and COUNT must have matching nonempty lengths",
            ));
        }
        let mut fields = Vec::with_capacity(names.len());
        let mut distinct = HashSet::new();
        let mut record_size = 0usize;
        for (index, name) in names.iter().enumerate() {
            if name.starts_with('#') || !distinct.insert(name) {
                return Err(invalid(format!("invalid or duplicate field: {name}")));
            }
            let size = parse_usize(&sizes[index], "SIZE")?;
            let kind = match kinds[index].as_str() {
                "F" if matches!(size, 4 | 8) => 'F',
                "I" if matches!(size, 1 | 2 | 4 | 8) => 'I',
                "U" if matches!(size, 1 | 2 | 4 | 8) => 'U',
                _ => return Err(invalid(format!("unsupported TYPE/SIZE for field {name}"))),
            };
            let count = match counts {
                Some(values) => parse_usize(&values[index], "COUNT")?,
                None => 1,
            };
            if count == 0 {
                return Err(invalid("COUNT must be greater than zero"));
            }
            let width = size
                .checked_mul(count)
                .ok_or_else(|| invalid("field byte size overflow"))?;
            fields.push(Field {
                name: name.clone(),
                size,
                kind,
                count,
                offset: record_size,
            });
            record_size = record_size
                .checked_add(width)
                .ok_or_else(|| invalid("record byte size overflow"))?;
        }
        let mut xyz_fields = [0; 3];
        for (axis, name) in ["x", "y", "z"].iter().enumerate() {
            let index = fields
                .iter()
                .position(|field| field.name == *name)
                .ok_or_else(|| invalid(format!("missing XYZ field: {name}")))?;
            if fields[index].kind != 'F' || fields[index].count != 1 {
                return Err(invalid(format!(
                    "XYZ field {name} must have TYPE F, SIZE 4 or 8, COUNT 1"
                )));
            }
            xyz_fields[axis] = index;
        }
        let points = header_integer(&header, "POINTS")?;
        let width = header_integer(&header, "WIDTH")?;
        let height = header_integer(&header, "HEIGHT")?;
        if height == 0 || width.checked_mul(height) != Some(points) {
            return Err(invalid(
                "WIDTH * HEIGHT must equal POINTS and HEIGHT must be positive",
            ));
        }
        let expected_bytes = points
            .checked_mul(record_size)
            .ok_or_else(|| invalid("POINTS * record size overflow"))?;
        let actual_bytes = file_size
            .checked_sub(header_size)
            .ok_or_else(|| invalid("PCD file changed while reading its header"))?;
        if expected_bytes != actual_bytes {
            return Err(invalid(format!("binary payload length mismatch: header requires {expected_bytes} bytes, file has {actual_bytes}")));
        }
        let viewpoint = match header.get("VIEWPOINT") {
            Some(values) => {
                if values.len() != 7
                    || values.iter().any(|value| {
                        value
                            .parse::<f64>()
                            .map_or(true, |number| !number.is_finite())
                    })
                {
                    return Err(invalid("VIEWPOINT must contain seven finite numbers"));
                }
                values.join(" ")
            }
            None => "0 0 0 1 0 0 0".to_owned(),
        };
        // Validate the real file length before reserving from untrusted POINTS.
        let mut payload = Vec::new();
        payload
            .try_reserve_exact(actual_bytes)
            .map_err(|error| invalid(format!("cannot allocate PCD payload: {error}")))?;
        payload.resize(actual_bytes, 0);
        reader.read_exact(&mut payload)?;
        let mut trailing = [0];
        if reader.read(&mut trailing)? != 0 {
            return Err(invalid("PCD file grew while reading its payload"));
        }
        let source = fs::canonicalize(path)?;
        #[cfg(unix)]
        let source_identity = {
            use std::os::unix::fs::MetadataExt;
            (metadata.dev(), metadata.ino())
        };
        let mut cloud = Self {
            fields,
            xyz_fields,
            record_size,
            points,
            payload,
            bounds: None,
            version,
            viewpoint,
            source,
            #[cfg(unix)]
            source_identity,
        };
        for index in 0..points {
            let point = cloud.xyz(index);
            if point.iter().any(|value| !value.is_finite()) {
                return Err(invalid(format!(
                    "point {index} has non-finite XYZ or an XYZ value outside float32 range"
                )));
            }
            match cloud.bounds.as_mut() {
                Some(bounds) => {
                    for axis in 0..3 {
                        bounds[axis][0] = bounds[axis][0].min(point[axis]);
                        bounds[axis][1] = bounds[axis][1].max(point[axis]);
                    }
                }
                None => cloud.bounds = Some(point.map(|value| [value, value])),
            }
        }
        Ok(cloud)
    }

    pub fn len(&self) -> usize {
        self.points
    }

    pub fn is_empty(&self) -> bool {
        self.points == 0
    }

    pub fn fields(&self) -> &[Field] {
        &self.fields
    }

    pub fn record_size(&self) -> usize {
        self.record_size
    }

    pub fn payload_bytes(&self) -> usize {
        self.payload.len()
    }

    pub fn bounds(&self) -> Option<[[f32; 2]; 3]> {
        self.bounds
    }

    /// Returns the validated coordinates converted to float32, as in the editor.
    /// Panics when `index >= len()`, like slice indexing.
    pub fn xyz(&self, index: usize) -> [f32; 3] {
        assert!(index < self.points, "point index out of bounds");
        self.xyz_fields.map(|field_index| {
            let field = &self.fields[field_index];
            let start = index * self.record_size + field.offset;
            if field.size == 4 {
                f32::from_le_bytes(self.payload[start..start + 4].try_into().unwrap())
            } else {
                f64::from_le_bytes(self.payload[start..start + 8].try_into().unwrap()) as f32
            }
        })
    }

    /// Inclusive ranges and float32 division/floor match NumPy's voxel filter.
    /// Coordinates outside the range are retained, without voxel filtering.
    pub fn select(&self, ranges: [[f32; 2]; 3], voxel: f32) -> Result<Selection> {
        if !voxel.is_finite() || voxel <= 0.0 {
            return Err(invalid("voxel size must be finite and positive"));
        }
        if ranges
            .iter()
            .any(|range| !range[0].is_finite() || !range[1].is_finite() || range[0] > range[1])
        {
            return Err(invalid(
                "each range must have finite bounds with minimum <= maximum",
            ));
        }
        let inside = |point: [f32; 3]| {
            (0..3).all(|axis| point[axis] >= ranges[axis][0] && point[axis] <= ranges[axis][1])
        };
        let mut indices = Vec::new();
        indices
            .try_reserve_exact(self.points)
            .map_err(|error| invalid(format!("cannot allocate selection: {error}")))?;
        // Two passes preserve outside-first ordering without a second index array.
        for index in 0..self.points {
            if !inside(self.xyz(index)) {
                indices.push(index);
            }
        }
        let in_range = self.points - indices.len();
        let mut occupied = HashSet::new();
        occupied
            .try_reserve(in_range)
            .map_err(|error| invalid(format!("cannot allocate voxel table: {error}")))?;
        for index in 0..self.points {
            let point = self.xyz(index);
            if !inside(point) {
                continue;
            }
            let mut cell = [0i32; 3];
            for axis in 0..3 {
                let coordinate = (point[axis] / voxel).floor();
                // i32::MAX cannot be represented exactly by f32; compare in f64.
                if !coordinate.is_finite()
                    || (coordinate as f64) < i32::MIN as f64
                    || (coordinate as f64) > i32::MAX as f64
                {
                    return Err(invalid(format!(
                        "point {index} voxel coordinate is outside int32 range"
                    )));
                }
                cell[axis] = coordinate as i32;
            }
            if occupied.insert(cell) {
                indices.push(index);
            }
        }
        Ok(Selection { indices, in_range })
    }

    /// Publishes a complete new binary PCD atomically, without replacing any path.
    /// All selected records and their extra fields are preserved byte-for-byte.
    pub fn write_selected(&self, path: &Path, indices: &[usize]) -> Result<()> {
        if indices.iter().any(|&index| index >= self.points) {
            return Err(invalid("selection contains an out-of-bounds point index"));
        }
        indices
            .len()
            .checked_mul(self.record_size)
            .ok_or_else(|| invalid("output payload size overflow"))?;
        let parent = path
            .parent()
            .filter(|parent| !parent.as_os_str().is_empty())
            .unwrap_or_else(|| Path::new("."));
        let filename = path
            .file_name()
            .ok_or_else(|| invalid("output path must name a file"))?;
        let resolved = fs::canonicalize(parent)?.join(filename);
        if resolved == self.source {
            return Err(invalid("refusing to overwrite the input PCD"));
        }
        match fs::symlink_metadata(path) {
            Ok(_) => {
                #[cfg(unix)]
                if let Ok(metadata) = fs::metadata(path) {
                    use std::os::unix::fs::MetadataExt;
                    if (metadata.dev(), metadata.ino()) == self.source_identity {
                        return Err(invalid("refusing to overwrite an alias of the input PCD"));
                    }
                }
                return Err(invalid("output already exists; choose a new output path"));
            }
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => {}
            Err(error) => return Err(error.into()),
        }
        let (temporary, file) = TemporaryFile::create(parent)?;
        let mut writer = BufWriter::new(file);
        writeln!(writer, "# .PCD v0.7 - Point Cloud Data file format")?;
        writeln!(writer, "VERSION {}", self.version)?;
        writeln!(
            writer,
            "FIELDS {}",
            self.fields
                .iter()
                .map(|field| field.name.as_str())
                .collect::<Vec<_>>()
                .join(" ")
        )?;
        writeln!(
            writer,
            "SIZE {}",
            self.fields
                .iter()
                .map(|field| field.size.to_string())
                .collect::<Vec<_>>()
                .join(" ")
        )?;
        writeln!(
            writer,
            "TYPE {}",
            self.fields
                .iter()
                .map(|field| field.kind.to_string())
                .collect::<Vec<_>>()
                .join(" ")
        )?;
        writeln!(
            writer,
            "COUNT {}",
            self.fields
                .iter()
                .map(|field| field.count.to_string())
                .collect::<Vec<_>>()
                .join(" ")
        )?;
        writeln!(
            writer,
            "WIDTH {}\nHEIGHT 1\nVIEWPOINT {}\nPOINTS {}\nDATA binary",
            indices.len(),
            self.viewpoint,
            indices.len()
        )?;
        for &index in indices {
            let start = index * self.record_size;
            writer.write_all(&self.payload[start..start + self.record_size])?;
        }
        writer.flush()?;
        writer.get_ref().sync_all()?;
        // A same-directory hard link publishes atomically and never replaces an
        // existing file, even if another process creates it after the check.
        fs::hard_link(&temporary.0, path)?;
        Ok(())
    }
}

fn read_header<R: BufRead>(reader: &mut R) -> Result<(HashMap<String, Vec<String>>, usize)> {
    let mut header = HashMap::new();
    let mut total = 0usize;
    loop {
        let mut line = Vec::new();
        loop {
            let bytes = reader.fill_buf()?;
            if bytes.is_empty() {
                return Err(invalid("incomplete PCD header"));
            }
            let end = bytes
                .iter()
                .position(|&byte| byte == b'\n')
                .map(|position| position + 1);
            let length = end.unwrap_or(bytes.len());
            total = total
                .checked_add(length)
                .ok_or_else(|| invalid("header size overflow"))?;
            if total > MAX_HEADER_BYTES {
                return Err(invalid("PCD header exceeds 1 MiB limit"));
            }
            line.extend_from_slice(&bytes[..length]);
            reader.consume(length);
            if end.is_some() {
                break;
            }
        }
        if !line
            .iter()
            .all(|byte| byte.is_ascii_graphic() || matches!(byte, b' ' | b'\t' | b'\r' | b'\n'))
        {
            return Err(invalid("PCD header must be printable ASCII or whitespace"));
        }
        let line = std::str::from_utf8(&line).unwrap();
        let mut tokens = line.split_ascii_whitespace();
        let Some(keyword) = tokens.next() else {
            continue;
        };
        if keyword.starts_with('#') {
            continue;
        }
        let keyword = keyword.to_ascii_uppercase();
        if !matches!(
            keyword.as_str(),
            "VERSION"
                | "FIELDS"
                | "SIZE"
                | "TYPE"
                | "COUNT"
                | "WIDTH"
                | "HEIGHT"
                | "VIEWPOINT"
                | "POINTS"
                | "DATA"
        ) {
            return Err(invalid(format!("unknown PCD header keyword: {keyword}")));
        }
        if header.contains_key(&keyword) {
            return Err(invalid(format!("duplicate PCD header keyword: {keyword}")));
        }
        let is_data = keyword == "DATA";
        header.insert(keyword, tokens.map(str::to_owned).collect());
        if is_data {
            return Ok((header, total));
        }
    }
}

fn header_values<'a>(
    header: &'a HashMap<String, Vec<String>>,
    key: &str,
) -> Result<&'a Vec<String>> {
    header
        .get(key)
        .ok_or_else(|| invalid(format!("missing PCD header keyword: {key}")))
}

fn parse_usize(value: &str, name: &str) -> Result<usize> {
    if value.is_empty() || !value.bytes().all(|byte| byte.is_ascii_digit()) {
        return Err(invalid(format!(
            "{name} must be a nonnegative decimal integer"
        )));
    }
    value
        .parse()
        .map_err(|_| invalid(format!("{name} integer overflow")))
}

fn header_integer(header: &HashMap<String, Vec<String>>, name: &str) -> Result<usize> {
    let values = header_values(header, name)?;
    if values.len() != 1 {
        return Err(invalid(format!("{name} requires exactly one integer")));
    }
    parse_usize(&values[0], name)
}

struct TemporaryFile(PathBuf);

impl TemporaryFile {
    fn create(parent: &Path) -> Result<(Self, File)> {
        for _ in 0..100 {
            let sequence = TEMP_COUNTER.fetch_add(1, Ordering::Relaxed);
            let path = parent.join(format!(".taffy-pcd-{}-{sequence}.tmp", std::process::id()));
            match OpenOptions::new().write(true).create_new(true).open(&path) {
                Ok(file) => return Ok((Self(path), file)),
                Err(error) if error.kind() == std::io::ErrorKind::AlreadyExists => continue,
                Err(error) => return Err(error.into()),
            }
        }
        Err(invalid("could not create a unique temporary output file"))
    }
}

impl Drop for TemporaryFile {
    fn drop(&mut self) {
        let _ = fs::remove_file(&self.0);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    struct TestDirectory(PathBuf);
    impl TestDirectory {
        fn new() -> Self {
            let path = std::env::temp_dir().join(format!(
                "taffy-core-test-{}-{}",
                std::process::id(),
                TEMP_COUNTER.fetch_add(1, Ordering::Relaxed)
            ));
            fs::create_dir(&path).unwrap();
            Self(path)
        }
        fn write(&self, name: &str, header: &str, payload: &[u8]) -> PathBuf {
            let path = self.0.join(name);
            let mut file = File::create(&path).unwrap();
            file.write_all(header.as_bytes()).unwrap();
            file.write_all(payload).unwrap();
            path
        }
    }
    impl Drop for TestDirectory {
        fn drop(&mut self) {
            let _ = fs::remove_dir_all(&self.0);
        }
    }

    fn header(points: usize) -> String {
        format!("VERSION .7\nFIELDS x y z\nSIZE 4 4 4\nTYPE F F F\nCOUNT 1 1 1\nWIDTH {points}\nHEIGHT 1\nVIEWPOINT 1 2 3 1 0 0 0\nPOINTS {points}\nDATA binary\n")
    }

    fn xyz_bytes(points: &[[f32; 3]]) -> Vec<u8> {
        points
            .iter()
            .flatten()
            .flat_map(|value| value.to_le_bytes())
            .collect()
    }

    #[test]
    fn reordered_float64_and_count_fields_survive_selection() {
        let directory = TestDirectory::new();
        let header = "VERSION .7\nFIELDS z descriptor x normal y\nSIZE 8 2 4 4 4\nTYPE F U F F F\nCOUNT 1 3 1 3 1\nWIDTH 2\nHEIGHT 1\nVIEWPOINT 1 2 3 0.5 0.5 0.5 0.5\nPOINTS 2\nDATA binary\n";
        let mut bytes = Vec::new();
        for point in 0..2 {
            bytes.extend_from_slice(&(point as f64 + 0.25).to_le_bytes());
            for number in [5u16, 7, 9] {
                bytes.extend_from_slice(&number.to_le_bytes());
            }
            bytes.extend_from_slice(&(point as f32 + 1.0).to_le_bytes());
            for number in [0.0f32, 1.0, -1.0] {
                bytes.extend_from_slice(&number.to_le_bytes());
            }
            bytes.extend_from_slice(&(point as f32 - 2.0).to_le_bytes());
        }
        let path = directory.write("source.pcd", header, &bytes);
        let cloud = PointCloud::read(&path).unwrap();
        assert_eq!(cloud.xyz(1), [2.0, -1.0, 1.25]);
        assert_eq!(cloud.record_size(), 34);
        assert_eq!(
            cloud.bounds(),
            Some([[1.0, 2.0], [-2.0, -1.0], [0.25, 1.25]])
        );
        let output = directory.0.join("selected.pcd");
        cloud.write_selected(&output, &[1, 0]).unwrap();
        let written = PointCloud::read(&output).unwrap();
        assert_eq!(written.fields(), cloud.fields());
        assert_eq!(written.viewpoint, cloud.viewpoint);
        assert_eq!(written.version, cloud.version);
        assert_eq!(&written.payload[..34], &bytes[34..]);
        assert_eq!(&written.payload[34..], &bytes[..34]);
        assert_eq!(
            fs::read(path).unwrap(),
            [header.as_bytes(), &bytes].concat()
        );
    }

    #[test]
    fn voxel_filter_uses_floor_inclusive_bounds_and_input_order() {
        let directory = TestDirectory::new();
        let coordinates = [-0.1, -0.09, -0.05, -0.01, 0.0, 0.049999997, 0.05, 0.1, 2.0];
        let points: Vec<_> = coordinates.map(|x| [x, 0.0, 0.0]).into();
        let path = directory.write("source.pcd", &header(points.len()), &xyz_bytes(&points));
        let cloud = PointCloud::read(&path).unwrap();
        let result = cloud
            .select([[-0.1, 0.1], [0.0, 0.0], [0.0, 0.0]], 0.05)
            .unwrap();
        assert_eq!(result.in_range, 8);
        assert_eq!(result.indices, [8, 0, 2, 4, 6, 7]);
        let outside = cloud
            .select([[3.0, 4.0], [0.0, 0.0], [0.0, 0.0]], 0.05)
            .unwrap();
        assert_eq!(outside.in_range, 0);
        assert_eq!(outside.indices, (0..points.len()).collect::<Vec<_>>());
    }

    #[test]
    fn empty_cloud_and_default_count_are_supported() {
        let directory = TestDirectory::new();
        let path = directory.write("empty.pcd", &header(0).replace("COUNT 1 1 1\n", ""), &[]);
        let cloud = PointCloud::read(&path).unwrap();
        assert!(cloud.is_empty());
        assert_eq!(cloud.bounds(), None);
        assert!(cloud
            .select([[0.0, 1.0]; 3], 0.1)
            .unwrap()
            .indices
            .is_empty());
        let output = directory.0.join("output.pcd");
        cloud.write_selected(&output, &[]).unwrap();
        assert!(PointCloud::read(&output).unwrap().is_empty());
    }

    #[test]
    fn malformed_headers_payloads_and_nonfinite_coordinates_are_rejected() {
        let directory = TestDirectory::new();
        let normal = header(1);
        let payload = xyz_bytes(&[[1.0, 2.0, 3.0]]);
        let bad_headers = [
            normal.replace("FIELDS x y z", "FIELDS x y z\0"),
            normal.replace("FIELDS x y z", "FIELDS x x z"),
            normal.replace("FIELDS x y z", "FIELDS x y intensity"),
            normal.replace("SIZE 4 4 4", "SIZE 4 4"),
            normal.replace("SIZE 4 4 4", "SIZE 4 4 3"),
            normal.replace("COUNT 1 1 1", "COUNT 1 1 0"),
            normal.replace("COUNT 1 1 1", "COUNT 1 1 2"),
            normal.replace("TYPE F F F", "TYPE F F U"),
            normal.replace("WIDTH 1", "WIDTH 2"),
            normal.replace("HEIGHT 1", "HEIGHT 0"),
            normal.replace("POINTS 1", "POINTS -1"),
            normal
                .replace("WIDTH 1", "WIDTH 18446744073709551615")
                .replace("POINTS 1", "POINTS 18446744073709551615"),
            normal.replace("DATA binary", "DATA ascii"),
            normal.replace("DATA binary", "DATA binary_compressed"),
            normal.replace("DATA binary", "WIDTH 1\nDATA binary"),
            normal.replace("VIEWPOINT 1 2 3 1 0 0 0", "VIEWPOINT nan 2 3 1 0 0 0"),
            normal.replace("DATA binary\n", ""),
        ];
        for (index, header) in bad_headers.iter().enumerate() {
            let path = directory.write(&format!("bad-{index}.pcd"), header, &payload);
            assert!(
                PointCloud::read(&path).is_err(),
                "accepted bad header {index}"
            );
        }
        for bytes in [&payload[..11], &[0u8; 13][..]] {
            let path = directory.write("length.pcd", &normal, bytes);
            assert!(PointCloud::read(&path).is_err());
        }
        for value in [f32::NAN, f32::INFINITY, f32::NEG_INFINITY] {
            let path = directory.write("nonfinite.pcd", &normal, &xyz_bytes(&[[value, 0.0, 0.0]]));
            assert!(PointCloud::read(&path).is_err());
        }
        let mut f64_payload = Vec::new();
        for value in [f64::MAX, 0.0, 0.0] {
            f64_payload.extend_from_slice(&value.to_le_bytes());
        }
        let path = directory.write(
            "f64-overflow.pcd",
            &normal.replace("SIZE 4 4 4", "SIZE 8 8 8"),
            &f64_payload,
        );
        assert!(PointCloud::read(&path).is_err());
        let path = directory.write("large-header.pcd", &"#".repeat(MAX_HEADER_BYTES + 1), &[]);
        assert!(PointCloud::read(&path)
            .unwrap_err()
            .to_string()
            .contains("1 MiB"));
    }

    #[test]
    fn invalid_filter_parameters_and_int32_overflow_are_rejected() {
        let directory = TestDirectory::new();
        let path = directory.write("source.pcd", &header(1), &xyz_bytes(&[[1.0, 0.0, 0.0]]));
        let cloud = PointCloud::read(&path).unwrap();
        for voxel in [0.0, -1.0, f32::NAN, f32::INFINITY, f32::MIN_POSITIVE] {
            assert!(cloud.select([[0.0, 2.0]; 3], voxel).is_err());
        }
        assert!(cloud.select([[1.0, 0.0]; 3], 0.1).is_err());
        assert!(cloud.select([[0.0, f32::INFINITY]; 3], 0.1).is_err());
        let path = directory.write(
            "limit.pcd",
            &header(2),
            &xyz_bytes(&[[i32::MIN as f32, 0.0, 0.0], [2147483648.0, 0.0, 0.0]]),
        );
        let cloud = PointCloud::read(&path).unwrap();
        assert!(cloud.select(cloud.bounds().unwrap(), 1.0).is_err());
        assert_eq!(
            cloud
                .select([[i32::MIN as f32, -1.0], [0.0, 0.0], [0.0, 0.0]], 1.0)
                .unwrap()
                .indices,
            [1, 0]
        );
    }

    #[test]
    fn output_never_replaces_input_existing_files_or_invalid_selections() {
        let directory = TestDirectory::new();
        let input = directory.write("source.pcd", &header(1), &xyz_bytes(&[[1.0, 2.0, 3.0]]));
        let cloud = PointCloud::read(&input).unwrap();
        let original = fs::read(&input).unwrap();
        assert!(cloud.write_selected(&input, &[]).is_err());
        let existing = directory.write("existing.pcd", "keep this file", &[]);
        assert!(cloud.write_selected(&existing, &[]).is_err());
        assert_eq!(fs::read(&existing).unwrap(), b"keep this file");
        let output = directory.0.join("invalid.pcd");
        assert!(cloud.write_selected(&output, &[1]).is_err());
        assert!(!output.exists());
        #[cfg(unix)]
        {
            use std::os::unix::fs::symlink;
            let hardlink = directory.0.join("hardlink.pcd");
            fs::hard_link(&input, &hardlink).unwrap();
            assert!(cloud.write_selected(&hardlink, &[]).is_err());
            let link = directory.0.join("symlink.pcd");
            symlink(&input, &link).unwrap();
            assert!(cloud.write_selected(&link, &[]).is_err());
            let dangling = directory.0.join("dangling.pcd");
            symlink(directory.0.join("absent"), &dangling).unwrap();
            assert!(cloud.write_selected(&dangling, &[]).is_err());
        }
        assert_eq!(fs::read(&input).unwrap(), original);
        assert!(!fs::read_dir(&directory.0).unwrap().any(|entry| entry
            .unwrap()
            .file_name()
            .to_string_lossy()
            .starts_with(".taffy-pcd-")));
    }
}
