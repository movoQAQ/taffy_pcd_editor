//! Native OpenGL point rendering. The CPU keeps coordinates once per scene layer;
//! each visible layer gets one packed GPU buffer, with no per-point egui shapes.
use std::collections::HashMap;
use std::sync::{Arc, Mutex};

use eframe::{egui, glow};
use glam::{Mat4, Vec3};
use glow::HasContext;

pub struct RenderLayer {
    pub id: u64,
    pub points: Arc<Vec<[f32; 3]>>,
    pub tint: [f32; 3],
}

/// Scene selection is owned by the editor. The viewport only picks real points
/// and displays the current selection, without mutating source cloud records.
pub struct SelectionOverlay {
    pub layer_id: u64,
    pub polygon: bool,
    pub picking: bool,
    pub picks: Vec<[f32; 3]>,
    pub hull_edges: Vec<[[f32; 3]; 2]>,
    pub ranges: [[f32; 2]; 3],
}

const BACKGROUND: egui::Color32 = egui::Color32::from_rgb(242, 232, 244);
const SELECTION_COLOR: egui::Color32 = egui::Color32::from_rgb(209, 58, 128);

pub struct Viewport {
    renderer: Arc<Mutex<Renderer>>,
    camera: Camera,
    last_bounds: Option<[[f32; 2]; 3]>,
    clicks: ViewportClicks,
}

impl Viewport {
    pub fn new(gl: Arc<glow::Context>) -> Result<Self, String> {
        Ok(Self {
            renderer: Arc::new(Mutex::new(Renderer::new(&gl)?)),
            camera: Camera::default(),
            last_bounds: None,
            clicks: ViewportClicks::default(),
        })
    }

    pub fn fit(&mut self, bounds: [[f32; 2]; 3]) {
        if let Some(camera) = Camera::fitted(bounds) {
            self.camera = camera;
            self.last_bounds = Some(bounds);
        }
    }

    pub fn top(&mut self) {
        self.camera.yaw = -std::f32::consts::FRAC_PI_2;
        self.camera.pitch = std::f32::consts::FRAC_PI_2;
    }

    /// Project a small set of world points using the current camera. This is
    /// also used by GUI verification to locate real, clickable cloud points.
    pub fn project_points(&self, rect: egui::Rect, points: &[[f32; 3]]) -> Vec<Option<egui::Pos2>> {
        let projection = Projection::new(self.camera, rect);
        points
            .iter()
            .map(|point| projection.point(*point).map(|(position, _)| position))
            .collect()
    }

    pub fn show(
        &mut self,
        ui: &mut egui::Ui,
        layers: Vec<RenderLayer>,
        point_size: f32,
        overlay: Option<SelectionOverlay>,
    ) -> Option<[f32; 3]> {
        let size = ui.available_size().max(egui::vec2(1.0, 1.0));
        let (rect, response) = ui.allocate_exact_size(size, egui::Sense::click_and_drag());
        ui.painter().rect_filled(rect, 0.0, BACKGROUND);
        let drawing = overlay.as_ref().is_some_and(|s| s.polygon && s.picking);
        let aspect = rect.width() / rect.height().max(1.0);
        let delta = response.drag_delta();
        if !drawing && response.dragged_by(egui::PointerButton::Primary) {
            self.camera.yaw -= delta.x * 0.007;
            self.camera.pitch = (self.camera.pitch + delta.y * 0.007).clamp(-1.55, 1.55);
            ui.ctx().set_cursor_icon(egui::CursorIcon::Grabbing);
        }
        if !drawing
            && (response.dragged_by(egui::PointerButton::Secondary)
                || response.dragged_by(egui::PointerButton::Middle))
        {
            self.camera.pan(delta.x, delta.y, rect.height(), aspect);
            ui.ctx().set_cursor_icon(egui::CursorIcon::Grabbing);
        }
        if response.hovered() && !drawing {
            let scroll = ui.input_mut(|input| {
                let scroll = input.smooth_scroll_delta.y;
                input.smooth_scroll_delta.y = 0.0;
                scroll
            });
            self.camera.zoom = (self.camera.zoom * (-scroll * 0.002).exp()).clamp(0.0001, 10_000.0);
        }
        let mut picked = None;
        let double_clicked = self.clicks.update(&response);
        if drawing {
            if response.clicked_by(egui::PointerButton::Primary) {
                if let (Some(cursor), Some(selection)) =
                    (response.interact_pointer_pos(), overlay.as_ref())
                {
                    picked = Projection::new(self.camera, rect)
                        .on_z_plane(cursor, selection.ranges[2][0]);
                }
            }
        } else if double_clicked {
            if let Some(selection) = overlay.as_ref().filter(|selection| selection.picking) {
                if let Some(cursor) = response.interact_pointer_pos() {
                    picked = pick_point(
                        &layers,
                        selection.layer_id,
                        self.camera,
                        rect,
                        cursor,
                        point_size,
                        selection.ranges,
                    );
                }
            } else if let Some(bounds) = self.last_bounds {
                self.fit(bounds);
            }
        }
        if response.hovered() && overlay.as_ref().is_some_and(|selection| selection.picking) {
            ui.ctx().set_cursor_icon(egui::CursorIcon::Crosshair);
        }

        let render_selection = overlay
            .as_ref()
            .map(|selection| (selection.layer_id, selection.ranges));
        let renderer = Arc::clone(&self.renderer);
        let camera = self.camera;
        let ctx = ui.ctx().clone();
        ui.painter().add(egui::PaintCallback {
            rect,
            callback: Arc::new(eframe::egui_glow::CallbackFn::new(move |info, painter| {
                if let Ok(mut renderer) = renderer.lock() {
                    if renderer.destroyed {
                        return;
                    }
                    let previous_error = renderer.error.clone();
                    renderer.paint(
                        painter.gl(),
                        info,
                        &layers,
                        camera,
                        point_size,
                        render_selection,
                    );
                    if renderer.error != previous_error {
                        ctx.request_repaint();
                    }
                }
            })),
        });
        if let Some(selection) = &overlay {
            let painter = ui.painter().with_clip_rect(rect);
            let projection = Projection::new(self.camera, rect);
            if selection.polygon && selection.hull_edges.is_empty() {
                for pair in selection.picks.windows(2) {
                    if let (Some((a, _)), Some((b, _))) = (
                        projection.unbounded_point(pair[0]),
                        projection.unbounded_point(pair[1]),
                    ) {
                        painter.line_segment([a, b], egui::Stroke::new(2.0_f32, SELECTION_COLOR));
                    }
                }
                if drawing && response.hovered() {
                    if let (Some(last), Some(cursor)) =
                        (selection.picks.last(), response.hover_pos())
                    {
                        if let Some((a, _)) = projection.unbounded_point(*last) {
                            painter.line_segment(
                                [a, cursor],
                                egui::Stroke::new(1.0_f32, SELECTION_COLOR),
                            );
                        }
                    }
                }
            }
            for [start, end] in &selection.hull_edges {
                // Clip against the editing ranges so the preview follows the
                // same limits as the cloud and subsequent deletion.
                if let Some([start, end]) = clip_segment(*start, *end, selection.ranges) {
                    if let (Some((a, _)), Some((b, _))) = (
                        projection.unbounded_point(start),
                        projection.unbounded_point(end),
                    ) {
                        painter.line_segment([a, b], egui::Stroke::new(1.8_f32, SELECTION_COLOR));
                    }
                }
            }
            let projected = self.project_points(rect, &selection.picks);
            for (index, (point, position)) in selection.picks.iter().zip(projected).enumerate() {
                if let Some(position) = position {
                    let color = if within_ranges(*point, selection.ranges) {
                        SELECTION_COLOR
                    } else {
                        egui::Color32::from_rgb(155, 143, 157)
                    };
                    painter.circle_filled(position, 5.0, color);
                    painter.circle_stroke(
                        position,
                        6.0,
                        egui::Stroke::new(1.5_f32, egui::Color32::WHITE),
                    );
                    let label = position + egui::vec2(9.0, -9.0);
                    painter.text(
                        label + egui::vec2(1.0, 1.0),
                        egui::Align2::LEFT_BOTTOM,
                        (index + 1).to_string(),
                        egui::FontId::proportional(15.0),
                        egui::Color32::WHITE,
                    );
                    painter.text(
                        label,
                        egui::Align2::LEFT_BOTTOM,
                        (index + 1).to_string(),
                        egui::FontId::proportional(15.0),
                        color,
                    );
                }
            }
        }
        if let Ok(renderer) = self.renderer.lock() {
            if let Some(error) = &renderer.error {
                ui.painter().text(
                    rect.left_top() + egui::vec2(14.0, 14.0),
                    egui::Align2::LEFT_TOP,
                    format!("渲染失败：{error}"),
                    egui::FontId::proportional(15.0),
                    egui::Color32::LIGHT_RED,
                );
            }
        }
        picked
    }

