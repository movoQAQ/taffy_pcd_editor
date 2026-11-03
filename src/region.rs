//! Convex selection volumes matching the original editor's XYZ expansion.
//!
//! Each picked point is expanded to the eight corners of an axis-aligned cube,
//! then a 3D convex hull is built. This is not a spherical offset of its faces.

use std::collections::BTreeMap;

const INSIDE_TOLERANCE: f64 = 1.0e-6;

#[derive(Clone, Debug)]
pub struct Region {
    pub vertices: Vec<[f32; 3]>,
    pub triangles: Vec<[usize; 3]>,
    pub bounds: [[f32; 2]; 3],
    precise_bounds: [[f64; 2]; 3],
    origin: [f64; 3],
    /// Unit-normal plane equations in global coordinates, n.x + d <= 1e-6.
    pub planes: Vec<[f64; 4]>,
    halfspaces: Vec<Plane>,
}

#[derive(Clone, Copy, Debug)]
struct Plane {
    normal: [f64; 3],
    point: [f64; 3],
}

impl Plane {
    fn distance(&self, point: [f64; 3]) -> f64 {
        dot(self.normal, sub(point, self.point))
    }
}

#[derive(Clone, Copy, Debug)]
struct Face {
    indices: [usize; 3],
    plane: Plane,
}

impl Region {
    pub fn from_picks(picks: &[[f32; 3]], expand_m: f32) -> Result<Self, String> {
        if !expand_m.is_finite() || expand_m < 0.0 {
            return Err("区域外扩距离必须是有限的非负数。".into());
        }
        if picks.iter().flatten().any(|value| !value.is_finite()) {
            return Err("边界点包含无效坐标。".into());
        }
        // Treat signed zero as one coordinate, as NumPy unique does.
        let mut unique: Vec<_> = picks
            .iter()
            .map(|point| point.map(|value| if value == 0.0 { 0.0 } else { value }))
            .collect();
        unique.sort_unstable_by(|a, b| {
            a[0].total_cmp(&b[0])
                .then(a[1].total_cmp(&b[1]))
                .then(a[2].total_cmp(&b[2]))
        });
        unique.dedup();
        if unique.len() < 4 {
            return Err("至少选择 4 个不同的点。".into());
        }
        let mut expanded = Vec::new();
        expanded
            .try_reserve_exact(unique.len().checked_mul(8).ok_or("边界点过多。")?)
            .map_err(|error| format!("无法分配区域顶点：{error}"))?;
        let expansion = f64::from(expand_m);
        for point in unique {
            for x in [-expansion, expansion] {
                for y in [-expansion, expansion] {
                    for z in [-expansion, expansion] {
                        let vertex = [
                            f64::from(point[0]) + x,
                            f64::from(point[1]) + y,
                            f64::from(point[2]) + z,
                        ];
                        if vertex.iter().any(|value| value.abs() > f64::from(f32::MAX)) {
                            return Err("外扩区域超出可显示的坐标范围。".into());
                        }
                        expanded.push(vertex);
                    }
                }
            }
        }
        expanded.sort_unstable_by(|a, b| {
            a[0].total_cmp(&b[0])
                .then(a[1].total_cmp(&b[1]))
                .then(a[2].total_cmp(&b[2]))
        });
        expanded.dedup();
        let mut precise_bounds = expanded[0].map(|value| [value, value]);
        for point in &expanded {
            for axis in 0..3 {
                precise_bounds[axis][0] = precise_bounds[axis][0].min(point[axis]);
                precise_bounds[axis][1] = precise_bounds[axis][1].max(point[axis]);
            }
        }
        // Local coordinates avoid loss of precision when maps have a large offset.
        let origin = precise_bounds.map(|[low, high]| low + (high - low) * 0.5);
        let scale = precise_bounds
            .iter()
            .map(|range| range[1] - range[0])
            .fold(0.0_f64, f64::max);
        let tolerance = scale * f64::EPSILON * 256.0;
        let points: Vec<_> = expanded.iter().map(|&point| sub(point, origin)).collect();
        let faces = convex_hull(&points, tolerance)?;

        // Compact to actual hull vertices, keeping the triangle indices stable.
        let mut used = vec![false; points.len()];
        for face in &faces {
            for &index in &face.indices {
                used[index] = true;
            }
        }
        let mut remap = vec![0; points.len()];
        let mut vertices = Vec::new();
        for (index, point) in expanded.iter().enumerate() {
            if used[index] {
                remap[index] = vertices.len();
                vertices.push(point.map(|value| value as f32));
            }
        }
        let triangles = faces
            .iter()
            .map(|face| face.indices.map(|index| remap[index]))
            .collect();
        Ok(Self {
            vertices,
            triangles,
            bounds: precise_bounds.map(|range| range.map(|value| value as f32)),
            precise_bounds,
            origin,
            planes: faces
                .iter()
                .map(|face| {
                    let normal = face.plane.normal;
                    let global = std::array::from_fn(|axis| face.plane.point[axis] + origin[axis]);
                    [normal[0], normal[1], normal[2], -dot(normal, global)]
                })
                .collect(),
            halfspaces: faces.into_iter().map(|face| face.plane).collect(),
        })
    }

