//! Scene ownership and field-preserving edits, independent of the GUI renderer.

use std::collections::HashSet;
use std::path::{Path, PathBuf};
use std::sync::Arc;

use taffy_pcd_core::PointCloud;

use crate::region::Region;

#[derive(Clone, Debug)]
pub struct Layer {
    /// Assigned by `Scene::insert`; zero means this layer has not been inserted.
    pub id: u64,
    pub name: String,
    pub source: PathBuf,
    pub cloud: Arc<PointCloud>,
    /// Original record indices in display order. `None` means the entire input.
    pub indices: Option<Arc<Vec<usize>>>,
    pub points: Arc<Vec<[f32; 3]>>,
    pub bounds: Option<[[f32; 2]; 3]>,
    pub visible: bool,
}

impl Layer {
    pub fn load(path: PathBuf) -> Result<Self, String> {
        let cloud = Arc::new(PointCloud::read(&path).map_err(|error| error.to_string())?);
        let points = collect_points(&cloud, 0..cloud.len(), cloud.len())?;
        let name = path
            .file_name()
            .unwrap_or(path.as_os_str())
            .to_string_lossy()
            .into_owned();
        Ok(Self {
            id: 0,
            name,
            source: path,
            bounds: cloud.bounds(),
            cloud,
            indices: None,
            points: Arc::new(points),
            visible: true,
        })
    }

    /// Retains points outside the box and the first point per voxel inside it.
    /// Repeated filtering operates on this layer's remaining points only.
    pub fn filtered(&self, ranges: [[f32; 2]; 3], voxel: f32) -> Result<Self, String> {
        validate_filter(ranges, voxel)?;
        let indices = match &self.indices {
            None => {
                self.cloud
                    .select(ranges, voxel)
                    .map_err(|error| error.to_string())?
                    .indices
            }
            Some(current) => {
                let inside = |point: [f32; 3]| {
                    (0..3).all(|axis| {
                        point[axis] >= ranges[axis][0] && point[axis] <= ranges[axis][1]
                    })
                };
                let mut selected = Vec::new();
                selected
                    .try_reserve_exact(current.len())
                    .map_err(|error| format!("cannot allocate selection: {error}"))?;
                for &index in current.iter() {
                    if !inside(self.cloud.xyz(index)) {
                        selected.push(index);
                    }
                }
                let mut occupied = HashSet::new();
                occupied
                    .try_reserve(current.len() - selected.len())
                    .map_err(|error| format!("cannot allocate voxel table: {error}"))?;
                for &index in current.iter() {
                    let point = self.cloud.xyz(index);
                    if !inside(point) {
                        continue;
                    }
                    let mut cell = [0_i32; 3];
                    for axis in 0..3 {
                        let coordinate = (point[axis] / voxel).floor();
                        if !coordinate.is_finite()
                            || (coordinate as f64) < i32::MIN as f64
                            || (coordinate as f64) > i32::MAX as f64
                        {
                            return Err(format!(
                                "point {index} voxel coordinate is outside int32 range"
                            ));
                        }
                        cell[axis] = coordinate as i32;
                    }
                    if occupied.insert(cell) {
                        selected.push(index);
                    }
                }
                selected
            }
        };
        let points = collect_points(&self.cloud, indices.iter().copied(), indices.len())?;
        let bounds = point_bounds(&points);
        Ok(Self {
            id: 0,
            name: format!("{} (filtered)", self.name),
            source: self.source.clone(),
            cloud: Arc::clone(&self.cloud),
            indices: Some(Arc::new(indices)),
            points: Arc::new(points),
            bounds,
            visible: true,
        })
    }