    pub fn destroy(&mut self, gl: &glow::Context) {
        if let Ok(mut renderer) = self.renderer.lock() {
            renderer.destroy(gl);
        }
    }
}

/// egui 0.33 counts double/triple clicks globally, even across widgets and
/// distant positions. A toolbar click followed quickly by a viewport double
/// click can therefore arrive as a single click then a triple click. Keep the
/// sequence local to this viewport so real double clicks are never lost, and a
/// click elsewhere or a camera drag cannot become the first half of selection.
#[derive(Default)]
struct ViewportClicks {
    previous: Option<(f64, egui::Pos2)>,
}

impl ViewportClicks {
    fn update(&mut self, response: &egui::Response) -> bool {
        if response.dragged_by(egui::PointerButton::Primary) {
            self.previous = None;
            return false;
        }
        let (time, released) = response
            .ctx
            .input(|input| (input.time, input.pointer.primary_released()));
        if response.clicked_by(egui::PointerButton::Primary) {
            if let Some(position) = response.interact_pointer_pos() {
                let options = response.ctx.options(|options| options.input_options);
                return self.click(
                    time,
                    position,
                    options.max_double_click_delay,
                    options.max_click_dist,
                );
            }
        }
        if released {
            self.previous = None;
        }
        false
    }

    fn click(
        &mut self,
        time: f64,
        position: egui::Pos2,
        max_delay: f64,
        max_distance: f32,
    ) -> bool {
        if self
            .previous
            .is_some_and(|(previous_time, previous_position)| {
                time >= previous_time
                    && time - previous_time < max_delay
                    && position.distance_sq(previous_position) <= max_distance * max_distance
            })
        {
            self.previous = None;
            true
        } else {
            self.previous = Some((time, position));
            false
        }
    }
}

/// Precomputed per-click projection; scanning a cloud never allocates another
/// coordinate array, and ordinary camera frames never scan points on the CPU.
struct Projection {
    matrix: Mat4,
    camera: Camera,
    rect: egui::Rect,
}

impl Projection {
    fn new(camera: Camera, rect: egui::Rect) -> Self {
        Self {
            matrix: camera.matrix(rect.width() / rect.height().max(1.0)),
            camera,
            rect,
        }
    }

    /// Intersect the orthographic cursor ray with a world Z plane; no cloud hit needed.
    fn on_z_plane(&self, cursor: egui::Pos2, z: f32) -> Option<[f32; 3]> {
        if !self.rect.contains(cursor) || !z.is_finite() {
            return None;
        }
        let aspect = self.rect.width() / self.rect.height();
        let half = self.camera.half_height(aspect);
        let x = (2.0 * (cursor.x - self.rect.left()) / self.rect.width() - 1.0) * half * aspect;
        let y = (1.0 - 2.0 * (cursor.y - self.rect.top()) / self.rect.height()) * half;
        let (direction, right, up) = self.camera.basis();
        if direction.z.abs() < 1e-6 {
            return None;
        }
        let plane = self.camera.target + right * x + up * y;
        let local_z = z * self.camera.world_scale - self.camera.origin.z;
        let local = plane + direction * ((local_z - plane.z) / direction.z);
        let world = (local + self.camera.origin) / self.camera.world_scale;
        world.is_finite().then_some([world.x, world.y, z])
    }