    /// Inclusive XYZ limits and hull boundaries, matching points_inside_region.
    pub fn contains(&self, point: [f32; 3], ranges: [[f32; 2]; 3]) -> bool {
        if !(0..3).all(|axis| {
            point[axis].is_finite()
                && point[axis] >= ranges[axis][0]
                && point[axis] <= ranges[axis][1]
                && f64::from(point[axis]) >= self.precise_bounds[axis][0]
                && f64::from(point[axis]) <= self.precise_bounds[axis][1]
        }) {
            return false;
        }
        let local = sub(point.map(f64::from), self.origin);
        self.halfspaces
            .iter()
            .all(|plane| plane.distance(local) <= INSIDE_TOLERANCE)
    }
}

fn convex_hull(points: &[[f64; 3]], tolerance: f64) -> Result<Vec<Face>, String> {
    let degenerate = || {
        "所选点无法形成有效三维凸包，请选择至少 4 个不共面的点，或增加 XYZ 外扩距离。".to_owned()
    };
    let a = 0;
    let b = (1..points.len())
        .max_by(|&i, &j| {
            norm(sub(points[i], points[a])).total_cmp(&norm(sub(points[j], points[a])))
        })
        .ok_or_else(degenerate)?;
    let ab = sub(points[b], points[a]);
    let line_length = norm(ab);
    if line_length <= tolerance {
        return Err(degenerate());
    }
    let c = (0..points.len())
        .max_by(|&i, &j| {
            norm(cross(ab, sub(points[i], points[a])))
                .total_cmp(&norm(cross(ab, sub(points[j], points[a]))))
        })
        .ok_or_else(degenerate)?;
    let normal = cross(ab, sub(points[c], points[a]));
    let area = norm(normal);
    if area / line_length <= tolerance {
        return Err(degenerate());
    }
    let unit = normal.map(|value| value / area);
    let d = (0..points.len())
        .max_by(|&i, &j| {
            dot(unit, sub(points[i], points[a]))
                .abs()
                .total_cmp(&dot(unit, sub(points[j], points[a])).abs())
        })
        .ok_or_else(degenerate)?;
    if dot(unit, sub(points[d], points[a])).abs() <= tolerance {
        return Err(degenerate());
    }
    let interior = std::array::from_fn(|axis| {
        (points[a][axis] + points[b][axis] + points[c][axis] + points[d][axis]) * 0.25
    });
    let mut faces = [[a, b, c], [a, b, d], [a, c, d], [b, c, d]]
        .into_iter()
        .map(|indices| make_face(points, indices, interior).ok_or_else(degenerate))
        .collect::<Result<Vec<_>, _>>()?;
    for (index, &point) in points.iter().enumerate() {
        if [a, b, c, d].contains(&index) {
            continue;
        }
        let mut horizon: BTreeMap<(usize, usize), usize> = BTreeMap::new();
        faces.retain(|face| {
            if face.plane.distance(point) <= tolerance {
                return true;
            }
            let [a, b, c] = face.indices;
            for (left, right) in [(a, b), (b, c), (c, a)] {
                let edge = (left.min(right), left.max(right));
                *horizon.entry(edge).or_default() += 1;
            }
            false
        });
        for ((left, right), count) in horizon {
            if count == 1 {
                let face =
                    make_face(points, [left, right, index], interior).ok_or_else(degenerate)?;
                faces.push(face);
            }
        }
    }
    Ok(faces)
}