    /// Deletes only surviving points in the convex region and current XYZ range.
    /// Original records remain shared, so all fields and survivor order are kept.
    pub fn delete_region(
        &self,
        region: &Region,
        ranges: [[f32; 2]; 3],
    ) -> Result<(Self, usize), String> {
        validate_ranges(ranges)?;
        let mut indices = Vec::new();
        indices
            .try_reserve_exact(self.points.len())
            .map_err(|error| format!("cannot allocate deletion selection: {error}"))?;
        for (position, &point) in self.points.iter().enumerate() {
            if !region.contains(point, ranges) {
                indices.push(
                    self.indices
                        .as_ref()
                        .map_or(position, |current| current[position]),
                );
            }
        }
        let removed = self.points.len() - indices.len();
        if removed == 0 {
            let mut unchanged = self.clone();
            unchanged.id = 0;
            return Ok((unchanged, 0));
        }
        if indices.is_empty() {
            return Err("该区域包含图层全部点，至少保留一个点。".into());
        }
        let points = collect_points(&self.cloud, indices.iter().copied(), indices.len())?;
        let bounds = point_bounds(&points);
        Ok((
            Self {
                id: 0,
                name: format!("{} (region deleted)", self.name),
                source: self.source.clone(),
                cloud: Arc::clone(&self.cloud),
                indices: Some(Arc::new(indices)),
                points: Arc::new(points),
                bounds,
                visible: true,
            },
            removed,
        ))
    }

    /// Writes a new PCD with complete original records, including normal fields.
    /// The core refuses to replace either an existing output or the source file.
    pub fn export(&self, path: &Path) -> Result<(), String> {
        match &self.indices {
            Some(indices) => self.cloud.write_selected(path, indices),
            None => {
                let mut indices = Vec::new();
                indices
                    .try_reserve_exact(self.cloud.len())
                    .map_err(|error| format!("cannot allocate export selection: {error}"))?;
                indices.extend(0..self.cloud.len());
                self.cloud.write_selected(path, &indices)
            }
        }
        .map_err(|error| error.to_string())
    }
}

#[derive(Debug, Default)]
pub struct Scene {
    pub layers: Vec<Layer>,
    pub selected: Option<u64>,
    last_id: u64,
}

impl Scene {
    pub fn insert(&mut self, mut layer: Layer) -> u64 {
        self.last_id = self.last_id.checked_add(1).expect("layer ID exhausted");
        layer.id = self.last_id;
        self.selected = Some(layer.id);
        self.layers.push(layer);
        self.last_id
    }

    /// Applies a background result only while its original source still exists.
    /// Missing-source results, including errors, are discarded without changing
    /// selection or visibility. Reimporting the same file has a different ID.
    pub fn complete_filter(
        &mut self,
        source_id: u64,
        result: Result<Layer, String>,
    ) -> Result<Option<u64>, String> {
        let Some(source) = self.layers.iter_mut().find(|layer| layer.id == source_id) else {
            return Ok(None);
        };
        let filtered = result?;
        source.visible = false;
        Ok(Some(self.insert(filtered)))
    }

    /// Removes scene data only. Source files are never touched.
    pub fn remove(&mut self, id: u64) -> bool {
        let Some(index) = self.layers.iter().position(|layer| layer.id == id) else {
            return false;
        };
        self.layers.remove(index);
        if self.selected == Some(id) {
            self.selected = self
                .layers
                .get(index.min(self.layers.len().saturating_sub(1)))
                .map(|layer| layer.id);
        }
        true
    }

    pub fn selected_layer(&self) -> Option<&Layer> {
        let selected = self.selected?;
        self.layers.iter().find(|layer| layer.id == selected)
    }

    pub fn bounds_visible(&self) -> Option<[[f32; 2]; 3]> {
        let mut result: Option<[[f32; 2]; 3]> = None;
        for layer in self.layers.iter().filter(|layer| layer.visible) {
            let Some(bounds) = layer.bounds else {
                continue;
            };
            match result.as_mut() {
                None => result = Some(bounds),
                Some(combined) => {
                    for axis in 0..3 {
                        combined[axis][0] = combined[axis][0].min(bounds[axis][0]);
                        combined[axis][1] = combined[axis][1].max(bounds[axis][1]);
                    }
                }
            }
        }
        result
    }
}