    fn point(&self, point: [f32; 3]) -> Option<(egui::Pos2, f32)> {
        self.unbounded_point(point)
            .filter(|(position, _)| self.rect.contains(*position))
    }

    // Overlay lines may cross the view even when their endpoints lie outside it;
    // egui clips the resulting segment to the viewport without dropping it.
    fn unbounded_point(&self, point: [f32; 3]) -> Option<(egui::Pos2, f32)> {
        let local = Vec3::from_array(point) * self.camera.world_scale - self.camera.origin;
        let clip = self.matrix.project_point3(local);
        if !clip.is_finite() || clip.z.abs() > 1.0 {
            return None;
        }
        Some((
            egui::pos2(
                self.rect.left() + (clip.x + 1.0) * self.rect.width() * 0.5,
                self.rect.top() + (1.0 - clip.y) * self.rect.height() * 0.5,
            ),
            clip.z,
        ))
    }
}

fn within_ranges(point: [f32; 3], ranges: [[f32; 2]; 3]) -> bool {
    point
        .iter()
        .zip(ranges)
        .all(|(value, [lo, hi])| *value >= lo && *value <= hi)
}

fn clip_segment(start: [f32; 3], end: [f32; 3], ranges: [[f32; 2]; 3]) -> Option<[[f32; 3]; 2]> {
    let mut enter = 0.0_f64;
    let mut leave = 1.0_f64;
    for axis in 0..3 {
        let origin = f64::from(start[axis]);
        let delta = f64::from(end[axis]) - origin;
        let [lo, hi] = ranges[axis].map(f64::from);
        if delta == 0.0 {
            if origin < lo || origin > hi {
                return None;
            }
        } else {
            let a = (lo - origin) / delta;
            let b = (hi - origin) / delta;
            enter = enter.max(a.min(b));
            leave = leave.min(a.max(b));
            if enter > leave {
                return None;
            }
        }
    }
    Some([enter, leave].map(|t| {
        std::array::from_fn(|axis| {
            (f64::from(start[axis]) + t * (f64::from(end[axis]) - f64::from(start[axis]))) as f32
        })
    }))
}

fn pick_point(
    layers: &[RenderLayer],
    layer_id: u64,
    camera: Camera,
    rect: egui::Rect,
    cursor: egui::Pos2,
    point_size: f32,
    ranges: [[f32; 2]; 3],
) -> Option<[f32; 3]> {
    if !rect.contains(cursor) {
        return None;
    }
    // Only layers actually supplied for rendering are eligible. Hidden layers
    // and every layer other than the editor's selected one cannot be picked.
    let layer = layers.iter().find(|layer| layer.id == layer_id)?;
    let projection = Projection::new(camera, rect);
    let radius_squared = (point_size.clamp(1.0, 16.0) * 0.5).powi(2);
    let tolerance_squared = 6.0_f32.max(point_size * 0.5).powi(2);
    let mut direct: Option<([f32; 3], f32, f32)> = None;
    let mut nearby: Option<([f32; 3], f32, f32)> = None;
    for point in layer.points.iter().copied() {
        if !within_ranges(point, ranges) {
            continue;
        }
        let Some((position, depth)) = projection.point(point) else {
            continue;
        };
        let distance = position.distance_sq(cursor);
        if distance > tolerance_squared {
            continue;
        }
        if distance <= radius_squared {
            // A point sprite actually covers the clicked pixel: emulate the
            // depth buffer, choosing the front surface before screen proximity.
            if direct.is_none_or(|(_, old_depth, old_distance)| {
                depth < old_depth || (depth == old_depth && distance < old_distance)
            }) {
                direct = Some((point, depth, distance));
            }
        } else if nearby.is_none_or(|(_, old_depth, old_distance)| {
            distance < old_distance || (distance == old_distance && depth < old_depth)
        }) {
            nearby = Some((point, depth, distance));
        }
    }
    direct.or(nearby).map(|(point, _, _)| point)
}

#[derive(Clone, Copy, Debug)]
struct Camera {
    target: Vec3,
    origin: Vec3,
    world_scale: f32,
    ground: f32,
    yaw: f32,
    pitch: f32,
    zoom: f32,
}

impl Default for Camera {
    fn default() -> Self {
        Self {
            target: Vec3::ZERO,
            origin: Vec3::ZERO,
            world_scale: 1.0,
            ground: 0.0,
            yaw: -1.05,
            pitch: 0.85,
            zoom: 1.2,
        }
    }
}

impl Camera {
    fn fitted(bounds: [[f32; 2]; 3]) -> Option<Self> {
        if bounds
            .iter()
            .any(|[lo, hi]| !lo.is_finite() || !hi.is_finite() || lo > hi)
        {
            return None;
        }
        // Compute the extent in f64: a valid f32 range can overflow f32 subtraction.
        let extent = bounds.map(|[lo, hi]| f64::from(hi) - f64::from(lo));
        let radius = (extent.iter().map(|v| v * v).sum::<f64>()).sqrt() * 0.5;
        let largest_coordinate = bounds
            .iter()
            .flatten()
            .map(|v| f64::from(*v).abs())
            .fold(0.0, f64::max);
        // A degenerate cloud far from zero still needs a finite origin and a
        // useful minimum view scale. Stay above the source f32 precision floor.
        let radius = radius
            .max(largest_coordinate * f64::from(f32::EPSILON) * 8.0)
            .max(0.000_001);
        let world_scale = (1.0 / radius) as f32;
        let origin = bounds.map(|[lo, hi]| ((f64::from(lo) + f64::from(hi)) * 0.5 / radius) as f32);
        Some(Self {
            target: Vec3::ZERO,
            origin: Vec3::from_array(origin),
            world_scale,
            ground: (-extent[2] * 0.5 / radius) as f32 - 0.001,
            ..Self::default()
        })
    }

