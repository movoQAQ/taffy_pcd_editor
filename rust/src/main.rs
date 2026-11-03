use std::env;
use std::ffi::OsString;
use std::path::PathBuf;
use std::process::ExitCode;
use std::time::Instant;
use taffy_pcd_core::PointCloud;

const HELP: &str = "Usage: taffy-pcd-core INPUT.pcd [--voxel METRES] [--bounds XMIN XMAX YMIN YMAX ZMIN ZMAX] [--output OUTPUT.pcd]

Binary PCD prototype: keep points outside the bounds, then keep the first point
in each occupied voxel inside the bounds, preserving source order and fields.
Default voxel: 0.05 m. Default bounds: the full cloud.
The input is read-only. Output must be a new file. ASCII/compressed PCD and GUI
operations are not implemented. Prints one JSON measurement record to stdout.";

struct Args {
    input: PathBuf,
    output: Option<PathBuf>,
    voxel: f32,
    bounds: Option<[[f32; 2]; 3]>,
}

fn number(value: Option<OsString>, name: &str) -> Result<f32, String> {
    let value = value.ok_or_else(|| format!("missing value for {name}"))?;
    let parsed = value
        .to_str()
        .ok_or_else(|| format!("{name} must be a number"))?
        .parse::<f32>()
        .map_err(|_| format!("invalid number for {name}"))?;
    if !parsed.is_finite() {
        return Err(format!("{name} must be finite"));
    }
    Ok(parsed)
}

fn arguments() -> Result<Option<Args>, String> {
    let mut values = env::args_os().skip(1);
    let first = values.next().ok_or_else(|| HELP.to_owned())?;
    if first == "--help" || first == "-h" {
        println!("{HELP}");
        return Ok(None);
    }
    let mut result = Args {
        input: PathBuf::from(first),
        output: None,
        voxel: 0.05,
        bounds: None,
    };
    let mut voxel_set = false;
    while let Some(option) = values.next() {
        match option.to_str() {
            Some("--voxel") if !voxel_set => {
                result.voxel = number(values.next(), "--voxel")?;
                if result.voxel <= 0.0 {
                    return Err("--voxel must be positive".to_owned());
                }
                voxel_set = true;
            }
            Some("--bounds") if result.bounds.is_none() => {
                let mut bounds = [[0.0; 2]; 3];
                for axis in &mut bounds {
                    axis[0] = number(values.next(), "--bounds")?;
                    axis[1] = number(values.next(), "--bounds")?;
                    if axis[0] > axis[1] {
                        return Err("each lower bound must be <= its upper bound".to_owned());
                    }
                }
                result.bounds = Some(bounds);
            }
            Some("--output") if result.output.is_none() => {
                result.output = Some(PathBuf::from(
                    values.next().ok_or("missing value for --output")?,
                ));
            }
            _ => {
                return Err(format!(
                    "unknown or repeated option: {}",
                    option.to_string_lossy()
                ))
            }
        }
    }
    Ok(Some(result))
}

fn run(args: Args) -> Result<(), Box<dyn std::error::Error>> {
    let output_requested = args.output.is_some();
    let started = Instant::now();
    let cloud = PointCloud::read(&args.input)?;
    let source_bounds = cloud.bounds().unwrap_or([[0.0; 2]; 3]);
    let bounds = args.bounds.unwrap_or(source_bounds);
    let loaded = Instant::now();
    let selected = cloud.select(bounds, args.voxel)?;
    let filtered = Instant::now();
    if let Some(path) = args.output {
        cloud.write_selected(&path, &selected.indices)?;
    }
    let written = Instant::now();
    let index_sum = selected
        .indices
        .iter()
        .fold(0_u64, |sum, &index| sum.wrapping_add(index as u64));
    let milliseconds = |duration: std::time::Duration| duration.as_secs_f64() * 1000.0;
    println!(
        "{{\"engine\":\"rust\",\"input_points\":{},\"in_range_points\":{},\"output_points\":{},\"record_bytes\":{},\"load_scan_ms\":{:.6},\"filter_ms\":{:.6},\"write_ms\":{:.6},\"work_ms\":{:.6},\"index_sum\":{},\"bounds\":{:?},\"filter_bounds\":{:?}}}",
        cloud.len(),
        selected.in_range,
        selected.indices.len(),
        cloud.record_size(),
        milliseconds(loaded.duration_since(started)),
        milliseconds(filtered.duration_since(loaded)),
        if output_requested { milliseconds(written.duration_since(filtered)) } else { 0.0 },
        milliseconds(written.duration_since(started)),
        index_sum,
        source_bounds,
        bounds,
    );
    Ok(())
}

fn main() -> ExitCode {
    match arguments() {
        Ok(Some(args)) => match run(args) {
            Ok(()) => ExitCode::SUCCESS,
            Err(error) => {
                eprintln!("taffy-pcd-core: {error}");
                ExitCode::from(2)
            }
        },
        Ok(None) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("{error}");
            ExitCode::from(2)
        }
    }
}