fn validate_filter(ranges: [[f32; 2]; 3], voxel: f32) -> Result<(), String> {
    if !voxel.is_finite() || voxel <= 0.0 {
        return Err("voxel size must be finite and positive".to_owned());
    }
    validate_ranges(ranges)
}

fn validate_ranges(ranges: [[f32; 2]; 3]) -> Result<(), String> {
    if ranges
        .iter()
        .any(|range| !range[0].is_finite() || !range[1].is_finite() || range[0] > range[1])
    {
        return Err("each range must have finite bounds with minimum <= maximum".to_owned());
    }
    Ok(())
}

fn collect_points(
    cloud: &PointCloud,
    indices: impl Iterator<Item = usize>,
    count: usize,
) -> Result<Vec<[f32; 3]>, String> {
    let mut points = Vec::new();
    points
        .try_reserve_exact(count)
        .map_err(|error| format!("cannot allocate display coordinates: {error}"))?;
    points.extend(indices.map(|index| cloud.xyz(index)));
    Ok(points)
}

fn point_bounds(points: &[[f32; 3]]) -> Option<[[f32; 2]; 3]> {
    let mut bounds = points.first()?.map(|value| [value, value]);
    for point in points.iter().skip(1) {
        for axis in 0..3 {
            bounds[axis][0] = bounds[axis][0].min(point[axis]);
            bounds[axis][1] = bounds[axis][1].max(point[axis]);
        }
    }
    Some(bounds)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use std::sync::atomic::{AtomicU64, Ordering};

    static TEST_COUNTER: AtomicU64 = AtomicU64::new(0);

    struct Fixture {
        directory: PathBuf,
        source: PathBuf,
        original: Vec<u8>,
        records: Vec<[u8; 24]>,
    }

    impl Fixture {
        fn new(coordinates: &[[f32; 3]]) -> Self {
            let directory = std::env::temp_dir().join(format!(
                "taffy-scene-test-{}-{}",
                std::process::id(),
                TEST_COUNTER.fetch_add(1, Ordering::Relaxed)
            ));
            fs::create_dir(&directory).unwrap();
            let source = directory.join("normals.pcd");
            let mut original = format!(
                "VERSION .7\nFIELDS x y z normal_x normal_y normal_z\nSIZE 4 4 4 4 4 4\nTYPE F F F F F F\nCOUNT 1 1 1 1 1 1\nWIDTH {}\nHEIGHT 1\nVIEWPOINT 0 0 0 1 0 0 0\nPOINTS {}\nDATA binary\n",
                coordinates.len(), coordinates.len()
            ).into_bytes();
            let records = coordinates
                .iter()
                .enumerate()
                .map(|(index, xyz)| {
                    let normal = [index as f32 + 0.25, -0.5, 1.0];
                    let mut record = [0_u8; 24];
                    for (field, value) in xyz.iter().chain(normal.iter()).enumerate() {
                        record[field * 4..field * 4 + 4].copy_from_slice(&value.to_le_bytes());
                    }
                    original.extend_from_slice(&record);
                    record
                })
                .collect();
            fs::write(&source, &original).unwrap();
            Self {
                directory,
                source,
                original,
                records,
            }
        }

        fn standard() -> Self {
            Self::new(&[
                [0.1, 0.0, 0.0],
                [0.2, 0.0, 0.0],
                [1.1, 0.0, 0.0],
                [1.2, 0.0, 0.0],
                [3.0, 0.0, 0.0],
            ])
        }

        fn load(&self) -> Layer {
            Layer::load(self.source.clone()).unwrap()
        }

        fn assert_source_unchanged(&self) {
            assert_eq!(fs::read(&self.source).unwrap(), self.original);
        }

        fn assert_export_records(&self, output: &Path, indices: &[usize]) {
            let bytes = fs::read(output).unwrap();
            let marker = b"DATA binary\n";
            let payload = bytes
                .windows(marker.len())
                .position(|window| window == marker)
                .unwrap()
                + marker.len();
            let expected: Vec<u8> = indices
                .iter()
                .flat_map(|&index| self.records[index])
                .collect();
            assert_eq!(&bytes[payload..], expected);
            let written = PointCloud::read(output).unwrap();
            assert_eq!(written.len(), indices.len());
            assert_eq!(written.fields(), self.load().cloud.fields());
        }
    }

    impl Drop for Fixture {
        fn drop(&mut self) {
            let _ = fs::remove_dir_all(&self.directory);
        }
    }

    #[test]
    fn deleting_selected_middle_or_last_layer_selects_neighbor() {
        let fixture = Fixture::standard();
        let mut scene = Scene::default();
        let first = scene.insert(fixture.load());
        let middle = scene.insert(fixture.load());
        let last = scene.insert(fixture.load());
        scene.selected = Some(middle);
        assert!(scene.remove(middle));
        assert_eq!(scene.selected_layer().unwrap().id, last);
        assert!(scene.remove(last));
        assert_eq!(scene.selected_layer().unwrap().id, first);
        assert!(scene.remove(first));
        assert!(scene.selected_layer().is_none());
        assert!(scene.layers.is_empty());
        assert!(scene.bounds_visible().is_none());
        fixture.assert_source_unchanged();
    }

    #[test]
    fn deleting_other_or_missing_layer_preserves_selection_and_ids_never_repeat() {
        let fixture = Fixture::standard();
        let mut scene = Scene::default();
        let first = scene.insert(fixture.load());
        let selected = scene.insert(fixture.load());
        assert!(scene.remove(first));
        assert_eq!(scene.selected, Some(selected));
        assert!(!scene.remove(first));
        assert!(!scene.remove(u64::MAX));
        assert_eq!(scene.selected, Some(selected));
        scene.remove(selected);
        assert_eq!(scene.selected, None);
        let reimported = scene.insert(fixture.load());
        assert!(reimported > selected);
        assert_eq!(scene.selected, Some(reimported));
        assert!(!scene.remove(first));
        fixture.assert_source_unchanged();
    }

    #[test]
    fn deleting_last_owner_releases_cloud_and_display_points() {
        let fixture = Fixture::standard();
        let layer = fixture.load();
        let cloud = Arc::downgrade(&layer.cloud);
        let points = Arc::downgrade(&layer.points);
        let mut scene = Scene::default();
        let id = scene.insert(layer);
        assert!(cloud.upgrade().is_some());
        scene.remove(id);
        assert!(cloud.upgrade().is_none());
        assert!(points.upgrade().is_none());
        fixture.assert_source_unchanged();
    }

    #[test]
    fn filtered_layer_keeps_shared_records_after_original_layer_is_deleted() {
        let fixture = Fixture::standard();
        let layer = fixture.load();
        let cloud = Arc::downgrade(&layer.cloud);
        let filtered = layer.filtered([[0.0, 2.0]; 3], 1.0).unwrap();
        assert!(Arc::ptr_eq(&layer.cloud, &filtered.cloud));
        let mut scene = Scene::default();
        let original = scene.insert(layer);
        let filtered_id = scene.insert(filtered);
        scene.remove(original);
        let path = fixture.directory.join("filtered.pcd");
        scene.selected_layer().unwrap().export(&path).unwrap();
        fixture.assert_export_records(&path, &[4, 0, 2]);
        assert!(cloud.upgrade().is_some());
        scene.remove(filtered_id);
        assert!(cloud.upgrade().is_none());
        fixture.assert_source_unchanged();
    }

    #[test]
    fn repeated_filter_does_not_restore_removed_points_and_preserves_normals() {
        let fixture = Fixture::standard();
        let layer = fixture.load();
        let filtered = layer.filtered([[0.0, 2.0]; 3], 1.0).unwrap();
        assert_eq!(filtered.indices.as_deref().unwrap(), &vec![4, 0, 2]);
        let again = filtered.filtered([[0.0, 1.0]; 3], 0.01).unwrap();
        assert_eq!(again.indices.as_deref().unwrap(), &vec![4, 2, 0]);
        assert_eq!(again.points.len(), 3);
        assert_eq!(again.points[1], [1.1, 0.0, 0.0]);
        let output = fixture.directory.join("again.pcd");
        again.export(&output).unwrap();
        fixture.assert_export_records(&output, &[4, 2, 0]);
        fixture.assert_source_unchanged();
    }

    #[test]
    fn export_full_layer_preserves_records_and_refuses_existing_paths() {
        let fixture = Fixture::standard();
        let layer = fixture.load();
        let output = fixture.directory.join("complete.pcd");
        layer.export(&output).unwrap();
        fixture.assert_export_records(&output, &[0, 1, 2, 3, 4]);
        let exported = fs::read(&output).unwrap();
        assert!(layer.export(&output).is_err());
        assert!(layer.export(&fixture.source).is_err());
        assert_eq!(fs::read(&output).unwrap(), exported);
        fixture.assert_source_unchanged();
    }

    #[test]
    fn empty_layers_can_be_filtered_exported_and_deleted() {
        let fixture = Fixture::new(&[]);
        let layer = fixture.load();
        assert!(layer.points.is_empty());
        assert_eq!(layer.bounds, None);
        let filtered = layer.filtered([[0.0, 1.0]; 3], 0.1).unwrap();
        assert!(filtered.points.is_empty());
        assert_eq!(filtered.bounds, None);
        let output = fixture.directory.join("empty.pcd");
        filtered.export(&output).unwrap();
        fixture.assert_export_records(&output, &[]);
        let mut scene = Scene::default();
        let id = scene.insert(filtered);
        assert_eq!(scene.bounds_visible(), None);
        assert!(scene.remove(id));
        fixture.assert_source_unchanged();
    }

    #[test]
    fn invalid_filter_parameters_are_rejected_for_original_and_subset() {
        let fixture = Fixture::standard();
        let original = fixture.load();
        let subset = original.filtered([[0.0, 2.0]; 3], 1.0).unwrap();
        for layer in [&original, &subset] {
            for voxel in [0.0, -1.0, f32::NAN, f32::INFINITY] {
                assert!(layer.filtered([[0.0, 4.0]; 3], voxel).is_err());
            }
            for range in [[1.0, 0.0], [f32::NAN, 1.0], [0.0, f32::INFINITY]] {
                assert!(layer.filtered([range; 3], 1.0).is_err());
            }
            assert!(layer.filtered([[0.0, 4.0]; 3], f32::MIN_POSITIVE).is_err());
        }
    }

    #[test]
    fn stale_filter_result_does_not_replace_reimported_layer_and_releases_resources() {
        let fixture = Fixture::standard();
        let original = fixture.load();
        let filtered = original.filtered([[0.0, 2.0]; 3], 1.0).unwrap();
        let old_cloud = Arc::downgrade(&filtered.cloud);
        let result_points = Arc::downgrade(&filtered.points);
        let result_indices = Arc::downgrade(filtered.indices.as_ref().unwrap());
        let mut scene = Scene::default();
        let source_id = scene.insert(original);
        scene.remove(source_id);
        let reimported_id = scene.insert(fixture.load());
        assert_ne!(reimported_id, source_id);
        assert!(old_cloud.upgrade().is_some());

        assert_eq!(
            scene.complete_filter(source_id, Ok(filtered)).unwrap(),
            None
        );

        assert_eq!(scene.layers.len(), 1);
        assert_eq!(scene.selected, Some(reimported_id));
        let reimported = scene.selected_layer().unwrap();
        assert_eq!(reimported.id, reimported_id);
        assert_eq!(reimported.points.len(), 5);
        assert!(reimported.visible);
        assert!(old_cloud.upgrade().is_none());
        assert!(result_points.upgrade().is_none());
        assert!(result_indices.upgrade().is_none());
        fixture.assert_source_unchanged();
    }

    #[test]
    fn completed_filter_hides_source_and_selects_new_result_only() {
        let fixture = Fixture::standard();
        let original = fixture.load();
        let filtered = original.filtered([[0.0, 2.0]; 3], 1.0).unwrap();
        let mut scene = Scene::default();
        let source_id = scene.insert(original);
        let other_id = scene.insert(fixture.load());

        let result_id = scene
            .complete_filter(source_id, Ok(filtered))
            .unwrap()
            .unwrap();

        assert_eq!(scene.layers.len(), 3);
        assert_eq!(scene.selected, Some(result_id));
        assert!(!scene.layers[0].visible);
        assert_eq!(scene.layers[1].id, other_id);
        assert!(scene.layers[1].visible);
        let result = scene.selected_layer().unwrap();
        assert!(result.visible);
        assert_eq!(result.points.len(), 3);
        assert!(result_id > other_id);
        fixture.assert_source_unchanged();
    }

    #[test]
    fn failed_filter_preserves_live_scene_and_stale_error_is_ignored() {
        let fixture = Fixture::standard();
        let mut scene = Scene::default();
        let source_id = scene.insert(fixture.load());
        let selected_id = scene.insert(fixture.load());

        assert_eq!(
            scene.complete_filter(source_id, Err("filter failed".into())),
            Err("filter failed".into())
        );

        assert_eq!(scene.layers.len(), 2);
        assert_eq!(scene.selected, Some(selected_id));
        assert!(scene.layers.iter().all(|layer| layer.visible));
        scene.remove(source_id);
        assert_eq!(
            scene
                .complete_filter(source_id, Err("late filter error".into()))
                .unwrap(),
            None
        );
        assert_eq!(scene.layers.len(), 1);
        assert_eq!(scene.selected, Some(selected_id));
        assert!(scene.layers[0].visible);
        fixture.assert_source_unchanged();
    }

    fn box_region(low: [f32; 3], high: [f32; 3]) -> Region {
        let mut corners = Vec::new();
        for x in [low[0], high[0]] {
            for y in [low[1], high[1]] {
                for z in [low[2], high[2]] {
                    corners.push([x, y, z]);
                }
            }
        }
        Region::from_picks(&corners, 0.0).unwrap()
    }

    #[test]
    fn region_deletion_uses_hull_and_xyz_ranges_and_preserves_complete_records() {
        let fixture = Fixture::new(&[
            [0.0, 0.0, 0.0],
            [0.1, 0.1, 0.1],
            [0.2, 0.2, 0.2],
            [1.0, 1.0, 1.0],
            [0.5, 0.5, 0.5],
        ]);
        let original = fixture.load();
        let region = Region::from_picks(
            &[
                [0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
            ],
            0.0,
        )
        .unwrap();
        let (edited, removed) = original
            .delete_region(&region, [[0.15, 1.0], [0.0, 1.0], [0.0, 1.0]])
            .unwrap();
        assert_eq!(removed, 1);
        assert_eq!(edited.id, 0);
        assert!(Arc::ptr_eq(&original.cloud, &edited.cloud));
        assert_eq!(edited.indices.as_deref().unwrap(), &vec![0, 1, 3, 4]);
        assert_eq!(
            edited.points.as_ref(),
            &vec![[0.0; 3], [0.1; 3], [1.0; 3], [0.5; 3]]
        );
        assert_eq!(edited.bounds, Some([[0.0, 1.0]; 3]));
        assert_eq!(original.points.len(), 5);
        let output = fixture.directory.join("region-deleted.pcd");
        edited.export(&output).unwrap();
        fixture.assert_export_records(&output, &[0, 1, 3, 4]);
        fixture.assert_source_unchanged();
    }

    #[test]
    fn deleting_from_filtered_subset_and_filtering_again_never_restores_records() {
        let fixture = Fixture::standard();
        let original = fixture.load();
        let filtered = original.filtered([[0.0, 2.0]; 3], 1.0).unwrap();
        assert_eq!(filtered.indices.as_deref().unwrap(), &vec![4, 0, 2]);
        let region = box_region([-0.1, -1.0, -1.0], [0.5, 1.0, 1.0]);
        let (deleted, removed) = filtered.delete_region(&region, [[-4.0, 4.0]; 3]).unwrap();
        assert_eq!(removed, 1);
        assert_eq!(deleted.indices.as_deref().unwrap(), &vec![4, 2]);
        let (again, removed) = deleted.delete_region(&region, [[-4.0, 4.0]; 3]).unwrap();
        assert_eq!(removed, 0);
        assert!(Arc::ptr_eq(&deleted.points, &again.points));
        let refiltered = again.filtered([[0.0, 4.0]; 3], 0.01).unwrap();
        assert_eq!(refiltered.indices.as_deref().unwrap(), &vec![4, 2]);
        let output = fixture.directory.join("deleted-filtered.pcd");
        refiltered.export(&output).unwrap();
        fixture.assert_export_records(&output, &[4, 2]);
        fixture.assert_source_unchanged();
    }

    #[test]
    fn no_match_shares_data_and_all_point_deletion_is_rejected_without_changes() {
        let fixture = Fixture::standard();
        let original = fixture.load();
        let absent = box_region([10.0; 3], [11.0; 3]);
        let (unchanged, removed) = original.delete_region(&absent, [[-20.0, 20.0]; 3]).unwrap();
        assert_eq!(removed, 0);
        assert_eq!(unchanged.id, 0);
        assert!(Arc::ptr_eq(&original.cloud, &unchanged.cloud));
        assert!(Arc::ptr_eq(&original.points, &unchanged.points));
        assert!(unchanged.indices.is_none());
        let all = box_region([-1.0; 3], [4.0; 3]);
        let error = original
            .delete_region(&all, [[-20.0, 20.0]; 3])
            .unwrap_err();
        assert!(error.contains("至少保留一个点"));
        assert_eq!(original.points.len(), 5);
        assert!(original.indices.is_none());
        let output = fixture.directory.join("unchanged-after-rejection.pcd");
        original.export(&output).unwrap();
        fixture.assert_export_records(&output, &[0, 1, 2, 3, 4]);
        fixture.assert_source_unchanged();
    }

    #[test]
    fn region_deletion_handles_empty_input_and_rejects_invalid_ranges() {
        let fixture = Fixture::new(&[]);
        let empty = fixture.load();
        let region = box_region([-1.0; 3], [1.0; 3]);
        let (result, removed) = empty.delete_region(&region, [[-2.0, 2.0]; 3]).unwrap();
        assert_eq!(removed, 0);
        assert!(result.points.is_empty());
        assert_eq!(result.bounds, None);
        for range in [[1.0, 0.0], [f32::NAN, 1.0], [0.0, f32::INFINITY]] {
            assert!(empty.delete_region(&region, [range; 3]).is_err());
        }
        fixture.assert_source_unchanged();
    }

    #[test]
    fn visible_bounds_ignore_hidden_and_empty_layers() {
        let first_fixture = Fixture::new(&[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]);
        let second_fixture = Fixture::new(&[[-7.0, 8.0, -9.0]]);
        let empty_fixture = Fixture::new(&[]);
        let mut scene = Scene::default();
        scene.insert(first_fixture.load());
        let second_id = scene.insert(second_fixture.load());
        scene.insert(empty_fixture.load());
        assert_eq!(
            scene.bounds_visible(),
            Some([[-7.0, 4.0], [2.0, 8.0], [-9.0, 6.0]])
        );
        scene.layers[1].visible = false;
        assert_eq!(
            scene.bounds_visible(),
            Some([[1.0, 4.0], [2.0, 5.0], [3.0, 6.0]])
        );
        scene.layers[0].visible = false;
        assert_eq!(scene.bounds_visible(), None);
        scene.remove(second_id);
        assert_eq!(scene.bounds_visible(), None);
    }
}