    fn basis(self) -> (Vec3, Vec3, Vec3) {
        let (sy, cy) = self.yaw.sin_cos();
        let (sp, cp) = self.pitch.sin_cos();
        let direction = Vec3::new(cy * cp, sy * cp, sp);
        let right = Vec3::new(-sy, cy, 0.0);
        let up = direction.cross(right);
        (direction, right, up)
    }

    fn half_height(self, aspect: f32) -> f32 {
        self.zoom * (1.0 / aspect.max(0.001)).max(1.0)
    }

    fn matrix(self, aspect: f32) -> Mat4 {
        let (direction, _, up) = self.basis();
        let half_height = self.half_height(aspect);
        let depth = (self.zoom * 4.0).max(1000.0);
        let view = Mat4::look_at_rh(self.target + direction * 10.0, self.target, up);
        Mat4::orthographic_rh_gl(
            -half_height * aspect,
            half_height * aspect,
            -half_height,
            half_height,
            -depth,
            depth,
        ) * view
    }

    fn pan(&mut self, dx: f32, dy: f32, height: f32, aspect: f32) {
        let (_, right, up) = self.basis();
        let units = self.half_height(aspect) * 2.0 / height.max(1.0);
        self.target += (-right * dx + up * dy) * units;
    }

    fn grid(self) -> Vec<[f32; 3]> {
        let desired_world = f64::from(self.zoom) / f64::from(self.world_scale) / 4.0;
        let power = 10.0_f64.powf(desired_world.log10().floor());
        let mantissa = desired_world / power;
        let nice = if mantissa < 2.0 {
            1.0
        } else if mantissa < 5.0 {
            2.0
        } else {
            5.0
        };
        let spacing = (nice * power * f64::from(self.world_scale)) as f32;
        let spacing = spacing.max(0.000_001);
        let cx = (self.target.x / spacing).floor() * spacing - self.origin.x.rem_euclid(spacing);
        let cy = (self.target.y / spacing).floor() * spacing - self.origin.y.rem_euclid(spacing);
        let extent = spacing * 12.0;
        let z = self.ground;
        let mut points = Vec::with_capacity(106);
        for i in -12..=12 {
            let x = cx + i as f32 * spacing;
            let y = cy + i as f32 * spacing;
            points.extend([[x, cy - extent, z], [x, cy + extent, z]]);
            points.extend([[cx - extent, y, z], [cx + extent, y, z]]);
        }
        // Origin axes use the same world coordinates as the imported PCD.
        points.extend([
            [cx - extent, -self.origin.y, z],
            [cx + extent, -self.origin.y, z],
        ]);
        points.extend([
            [-self.origin.x, cy - extent, z],
            [-self.origin.x, cy + extent, z],
        ]);
        points.extend([
            [-self.origin.x, -self.origin.y, z],
            [-self.origin.x, -self.origin.y, z + extent * 0.25],
        ]);
        points
    }
}

struct GpuLayer {
    vao: glow::VertexArray,
    buffer: glow::Buffer,
    points: Arc<Vec<[f32; 3]>>,
    count: i32,
    height: [f32; 2],
}

struct Renderer {
    program: glow::Program,
    matrix: Option<glow::UniformLocation>,
    scale: Option<glow::UniformLocation>,
    origin: Option<glow::UniformLocation>,
    point_size: Option<glow::UniformLocation>,
    height: Option<glow::UniformLocation>,
    tint: Option<glow::UniformLocation>,
    kind: Option<glow::UniformLocation>,
    clip_enabled: Option<glow::UniformLocation>,
    clip_min: Option<glow::UniformLocation>,
    clip_max: Option<glow::UniformLocation>,
    grid_vao: glow::VertexArray,
    grid_buffer: glow::Buffer,
    layers: HashMap<u64, GpuLayer>,
    error: Option<String>,
    destroyed: bool,
    desktop: bool,
}

impl Renderer {
    fn new(gl: &glow::Context) -> Result<Self, String> {
        let desktop = !gl.version().is_embedded;
        let version = if desktop {
            "#version 330 core\n"
        } else {
            "#version 300 es\nprecision highp float;\n"
        };
        let vertex = format!("{version}{VERTEX_SHADER}");
        let fragment = format!("{version}{FRAGMENT_SHADER}");
        // SAFETY: eframe supplies the current GL context on this thread. All GPU
        // objects are subsequently accessed only from its paint/on_exit callbacks.
        unsafe {
            let program = compile_program(gl, &vertex, &fragment)?;
            let (grid_vao, grid_buffer) = match create_buffer(gl) {
                Ok(value) => value,
                Err(error) => {
                    gl.delete_program(program);
                    return Err(error);
                }
            };
            Ok(Self {
                matrix: gl.get_uniform_location(program, "u_matrix"),
                scale: gl.get_uniform_location(program, "u_scale"),
                origin: gl.get_uniform_location(program, "u_origin"),
                point_size: gl.get_uniform_location(program, "u_point_size"),
                height: gl.get_uniform_location(program, "u_height"),
                tint: gl.get_uniform_location(program, "u_tint"),
                kind: gl.get_uniform_location(program, "u_kind"),
                clip_enabled: gl.get_uniform_location(program, "u_clip_enabled"),
                clip_min: gl.get_uniform_location(program, "u_clip_min"),
                clip_max: gl.get_uniform_location(program, "u_clip_max"),
                program,
                grid_vao,
                grid_buffer,
                layers: HashMap::new(),
                error: None,
                destroyed: false,
                desktop,
            })
        }
    }

