//! Standalone round-trip probe compiled by pcd_formats.py, without GUI dependencies.
#![cfg(not(test))]

use std::path::Path;
use taffy_pcd_core::PointCloud;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args_os().collect();
    if args.len() != 3 {
        return Err("usage: pcd_read_probe input.pcd output.pcd".into());
    }
    let cloud = PointCloud::read(Path::new(&args[1]))?;
    let indices: Vec<_> = (0..cloud.len()).collect();
    cloud.write_selected(Path::new(&args[2]), &indices)?;
    println!(
        "{} points, {} bytes/point",
        cloud.len(),
        cloud.record_size()
    );
    Ok(())
}