fn make_face(points: &[[f64; 3]], mut indices: [usize; 3], interior: [f64; 3]) -> Option<Face> {
    let a = points[indices[0]];
    let normal = cross(sub(points[indices[1]], a), sub(points[indices[2]], a));
    let length = norm(normal);
    if length == 0.0 || !length.is_finite() {
        return None;
    }
    let mut normal = normal.map(|value| value / length);
    if dot(normal, sub(interior, a)) > 0.0 {
        normal = normal.map(|value| -value);
        indices.swap(1, 2);
    }
    Some(Face {
        indices,
        plane: Plane { normal, point: a },
    })
}

fn sub(a: [f64; 3], b: [f64; 3]) -> [f64; 3] {
    std::array::from_fn(|axis| a[axis] - b[axis])
}

fn dot(a: [f64; 3], b: [f64; 3]) -> f64 {
    a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
}

fn cross(a: [f64; 3], b: [f64; 3]) -> [f64; 3] {
    [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]
}

fn norm(vector: [f64; 3]) -> f64 {
    dot(vector, vector).sqrt()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn tetrahedron() -> [[f32; 3]; 4] {
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
    }

    fn everywhere() -> [[f32; 2]; 3] {
        [[-100.0, 100.0]; 3]
    }

    #[test]
    fn tetrahedron_is_not_its_axis_aligned_bounding_box() {
        let region = Region::from_picks(&tetrahedron(), 0.0).unwrap();
        assert_eq!(region.vertices.len(), 4);
        assert_eq!(region.triangles.len(), 4);
        assert_eq!(region.bounds, [[0.0, 1.0]; 3]);
        for point in tetrahedron() {
            assert!(region.contains(point, everywhere()));
        }
        assert!(region.contains([0.1, 0.2, 0.3], everywhere()));
        assert!(!region.contains([0.5, 0.5, 0.5], everywhere()));
        assert!(!region.contains([-0.0000001, 0.0, 0.0], everywhere()));
        assert!(!region.contains([f32::NAN, 0.0, 0.0], everywhere()));
    }

    #[test]
    fn visible_ranges_clip_the_hull_and_include_boundaries() {
        let region = Region::from_picks(&tetrahedron(), 0.0).unwrap();
        let ranges = [[0.2, 0.4], [0.0, 1.0], [0.0, 1.0]];
        assert!(region.contains([0.2, 0.1, 0.1], ranges));
        assert!(region.contains([0.4, 0.1, 0.1], ranges));
        assert!(!region.contains([0.1, 0.1, 0.1], ranges));
        assert!(!region.contains([0.3, 0.1, 0.1], [[2.0, 3.0]; 3]));
    }

    #[test]
    fn expansion_is_xyz_cube_minkowski_sum_not_normal_offset() {
        let region = Region::from_picks(&tetrahedron(), 0.25).unwrap();
        assert_eq!(region.bounds, [[-0.25, 1.25]; 3]);
        assert!(region.contains([-0.25, -0.25, -0.25], everywhere()));
        assert!(region.contains([1.25, 0.25, 0.25], everywhere()));
        assert!(region.contains([0.5, 0.5, 0.5], everywhere()));
        assert!(!region.contains([0.75, 0.75, 0.75], everywhere()));
    }

    #[test]
    fn duplicate_and_coplanar_picks_follow_original_expansion_order() {
        let mut picks = tetrahedron().to_vec();
        picks.extend(tetrahedron());
        assert_eq!(Region::from_picks(&picks, 0.0).unwrap().vertices.len(), 4);
        assert!(Region::from_picks(&[[0.0; 3]; 5], 1.0).is_err());
        let coplanar = [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [1.0, 1.0, 0.0],
        ];
        assert!(Region::from_picks(&coplanar, 0.0).is_err());
        let expanded = Region::from_picks(&coplanar, 0.25).unwrap();
        assert!(expanded.contains([0.5, 0.5, 0.25], everywhere()));
        assert!(!expanded.contains([0.5, 0.5, 0.26], everywhere()));
        let collinear = [[0.0; 3], [1.0; 3], [2.0; 3], [3.0; 3]];
        assert!(Region::from_picks(&collinear, 0.0).is_err());
        assert!(Region::from_picks(&collinear, 0.25).is_ok());
    }

    #[test]
    fn signed_zero_duplicates_do_not_count_as_distinct_picks() {
        let picks = [
            [-0.0, 0.0, 0.0],
            [-0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ];
        assert!(Region::from_picks(&picks, 0.25).is_err());
    }

    #[test]
    fn near_flat_tetrahedron_remains_valid() {
        let mut picks = tetrahedron();
        picks[3][2] = 1e-8;
        let region = Region::from_picks(&picks, 0.0).unwrap();
        assert!(region.contains([0.1, 0.1, 1e-9], everywhere()));
        assert!(!region.contains([0.1, 0.1, 2e-8], everywhere()));
    }

    #[test]
    fn many_coplanar_surface_points_form_a_closed_cube_mesh() {
        let mut picks = Vec::new();
        for x in 0..5 {
            for y in 0..5 {
                for z in 0..5 {
                    if [x, y, z]
                        .iter()
                        .any(|&coordinate| coordinate == 0 || coordinate == 4)
                    {
                        picks.push([x as f32 / 4.0, y as f32 / 4.0, z as f32 / 4.0]);
                    }
                }
            }
        }
        for expansion in [0.0, 0.25] {
            let region = Region::from_picks(&picks, expansion).unwrap();
            assert!(region.contains([0.5; 3], everywhere()));
            for &point in &picks {
                assert!(region.contains(point, everywhere()));
            }
            let mut edge_counts = BTreeMap::new();
            for &[a, b, c] in &region.triangles {
                for (left, right) in [(a, b), (b, c), (c, a)] {
                    *edge_counts
                        .entry((left.min(right), left.max(right)))
                        .or_insert(0) += 1;
                }
            }
            assert!(edge_counts.values().all(|&count| count == 2));
            assert_eq!(
                region.vertices.len() + region.triangles.len(),
                edge_counts.len() + 2
            );
        }
    }

    #[test]
    fn invalid_expansion_and_coordinates_are_rejected() {
        for expansion in [-0.1, f32::NAN, f32::INFINITY] {
            assert!(Region::from_picks(&tetrahedron(), expansion).is_err());
        }
        let mut picks = tetrahedron();
        picks[0][0] = f32::INFINITY;
        assert!(Region::from_picks(&picks, 0.0).is_err());
    }

    #[test]
    fn translated_hull_and_interior_picks_keep_volume_unchanged() {
        let mut picks = tetrahedron().to_vec();
        picks.push([0.25; 3]);
        for point in &mut picks {
            for value in point {
                *value += 1_000_000.0;
            }
        }
        let region = Region::from_picks(&picks, 0.0).unwrap();
        let ranges = [[999_999.0, 1_000_002.0]; 3];
        assert_eq!(region.vertices.len(), 4);
        assert!(region.contains([1_000_000.25; 3], ranges));
        assert!(!region.contains([1_000_000.5; 3], ranges));
    }
}