    fn upload(&mut self, gl: &glow::Context, layer: &RenderLayer) -> Result<(), String> {
        if self
            .layers
            .get(&layer.id)
            .is_some_and(|cached| Arc::ptr_eq(&cached.points, &layer.points))
        {
            return Ok(());
        }
        if let Some(old) = self.layers.remove(&layer.id) {
            unsafe {
                gl.delete_vertex_array(old.vao);
                gl.delete_buffer(old.buffer);
            }
        }
        let count = i32::try_from(layer.points.len())
            .map_err(|_| "单图层点数超过 OpenGL 绘制上限".to_owned())?;
        let mut min_z = f32::INFINITY;
        let mut max_z = f32::NEG_INFINITY;
        for point in layer.points.iter() {
            min_z = min_z.min(point[2]);
            max_z = max_z.max(point[2]);
        }
        let height = if layer.points.is_empty() || min_z == max_z {
            [0.0, 0.0]
        } else {
            let inverse = 1.0 / (f64::from(max_z) - f64::from(min_z));
            [inverse as f32, (f64::from(min_z) * inverse) as f32]
        };
        unsafe {
            let (vao, buffer) = create_buffer(gl)?;
            gl.bind_vertex_array(Some(vao));
            gl.bind_buffer(glow::ARRAY_BUFFER, Some(buffer));
            gl.buffer_data_u8_slice(
                glow::ARRAY_BUFFER,
                bytemuck::cast_slice(layer.points.as_slice()),
                glow::STATIC_DRAW,
            );
            let error = gl.get_error();
            if error != glow::NO_ERROR {
                gl.delete_vertex_array(vao);
                gl.delete_buffer(buffer);
                return Err(format!("点云上传到显卡失败 (OpenGL 0x{error:04x})"));
            }
            let old = self.layers.insert(
                layer.id,
                GpuLayer {
                    vao,
                    buffer,
                    points: Arc::clone(&layer.points),
                    count,
                    height,
                },
            );
            if let Some(old) = old {
                gl.delete_vertex_array(old.vao);
                gl.delete_buffer(old.buffer);
            }
        }
        Ok(())
    }

    fn paint(
        &mut self,
        gl: &glow::Context,
        mut info: egui::PaintCallbackInfo,
        layers: &[RenderLayer],
        camera: Camera,
        point_size: f32,
        selection: Option<(u64, [[f32; 2]; 3])>,
    ) {
        // egui_glow restores its program, VAO, blend, viewport and scissor after
        // callbacks. Preserve the extra GL state touched here as well.
        unsafe {
            let old_depth_mask = gl.get_parameter_bool(glow::DEPTH_WRITEMASK);
            let old_depth_func = gl.get_parameter_i32(glow::DEPTH_FUNC) as u32;
            let old_depth_clear = gl.get_parameter_f32(glow::DEPTH_CLEAR_VALUE);
            let old_array_buffer = gl.get_parameter_buffer(glow::ARRAY_BUFFER_BINDING);
            let old_point_size_enabled = self.desktop && gl.is_enabled(glow::PROGRAM_POINT_SIZE);
            let mut old_clear = [0.0; 4];
            gl.get_parameter_f32_slice(glow::COLOR_CLEAR_VALUE, &mut old_clear);
            info.clip_rect = info.clip_rect.intersect(info.viewport);
            let clip = info.clip_rect_in_pixels();
            gl.scissor(
                clip.left_px,
                clip.from_bottom_px,
                clip.width_px,
                clip.height_px,
            );
            gl.enable(glow::SCISSOR_TEST);
            gl.depth_mask(true);
            gl.clear_depth_f32(1.0);
            gl.clear_color(242.0 / 255.0, 232.0 / 255.0, 244.0 / 255.0, 1.0);
            gl.clear(glow::COLOR_BUFFER_BIT | glow::DEPTH_BUFFER_BIT);
            gl.enable(glow::DEPTH_TEST);
            gl.depth_func(glow::LEQUAL);
            gl.disable(glow::BLEND);
            gl.disable(glow::CULL_FACE);
            if self.desktop {
                gl.enable(glow::PROGRAM_POINT_SIZE);
            }

            self.layers.retain(|id, layer| {
                let keep = layers.iter().any(|visible| visible.id == *id);
                if !keep {
                    gl.delete_vertex_array(layer.vao);
                    gl.delete_buffer(layer.buffer);
                }
                keep
            });
            self.error = None;
            for layer in layers {
                if let Err(error) = self.upload(gl, layer) {
                    self.error = Some(error);
                }
            }
            gl.use_program(Some(self.program));
            let aspect = info.viewport.width() / info.viewport.height().max(1.0);
            gl.uniform_matrix_4_f32_slice(
                self.matrix.as_ref(),
                false,
                &camera.matrix(aspect).to_cols_array(),
            );
            gl.uniform_1_f32(
                self.point_size.as_ref(),
                point_size.clamp(1.0, 16.0) * info.pixels_per_point,
            );
            gl.uniform_1_f32(self.scale.as_ref(), 1.0);
            gl.uniform_3_f32(self.origin.as_ref(), 0.0, 0.0, 0.0);
            gl.uniform_1_i32(self.kind.as_ref(), 1);
            gl.uniform_1_i32(self.clip_enabled.as_ref(), 0);
            let grid = camera.grid();
            gl.bind_vertex_array(Some(self.grid_vao));
            gl.bind_buffer(glow::ARRAY_BUFFER, Some(self.grid_buffer));
            gl.buffer_data_u8_slice(
                glow::ARRAY_BUFFER,
                bytemuck::cast_slice(grid.as_slice()),
                glow::STREAM_DRAW,
            );
            gl.uniform_3_f32(self.tint.as_ref(), 0.80, 0.73, 0.83);
            gl.draw_arrays(glow::LINES, 0, 100);
            for (i, color) in [[0.70, 0.24, 0.25], [0.20, 0.62, 0.34], [0.25, 0.48, 0.85]]
                .iter()
                .enumerate()
            {
                gl.uniform_3_f32(self.tint.as_ref(), color[0], color[1], color[2]);
                gl.draw_arrays(glow::LINES, 100 + i as i32 * 2, 2);
            }
            gl.uniform_1_f32(self.scale.as_ref(), camera.world_scale);
            gl.uniform_3_f32(
                self.origin.as_ref(),
                camera.origin.x,
                camera.origin.y,
                camera.origin.z,
            );
            gl.uniform_1_i32(self.kind.as_ref(), 0);
            for layer in layers {
                if let Some(gpu) = self.layers.get(&layer.id) {
                    // Scene IDs start at one; zero is the preview-only highlight buffer.
                    gl.uniform_1_i32(self.kind.as_ref(), if layer.id == 0 { 2 } else { 0 });
                    if let Some((_, ranges)) = selection.filter(|(id, _)| *id == layer.id) {
                        gl.uniform_1_i32(self.clip_enabled.as_ref(), 1);
                        gl.uniform_3_f32(
                            self.clip_min.as_ref(),
                            ranges[0][0],
                            ranges[1][0],
                            ranges[2][0],
                        );
                        gl.uniform_3_f32(
                            self.clip_max.as_ref(),
                            ranges[0][1],
                            ranges[1][1],
                            ranges[2][1],
                        );
                    } else {
                        gl.uniform_1_i32(self.clip_enabled.as_ref(), 0);
                    }
                    gl.bind_vertex_array(Some(gpu.vao));
                    gl.uniform_2_f32(self.height.as_ref(), gpu.height[0], gpu.height[1]);
                    gl.uniform_3_f32(
                        self.tint.as_ref(),
                        layer.tint[0],
                        layer.tint[1],
                        layer.tint[2],
                    );
                    gl.draw_arrays(glow::POINTS, 0, gpu.count);
                }
            }
            gl.bind_buffer(glow::ARRAY_BUFFER, old_array_buffer);
            gl.depth_mask(old_depth_mask);
            gl.depth_func(old_depth_func);
            gl.clear_depth_f32(old_depth_clear);
            gl.clear_color(old_clear[0], old_clear[1], old_clear[2], old_clear[3]);
            if self.desktop && !old_point_size_enabled {
                gl.disable(glow::PROGRAM_POINT_SIZE);
            }
        }
    }

    fn destroy(&mut self, gl: &glow::Context) {
        if self.destroyed {
            return;
        }
        unsafe {
            for (_, layer) in self.layers.drain() {
                gl.delete_vertex_array(layer.vao);
                gl.delete_buffer(layer.buffer);
            }
            gl.delete_vertex_array(self.grid_vao);
            gl.delete_buffer(self.grid_buffer);
            gl.delete_program(self.program);
        }
        self.destroyed = true;
    }
}

unsafe fn create_buffer(gl: &glow::Context) -> Result<(glow::VertexArray, glow::Buffer), String> {
    let vao = gl.create_vertex_array()?;
    let buffer = match gl.create_buffer() {
        Ok(buffer) => buffer,
        Err(error) => {
            gl.delete_vertex_array(vao);
            return Err(error);
        }
    };
    let old_vao = gl.get_parameter_vertex_array(glow::VERTEX_ARRAY_BINDING);
    let old_buffer = gl.get_parameter_buffer(glow::ARRAY_BUFFER_BINDING);
    gl.bind_vertex_array(Some(vao));
    gl.bind_buffer(glow::ARRAY_BUFFER, Some(buffer));
    gl.enable_vertex_attrib_array(0);
    gl.vertex_attrib_pointer_f32(0, 3, glow::FLOAT, false, 12, 0);
    gl.bind_vertex_array(old_vao);
    gl.bind_buffer(glow::ARRAY_BUFFER, old_buffer);
    Ok((vao, buffer))
}

unsafe fn compile_program(
    gl: &glow::Context,
    vertex: &str,
    fragment: &str,
) -> Result<glow::Program, String> {
    let program = gl.create_program()?;
    let mut compiled = Vec::new();
    let result = (|| {
        for (kind, source) in [
            (glow::VERTEX_SHADER, vertex),
            (glow::FRAGMENT_SHADER, fragment),
        ] {
            let shader = gl.create_shader(kind)?;
            compiled.push(shader);
            gl.attach_shader(program, shader);
            gl.shader_source(shader, source);
            gl.compile_shader(shader);
            if !gl.get_shader_compile_status(shader) {
                return Err(gl.get_shader_info_log(shader));
            }
        }
        gl.link_program(program);
        if !gl.get_program_link_status(program) {
            return Err(gl.get_program_info_log(program));
        }
        Ok(program)
    })();
    for shader in compiled {
        gl.detach_shader(program, shader);
        gl.delete_shader(shader);
    }
    if result.is_err() {
        gl.delete_program(program);
    }
    result
}

const VERTEX_SHADER: &str = r#"
layout(location = 0) in vec3 a_position;
uniform mat4 u_matrix;
uniform float u_scale;
uniform vec3 u_origin;
uniform float u_point_size;
uniform vec2 u_height;
uniform vec3 u_tint;
uniform int u_kind;
uniform int u_clip_enabled;
uniform vec3 u_clip_min;
uniform vec3 u_clip_max;
out vec3 v_color;
void main() {
    gl_Position = u_matrix * vec4(a_position * u_scale - u_origin, 1.0);
    if (u_clip_enabled == 1 && (any(lessThan(a_position, u_clip_min)) || any(greaterThan(a_position, u_clip_max)))) {
        gl_Position = vec4(0.0, 0.0, 2.0, 1.0);
    }
    gl_PointSize = u_point_size;
    float t = clamp(a_position.z * u_height.x - u_height.y, 0.0, 1.0);
    vec3 low = vec3(0.18, 0.56, 0.91);
    vec3 mid = vec3(0.16, 0.83, 0.66);
    vec3 high = vec3(1.0, 0.71, 0.22);
    vec3 elevation = t < 0.5 ? mix(low, mid, t * 2.0) : mix(mid, high, t * 2.0 - 1.0);
    v_color = u_kind != 0 ? u_tint : mix(elevation, u_tint, 0.12);
}
"#;

const FRAGMENT_SHADER: &str = r#"
in vec3 v_color;
uniform int u_kind;
out vec4 out_color;
void main() {
    if (u_kind != 1) {
        vec2 p = gl_PointCoord * 2.0 - 1.0;
        if (dot(p, p) > 1.0) discard;
    }
    out_color = vec4(v_color, 1.0);
}
"#;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn viewport_double_click_survives_toolbar_click_becoming_an_egui_triple_click() {
        let ctx = egui::Context::default();
        let mut clicks = ViewportClicks::default();
        let mut selected = 0;
        let mut global_doubles = 0;
        let mut global_triples = 0;
        for (time, pressed, position) in [
            (1.00, true, egui::pos2(1042.0, 166.0)),
            (1.04, false, egui::pos2(1042.0, 166.0)),
            (1.47, true, egui::pos2(496.0, 484.0)),
            (1.51, false, egui::pos2(496.0, 484.0)),
            (1.59, true, egui::pos2(496.0, 484.0)),
            (1.63, false, egui::pos2(496.0, 484.0)),
        ] {
            let raw = egui::RawInput {
                screen_rect: Some(egui::Rect::from_min_size(
                    egui::Pos2::ZERO,
                    egui::vec2(1280.0, 800.0),
                )),
                time: Some(time),
                events: vec![
                    egui::Event::PointerMoved(position),
                    egui::Event::PointerButton {
                        pos: position,
                        button: egui::PointerButton::Primary,
                        pressed,
                        modifiers: egui::Modifiers::default(),
                    },
                ],
                ..Default::default()
            };
            let _ = ctx.run(raw, |ctx| {
                egui::CentralPanel::default().show(ctx, |ui| {
                    let response = ui.interact(
                        egui::Rect::from_min_max(egui::pos2(228.0, 54.0), egui::pos2(976.0, 792.0)),
                        egui::Id::new("test_viewport"),
                        egui::Sense::click_and_drag(),
                    );
                    if time > 1.1 {
                        global_doubles += usize::from(response.double_clicked());
                        global_triples += usize::from(response.triple_clicked());
                    }
                    selected += usize::from(clicks.update(&response));
                });
            });
        }
        assert_eq!(global_doubles, 0, "Reproduce the egui global count problem");
        assert_eq!(global_triples, 1);
        assert_eq!(
            selected, 1,
            "The two viewport clicks must produce exactly one selection"
        );
    }

    #[test]
    fn viewport_double_click_rejects_slow_or_distant_clicks_and_consumes_each_pair() {
        let mut clicks = ViewportClicks::default();
        let a = egui::pos2(30.0, 40.0);
        let b = egui::pos2(60.0, 70.0);
        assert!(!clicks.click(1.0, a, 0.3, 6.0));
        assert!(!clicks.click(1.5, a, 0.3, 6.0));
        assert!(!clicks.click(1.6, b, 0.3, 6.0));
        assert!(clicks.click(1.7, b + egui::vec2(1.0, 1.0), 0.3, 6.0));
        assert!(!clicks.click(1.8, b, 0.3, 6.0));
        assert!(clicks.click(1.9, b, 0.3, 6.0));
    }

    fn top_camera() -> Camera {
        Camera {
            yaw: -std::f32::consts::FRAC_PI_2,
            pitch: std::f32::consts::FRAC_PI_2,
            ..Camera::default()
        }
    }

    fn test_layer(id: u64, points: Vec<[f32; 3]>) -> RenderLayer {
        RenderLayer {
            id,
            points: Arc::new(points),
            tint: [1.0, 1.0, 1.0],
        }
    }

    fn test_rect() -> egui::Rect {
        egui::Rect::from_min_size(egui::pos2(220.0, 70.0), egui::vec2(800.0, 600.0))
    }

    const FULL_RANGE: [[f32; 2]; 3] = [[-10.0, 10.0]; 3];

    #[test]
    fn picking_a_pixel_selects_the_front_surface_independent_of_record_order() {
        let camera = top_camera();
        let rect = test_rect();
        let front = [0.0, 0.0, 1.0];
        let back = [0.0, 0.0, -1.0];
        for points in [vec![front, back], vec![back, front]] {
            let layers = [test_layer(7, points)];
            assert_eq!(
                pick_point(&layers, 7, camera, rect, rect.center(), 3.0, FULL_RANGE),
                Some(front)
            );
        }
    }

    #[test]
    fn picking_does_not_fall_back_to_unselected_or_hidden_layers() {
        let camera = top_camera();
        let rect = test_rect();
        let layers = [test_layer(8, vec![[0.0; 3]])];
        assert_eq!(
            pick_point(&layers, 7, camera, rect, rect.center(), 3.0, FULL_RANGE),
            None
        );
        assert_eq!(
            pick_point(&[], 7, camera, rect, rect.center(), 3.0, FULL_RANGE),
            None
        );
        let layers = [
            test_layer(7, vec![[0.5, 0.5, 0.0]]),
            test_layer(8, vec![[0.0; 3]]),
        ];
        assert_eq!(
            pick_point(&layers, 7, camera, rect, rect.center(), 3.0, FULL_RANGE),
            None
        );
    }

    #[test]
    fn picking_respects_the_visible_coordinate_range() {
        let camera = top_camera();
        let rect = test_rect();
        let layers = [test_layer(7, vec![[0.0, 0.0, 1.0], [0.0, 0.0, -1.0]])];
        let ranges = [[-10.0, 10.0], [-10.0, 10.0], [-2.0, 0.0]];
        assert_eq!(
            pick_point(&layers, 7, camera, rect, rect.center(), 3.0, ranges),
            Some([0.0, 0.0, -1.0])
        );
        assert_eq!(
            pick_point(
                &layers,
                7,
                camera,
                rect,
                rect.center(),
                3.0,
                [[4.0, 5.0]; 3]
            ),
            None
        );
    }

    #[test]
    fn picking_tolerance_ignores_empty_space_and_prefers_the_nearest_point() {
        let camera = top_camera();
        let rect = test_rect();
        let layers = [test_layer(7, vec![[0.0; 3], [0.02, 0.0, 0.0]])];
        let center = rect.center();
        assert_eq!(
            pick_point(
                &layers,
                7,
                camera,
                rect,
                center + egui::vec2(0.0, 5.0),
                2.0,
                FULL_RANGE
            ),
            Some([0.0; 3])
        );
        assert_eq!(
            pick_point(
                &layers,
                7,
                camera,
                rect,
                center + egui::vec2(0.0, 8.0),
                2.0,
                FULL_RANGE
            ),
            None
        );
        assert_eq!(
            pick_point(
                &layers,
                7,
                camera,
                rect,
                rect.left_top() - egui::vec2(1.0, 1.0),
                2.0,
                FULL_RANGE
            ),
            None
        );
    }

    #[test]
    fn picking_and_projection_follow_camera_pan_and_normalized_cloud_origin() {
        let mut camera = Camera::fitted([[1000.0, 1010.0], [-500.0, -490.0], [0.0, 5.0]]).unwrap();
        let rect = test_rect();
        camera.pan(75.0, -42.0, rect.height(), rect.width() / rect.height());
        let point = [1004.0, -496.0, 2.0];
        let (position, _) = Projection::new(camera, rect).point(point).unwrap();
        let layers = [test_layer(7, vec![point])];
        assert_eq!(
            pick_point(
                &layers,
                7,
                camera,
                rect,
                position,
                3.0,
                [[-2000.0, 2000.0]; 3]
            ),
            Some(point)
        );
        assert_eq!(
            pick_point(
                &layers,
                7,
                camera,
                rect,
                rect.center(),
                3.0,
                [[-2000.0, 2000.0]; 3]
            ),
            None
        );
    }

    #[test]
    fn hull_preview_segments_are_clipped_to_editing_ranges() {
        assert_eq!(
            clip_segment([-2.0, 0.0, 0.0], [2.0, 0.0, 0.0], [[-1.0, 1.0]; 3]),
            Some([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
        );
        assert_eq!(
            clip_segment([2.0, 0.0, 0.0], [-2.0, 0.0, 0.0], [[-1.0, 1.0]; 3]),
            Some([[1.0, 0.0, 0.0], [-1.0, 0.0, 0.0]])
        );
        assert_eq!(
            clip_segment([-2.0, 3.0, 0.0], [2.0, 3.0, 0.0], [[-1.0, 1.0]; 3]),
            None
        );
    }

    #[test]
    fn fit_keeps_all_corners_inside_wide_and_narrow_views() {
        let bounds = [[0.0, 28.0], [0.0, 16.0], [0.0, 3.8]];
        let camera = Camera::fitted(bounds).unwrap();
        for aspect in [0.3, 1.0, 2.5] {
            let matrix = camera.matrix(aspect);
            for x in bounds[0] {
                for y in bounds[1] {
                    for z in bounds[2] {
                        let clip = matrix.project_point3(
                            Vec3::new(x, y, z) * camera.world_scale - camera.origin,
                        );
                        assert!(clip.is_finite());
                        assert!(clip.x.abs() <= 1.0 && clip.y.abs() <= 1.0 && clip.z.abs() <= 1.0);
                    }
                }
            }
        }
    }

    #[test]
    fn top_view_and_single_point_fit_have_finite_transforms() {
        let mut camera = Camera::fitted([[3.0, 3.0], [5.0, 5.0], [-1.0, -1.0]]).unwrap();
        camera.yaw = -std::f32::consts::FRAC_PI_2;
        camera.pitch = std::f32::consts::FRAC_PI_2;
        assert!(camera.matrix(1.0).is_finite());
        let before = camera.target;
        camera.pan(10.0, 5.0, 600.0, 1.0);
        assert!(camera.target.is_finite());
        assert_ne!(camera.target, before);
        assert!(Camera::fitted([[f32::NAN, 1.0], [0.0, 1.0], [0.0, 1.0]]).is_none());
    }

    #[test]
    fn ground_tracks_minimum_height_after_translating_the_cloud() {
        for z in [[0.0, 4.0], [10.0, 14.0], [-25.0, -21.0]] {
            let camera = Camera::fitted([[0.0, 28.0], [0.0, 16.0], z]).unwrap();
            let displayed_minimum = z[0] * camera.world_scale - camera.origin.z;
            assert!((camera.ground - (displayed_minimum - 0.001)).abs() < 1.0e-6);
        }
    }

    #[test]
    fn far_from_origin_single_point_has_finite_camera_and_grid() {
        let camera = Camera::fitted([[f32::MAX, f32::MAX]; 3]).unwrap();
        assert!(camera.origin.is_finite());
        assert!(camera.matrix(1.0).is_finite());
        assert!(camera.grid().iter().flatten().all(|n| n.is_finite()));
    }

    #[test]
    fn fit_handles_finite_f32_ranges_without_extent_overflow() {
        let camera = Camera::fitted([[-f32::MAX, f32::MAX]; 3]).unwrap();
        assert!(camera.world_scale > 0.0 && camera.world_scale.is_finite());
        assert!(camera.target.is_finite());
        assert!(camera.matrix(1.0).is_finite());
        assert!(camera.grid().iter().flatten().all(|n| n.is_finite()));
    }
    #[test]
    fn polygon_click_unprojects_empty_space_to_world_xy_and_survives_camera_changes() {
        let mut camera = Camera::fitted([[10., 30.], [-20., 20.], [5., 8.]]).unwrap();
        camera.yaw = -std::f32::consts::FRAC_PI_2;
        camera.pitch = std::f32::consts::FRAC_PI_2;
        let rect = egui::Rect::from_min_size(egui::pos2(200., 50.), egui::vec2(700., 600.));
        let projection = Projection::new(camera, rect);
        let cursor = rect.center() + egui::vec2(100., -80.);
        let picked = projection.on_z_plane(cursor, 5.5).unwrap();
        let projected = projection.point(picked).unwrap().0;
        assert!(projected.distance(cursor) < 0.001);
        let raised = projection.on_z_plane(cursor, 7.5).unwrap();
        assert!((picked[0] - raised[0]).abs() < 0.0001);
        assert!((picked[1] - raised[1]).abs() < 0.0001);
        assert_eq!(picked[2], 5.5);
        assert!(projection
            .on_z_plane(rect.min - egui::vec2(1., 1.), 5.5)
            .is_none());
        camera.yaw += 0.4;
        camera.pitch -= 0.4;
        assert!(Projection::new(camera, rect).point(picked).is_some());
    }
}
