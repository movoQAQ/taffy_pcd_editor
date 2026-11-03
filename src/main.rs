mod region;
mod scene;
mod theme;
mod viewport;

use eframe::egui::{self, Color32, RichText};
use region::Region;
use scene::{Layer, Scene};
use std::{
    collections::BTreeMap,
    path::PathBuf,
    sync::{mpsc, Arc},
    thread,
    time::Duration,
};
use viewport::{RenderLayer, SelectionOverlay, Viewport};

const TITLE: &str = "Taffy PCD Editor · Rust";

enum Message {
    Loaded(Result<Layer, String>),
    Filtered(u64, Result<Layer, String>),
    Exported(PathBuf, Result<(), String>),
    Picked(Option<PathBuf>),
    RegionPreview(u64, u64, Result<(Arc<Region>, usize), String>),
    RegionDeleted(u64, Result<(Layer, usize), String>),
}

#[derive(Clone, Copy)]
enum PathAction {
    Import,
    Export(u64),
}

struct RegionEdit {
    layer_id: Option<u64>,
    picking: bool,
    picks: Vec<[f32; 3]>,
    expand_cm: f32,
    revision: u64,
    hull: Option<Arc<Region>>,
    count: Option<usize>,
    computing: bool,
    status: String,
}

impl Default for RegionEdit {
    fn default() -> Self {
        Self {
            layer_id: None,
            picking: false,
            picks: Vec::new(),
            expand_cm: 5.0,
            revision: 0,
            hull: None,
            count: None,
            computing: false,
            status: "双击点云选择边界点，至少 4 个不同点。".into(),
        }
    }
}

impl RegionEdit {
    fn invalidate(&mut self) {
        self.revision = self.revision.wrapping_add(1);
        self.hull = None;
        self.count = None;
        self.computing = false;
    }
    fn ranges_changed(&mut self, previous: [[f32; 2]; 3], current: [[f32; 2]; 3]) {
        if previous != current {
            self.invalidate();
            self.status = "XYZ 范围已改变，请重新计算区域。".into();
        }
    }

    fn clear(&mut self) {
        self.invalidate();
        self.layer_id = None;
        self.picking = false;
        self.picks.clear();
        self.status = "双击点云选择边界点，至少 4 个不同点。".into();
    }
}

struct Editor {
    scene: Scene,
    viewport: Viewport,
    tx: mpsc::Sender<Message>,
    rx: mpsc::Receiver<Message>,
    jobs: Vec<thread::JoinHandle<()>>,
    pending: usize,
    status: String,
    error: Option<String>,
    path_action: Option<PathAction>,
    path_text: String,
    picking: bool,
    delete_id: Option<u64>,
    ranges: [[f32; 2]; 3],
    voxel: f32,
    point_size: f32,
    widgets: BTreeMap<String, [f32; 4]>,
    telemetry: Option<PathBuf>,
    last_telemetry: String,
    region: RegionEdit,
    logo: egui::TextureHandle,
    panels: BTreeMap<String, [f32; 4]>,
    qa_candidates: Vec<[f32; 3]>,
    projected_candidates: Vec<[f32; 2]>,
}

impl Editor {
    fn new(cc: &eframe::CreationContext<'_>, paths: Vec<PathBuf>) -> Result<Self, String> {
        theme::configure(&cc.egui_ctx);
        let icon = eframe::icon_data::from_png_bytes(include_bytes!("../assets/icon.png"))
            .map_err(|e| e.to_string())?;
        let logo = cc.egui_ctx.load_texture(
            "original_taffy_icon",
            egui::ColorImage::from_rgba_unmultiplied(
                [icon.width as usize, icon.height as usize],
                &icon.rgba,
            ),
            egui::TextureOptions::LINEAR,
        );
        let gl = cc.gl.clone().ok_or("需要 OpenGL 图形环境")?;
        let (tx, rx) = mpsc::channel();
        let mut app = Self {
            scene: Scene::default(),
            viewport: Viewport::new(gl)?,
            tx,
            rx,
            jobs: Vec::new(),
            pending: 0,
            status: "导入 PCD，或将文件拖入窗口".into(),
            error: None,
            path_action: None,
            path_text: String::new(),
            picking: false,
            delete_id: None,
            ranges: [[0.0, 1.0]; 3],
            voxel: 0.05,
            point_size: 2.0,
            widgets: BTreeMap::new(),
            telemetry: std::env::var_os("TAFFY_UI_STATE").map(PathBuf::from),
            last_telemetry: String::new(),
            region: RegionEdit::default(),
            logo,
            panels: BTreeMap::new(),
            qa_candidates: Vec::new(),
            projected_candidates: Vec::new(),
        };
        for path in paths {
            app.load(path, &cc.egui_ctx);
        }
        Ok(app)
    }

    fn mark(&mut self, key: impl Into<String>, r: &egui::Response) {
        self.widgets.insert(
            key.into(),
            [r.rect.min.x, r.rect.min.y, r.rect.width(), r.rect.height()],
        );
    }

    fn job(&mut self, ctx: &egui::Context, f: impl FnOnce() -> Message + Send + 'static) {
        let tx = self.tx.clone();
        let ctx = ctx.clone();
        self.pending += 1;
        self.jobs.push(thread::spawn(move || {
            let _ = tx.send(f());
            ctx.request_repaint();
        }));
    }

    fn load(&mut self, path: PathBuf, ctx: &egui::Context) {
        self.status = format!("正在载入 {}…", path.display());
        self.job(ctx, move || Message::Loaded(Layer::load(path)));
    }

    fn select(&mut self, id: u64) {
        if self.region.layer_id.is_some_and(|source| source != id) {
            self.region.clear();
        }
        self.scene.selected = Some(id);
        if let Some(bounds) = self.scene.selected_layer().and_then(|l| l.bounds) {
            self.region.ranges_changed(self.ranges, bounds);
            self.ranges = bounds;
        }
    }

    fn fit(&mut self) {
        if let Some(bounds) = self.scene.bounds_visible() {
            self.viewport.fit(bounds);
        }
    }

    fn poll(&mut self) {
        while let Ok(message) = self.rx.try_recv() {
            match message {
                Message::RegionPreview(source, revision, result) => {
                    self.pending = self.pending.saturating_sub(1);
                    if self.region.layer_id != Some(source)
                        || self.region.revision != revision
                        || self.scene.selected != Some(source)
                    {
                        continue;
                    }
                    self.region.computing = false;
                    match result {
                        Ok((hull, count)) => {
                            self.region.hull = Some(hull);
                            self.region.count = Some(count);
                            self.region.status =
                                format!("凸包内命中 {count} 点（受 XYZ 范围约束）。");
                        }
                        Err(error) => {
                            self.region.status = error.clone();
                            self.fail(error);
                        }
                    }
                }
                Message::RegionDeleted(source, result) => {
                    self.pending = self.pending.saturating_sub(1);
                    if !self.scene.layers.iter().any(|l| l.id == source) {
                        self.status = "源图层已移除，已丢弃区域删除结果".into();
                        continue;
                    }
                    match result {
                        Ok((_, 0)) => self.status = "选区内没有可删除的点，图层保持原样".into(),
                        Ok((layer, count)) => {
                            if let Ok(Some(id)) = self.scene.complete_filter(source, Ok(layer)) {
                                self.select(id);
                                self.region.clear();
                                self.status =
                                    format!("已删除 {count} 点；结果已选中，原图层已隐藏");
                            }
                        }
                        Err(error) => self.fail(error),
                    }
                }
                Message::Picked(path) => {
                    self.picking = false;
                    if let Some(path) = path {
                        self.path_text = path.to_string_lossy().into_owned();
                    }
                }
                Message::Loaded(result) => {
                    self.pending = self.pending.saturating_sub(1);
                    match result {
                        Ok(layer) => {
                            self.status =
                                format!("已载入 {} · {} 点", layer.name, layer.points.len());
                            let id = self.scene.insert(layer);
                            self.select(id);
                            self.fit();
                        }
                        Err(e) => self.fail(e),
                    }
                }
                Message::Filtered(source, result) => {
                    self.pending = self.pending.saturating_sub(1);
                    match self.scene.complete_filter(source, result) {
                        Ok(Some(id)) => {
                            let count = self.scene.selected_layer().map_or(0, |l| l.points.len());
                            self.status = format!("滤波完成 · {count} 点；原图层已隐藏");
                            self.select(id);
                        }
                        Ok(None) => self.status = "源图层已移除，已丢弃滤波结果".into(),
                        Err(e) => self.fail(e),
                    }
                }
                Message::Exported(path, result) => {
                    self.pending = self.pending.saturating_sub(1);
                    match result {
                        Ok(()) => {
                            self.status = format!("已导出 {}（保留全部字段）", path.display())
                        }
                        Err(e) => self.fail(e),
                    }
                }
            }
        }
        self.jobs.retain_mut(|job| !job.is_finished());
    }

    fn fail(&mut self, message: String) {
        self.status = "操作失败，请查看提示".into();
        self.error = Some(message);
    }

    fn filter(&mut self, ctx: &egui::Context) {
        if let Some(layer) = self.scene.selected_layer().cloned() {
            let id = layer.id;
            let ranges = self.ranges;
            let voxel = self.voxel;
            self.status = "正在进行体素滤波…".into();
            self.job(ctx, move || {
                Message::Filtered(id, layer.filtered(ranges, voxel))
            });
        }
    }

    fn start_region(&mut self) {
        let Some(layer) = self.scene.selected_layer() else {
            return;
        };
        if !layer.visible || layer.points.is_empty() {
            return;
        }
        self.region.clear();
        self.region.layer_id = Some(layer.id);
        self.region.picking = true;
        self.region.status = "在点云上双击选点；可旋转视图选择不同高度。".into();
        // Read-only automation targets. They only locate real mouse clicks;
        // QA obtains the actual selected coordinates from the picking result.
        self.qa_candidates.clear();
        if self.telemetry.is_some() {
            if let Some(b) = layer.bounds {
                for [fx, fy] in [
                    [0.30, 0.30],
                    [0.70, 0.30],
                    [0.70, 0.70],
                    [0.30, 0.70],
                    [0.50, 0.25],
                    [0.50, 0.75],
                    [0.25, 0.50],
                    [0.75, 0.50],
                ] {
                    let x = b[0][0] + (b[0][1] - b[0][0]) * fx;
                    let y = b[1][0] + (b[1][1] - b[1][0]) * fy;
                    if let Some(point) = layer.points.iter().step_by(8).min_by(|a, b| {
                        ((a[0] - x).powi(2) + (a[1] - y).powi(2))
                            .total_cmp(&((b[0] - x).powi(2) + (b[1] - y).powi(2)))
                    }) {
                        self.qa_candidates.push(*point);
                    }
                }
            }
        }
    }

    fn calculate_region(&mut self, ctx: &egui::Context) {
        let Some(layer) = self.scene.selected_layer() else {
            return;
        };
        if self.region.layer_id != Some(layer.id) {
            return;
        }
        if self
            .ranges
            .iter()
            .any(|r| !r[0].is_finite() || !r[1].is_finite() || r[0] > r[1])
        {
            self.fail("XYZ 范围必须有限，且最小值不能超过最大值。".into());
            return;
        }
        let source = layer.id;
        let points = layer.points.clone();
        let picks = self.region.picks.clone();
        let expansion = self.region.expand_cm / 100.0;
        let ranges = self.ranges;
        self.region.invalidate();
        self.region.picking = false;
        self.region.computing = true;
        self.region.status = "正在计算凸包和区域点数…".into();
        let revision = self.region.revision;
        self.job(ctx, move || {
            let result = Region::from_picks(&picks, expansion).map(|hull| {
                let count = points.iter().filter(|p| hull.contains(**p, ranges)).count();
                (Arc::new(hull), count)
            });
            Message::RegionPreview(source, revision, result)
        });
    }

    fn delete_region(&mut self, ctx: &egui::Context) {
        let Some(layer) = self.scene.selected_layer().cloned() else {
            return;
        };
        if self.region.layer_id != Some(layer.id) {
            return;
        }
        let Some(region) = self.region.hull.clone() else {
            return;
        };
        let ranges = self.ranges;
        let source = layer.id;
        self.region.picking = false;
        self.status = "正在删除选中区域的点…".into();
        self.job(ctx, move || {
            Message::RegionDeleted(source, layer.delete_region(&region, ranges))
        });
    }

    fn region_controls(&mut self, ui: &mut egui::Ui, ctx: &egui::Context) {
        let ready = self.pending == 0
            && self
                .scene
                .selected_layer()
                .is_some_and(|l| l.visible && !l.points.is_empty());
        ui.add_enabled_ui(ready, |ui| {
            let start = ui.button(if self.region.picking {
                "停止选点"
            } else {
                "开始选点区域"
            });
            self.mark("region_start", &start);
            if start.clicked() {
                if self.region.picking {
                    self.region.picking = false;
                } else {
                    self.start_region();
                }
            }
            ui.weak("双击拾取真实点，拖动可旋转视图。");
            ui.label(format!("已选择 {} 个边界点", self.region.picks.len()));
            ui.horizontal(|ui| {
                let undo =
                    ui.add_enabled(!self.region.picks.is_empty(), egui::Button::new("撤销选点"));
                self.mark("region_undo_pick", &undo);
                if undo.clicked() {
                    self.region.picks.pop();
                    self.region.invalidate();
                    self.region.status = "已撤销最后一个选点，请重新计算区域。".into();
                }
                let clear = ui.button("清空选点");
                self.mark("region_clear", &clear);
                if clear.clicked() {
                    self.region.clear();
                }
            });
            ui.horizontal(|ui| {
                ui.label("XYZ 外扩 / 厘米");
                let expand = ui.add(
                    egui::DragValue::new(&mut self.region.expand_cm)
                        .speed(1.0)
                        .range(0.0..=10000.0)
                        .max_decimals(1),
                );
                self.mark("region_expand", &expand);
                if expand.changed() {
                    self.region.invalidate();
                    self.region.status = "外扩已改变，请重新计算凸包。".into();
                }
            });
            let calculate = ui.add_enabled(
                self.region.picks.len() >= 4,
                egui::Button::new("计算凸包区域"),
            );
            self.mark("region_calculate", &calculate);
            if calculate.clicked() {
                self.calculate_region(ctx);
            }
            let delete = ui.add_enabled(
                self.region.count.is_some_and(|n| n > 0),
                egui::Button::new(RichText::new("删除区域点").color(theme::BRAND))
                    .fill(theme::PRIMARY),
            );
            self.mark("region_delete", &delete);
            if delete.clicked() {
                self.delete_region(ctx);
            }
        });
        ui.label(
            RichText::new(&self.region.status)
                .small()
                .color(theme::SECTION),
        );
        ui.weak("生成编辑图层，原图层保留并隐藏。外扩为 0 时，边界点须不共面。");
    }

    fn path_modal(&mut self, ctx: &egui::Context) {
        let Some(action) = self.path_action else {
            return;
        };
        let import = matches!(action, PathAction::Import);
        let prefix = if import { "import" } else { "export" };
        let mut submit = false;
        let mut cancel = false;
        let modal = egui::Modal::new(egui::Id::new("path_modal")).show(ctx, |ui| {
            ui.set_width(560.0);
            ui.heading(if import {
                "导入 PCD 图层"
            } else {
                "导出选中图层"
            });
            ui.add_space(10.0);
            ui.label(if import {
                "文件路径（支持 binary PCD）"
            } else {
                "新文件路径（保留法线、强度等全部原始字段）"
            });
            let input = ui.add(
                egui::TextEdit::singleline(&mut self.path_text)
                    .desired_width(f32::INFINITY)
                    .hint_text("/path/to/map.pcd"),
            );
            self.mark(format!("{prefix}_path_input"), &input);
            ui.add_space(10.0);
            ui.horizontal(|ui| {
                if ui
                    .add_enabled(!self.picking, egui::Button::new("浏览…"))
                    .clicked()
                {
                    self.picking = true;
                    let tx = self.tx.clone();
                    let ctx = ctx.clone();
                    thread::spawn(move || {
                        let dialog = rfd::FileDialog::new().add_filter("Point Cloud", &["pcd"]);
                        let path = if import {
                            dialog.pick_file()
                        } else {
                            dialog.set_file_name("edited.pcd").save_file()
                        };
                        let _ = tx.send(Message::Picked(path));
                        ctx.request_repaint();
                    });
                }
                let ok = ui.add_enabled(
                    !self.picking && !self.path_text.trim().is_empty(),
                    egui::Button::new(if import { "打开" } else { "保存" }),
                );
                self.mark(format!("{prefix}_path_confirm"), &ok);
                submit = ok.clicked();
                let close = ui.add_enabled(!self.picking, egui::Button::new("取消"));
                self.mark("path_cancel", &close);
                cancel = close.clicked();
                if self.picking {
                    ui.spinner();
                }
            });
            if !import {
                ui.weak("保存为新的 PCD 文件；已有文件不会被覆盖。");
            }
        });
        if submit {
            let path = PathBuf::from(self.path_text.trim());
            self.path_action = None;
            match action {
                PathAction::Import => self.load(path, ctx),
                PathAction::Export(id) => {
                    if let Some(layer) = self.scene.layers.iter().find(|l| l.id == id).cloned() {
                        self.status = "正在导出…".into();
                        self.job(ctx, move || {
                            let result = layer.export(&path);
                            Message::Exported(path, result)
                        });
                    }
                }
            }
        } else if !self.picking && (cancel || modal.should_close()) {
            self.path_action = None;
        }
    }

    fn delete_modal(&mut self, ctx: &egui::Context) {
        let Some(id) = self.delete_id else {
            return;
        };
        let Some(layer) = self.scene.layers.iter().find(|l| l.id == id) else {
            self.delete_id = None;
            return;
        };
        let name = layer.name.clone();
        let mut confirm = false;
        let mut cancel = false;
        let modal = egui::Modal::new(egui::Id::new("delete_modal")).show(ctx, |ui| {
            ui.set_width(420.0);
            ui.heading("删除场景图层？");
            ui.add_space(8.0);
            ui.label(&name);
            ui.label("移除该图层及其未导出的编辑。磁盘上的 PCD 文件保留。");
            ui.add_space(12.0);
            ui.horizontal(|ui| {
                let yes =
                    ui.button(RichText::new("删除图层").color(Color32::from_rgb(255, 145, 128)));
                self.mark("delete_confirm", &yes);
                confirm = yes.clicked();
                let no = ui.button("取消");
                self.mark("delete_cancel", &no);
                cancel = no.clicked();
            });
        });
        if confirm {
            let previous_selection = self.scene.selected;
            self.scene.remove(id);
            if self.scene.selected != previous_selection {
                if let Some(selected) = self.scene.selected {
                    self.select(selected);
                }
            }
            if self.region.layer_id == Some(id) {
                self.region.clear();
            }
            self.status = format!("已移除图层 {name}");
            self.delete_id = None;
        } else if cancel || modal.should_close() {
            self.delete_id = None;
        }
    }

    fn telemetry(&mut self, ctx: &egui::Context) {
        let Some(path) = &self.telemetry else {
            return;
        };
        let data = serde_json::json!({
            "window_title": TITLE, "pixels_per_point": ctx.pixels_per_point(),
            "layers": self.scene.layers.iter().map(|l| serde_json::json!({"id":l.id,"name":l.name,"points":l.points.len(),"visible":l.visible})).collect::<Vec<_>>(),
            "selected_layer_id":self.scene.selected,"busy":self.pending>0,"status":self.status,
            "widgets":self.widgets,"error":self.error,"panels":self.panels,
            "ranges": self.ranges, "projected_candidates":self.projected_candidates,
            "region": { "layer_id":self.region.layer_id,"picking":self.region.picking,
                "picks":self.region.picks,"expand_cm":self.region.expand_cm,"count":self.region.count,
                "computing":self.region.computing,"status":self.region.status,
                "vertices":self.region.hull.as_ref().map(|h| &h.vertices),
                "planes":self.region.hull.as_ref().map(|h| &h.planes),
                "bounds":self.region.hull.as_ref().map(|h| h.bounds) },
            "modal_kind": if self.delete_id.is_some() { "delete" } else if matches!(self.path_action,Some(PathAction::Import)) { "import" } else if self.path_action.is_some() { "export" } else { "none" }
        }).to_string();
        if data != self.last_telemetry {
            let temporary = path.with_extension("tmp");
            if std::fs::write(&temporary, &data).is_ok() && std::fs::rename(temporary, path).is_ok()
            {
                self.last_telemetry = data;
            }
        }
    }
}

impl eframe::App for Editor {
    fn update(&mut self, ctx: &egui::Context, _: &mut eframe::Frame) {
        self.widgets.clear();
        self.panels.clear();
        self.poll();
        for path in ctx.input(|i| {
            i.raw
                .dropped_files
                .iter()
                .filter_map(|f| f.path.clone())
                .collect::<Vec<_>>()
        }) {
            self.load(path, ctx);
        }
        if self.path_action.is_none()
            && self.delete_id.is_none()
            && self.error.is_none()
            && !ctx.wants_keyboard_input()
        {
            if ctx.input(|i| i.key_pressed(egui::Key::Delete)) {
                self.delete_id = self.scene.selected;
            }
            if ctx.input(|i| i.key_pressed(egui::Key::Escape)) {
                self.region.clear();
            }
            if ctx.input(|i| i.key_pressed(egui::Key::F)) {
                self.fit();
            }
        }
        egui::TopBottomPanel::top("toolbar")
            .frame(egui::Frame::new().fill(theme::HEADER).inner_margin(10.0))
            .show(ctx, |ui| {
                theme::paint_pattern(ui);
                ui.horizontal(|ui| {
                    ui.image((self.logo.id(), egui::vec2(34.0, 34.0)));
                    ui.label(
                        RichText::new("taffy编辑器")
                            .size(20.0)
                            .strong()
                            .color(theme::BRAND),
                    );
                    ui.label(RichText::new("本地版 · Rust").color(theme::MUTED));
                    ui.separator();
                    let fit = ui.button("适配视图  F");
                    self.mark("fit_button", &fit);
                    if fit.clicked() {
                        self.fit();
                    }
                    let top = ui.button("俯视");
                    self.mark("top_button", &top);
                    if top.clicked() {
                        self.viewport.top();
                    }
                    ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                        if let Some(layer) = self.scene.selected_layer() {
                            ui.label(
                                RichText::new(format!("{} 点", layer.points.len()))
                                    .size(19.0)
                                    .strong()
                                    .color(theme::SECTION),
                            );
                        }
                    });
                });
            });
        egui::TopBottomPanel::bottom("status")
            .frame(egui::Frame::new().fill(theme::HEADER).inner_margin(5.0))
            .show(ctx, |ui| {
                ui.horizontal(|ui| {
                    if self.pending > 0 {
                        ui.spinner();
                    }
                    ui.label(&self.status);
                });
            });
        egui::SidePanel::left("layers")
            .exact_width(228.0)
            .resizable(false)
            .frame(egui::Frame::new().fill(theme::SIDEBAR).inner_margin(10.0))
            .show(ctx, |ui| {
                theme::paint_pattern(ui);
                ui.weak("工作区");
                ui.label(RichText::new("◈  点云查看器").strong().color(theme::BRAND));
                ui.add_space(8.0);
                let import = ui.add_enabled(
                    self.pending == 0,
                    egui::Button::new("＋  导入 PCD 文件")
                        .fill(theme::PRIMARY)
                        .min_size(egui::vec2(ui.available_width(), 36.0)),
                );
                self.mark("import_button", &import);
                if import.clicked() {
                    self.path_action = Some(PathAction::Import);
                    self.path_text.clear();
                }
                ui.add_space(18.0);
                ui.label(
                    RichText::new(format!("场景图层 · {}", self.scene.layers.len()))
                        .color(theme::MUTED),
                );
                let mut clicked = None;
                let mut remove = None;
                egui::ScrollArea::vertical()
                    .id_salt("layer_list")
                    .max_height(360.0)
                    .show(ui, |ui| {
                        for layer in &mut self.scene.layers {
                            ui.push_id(layer.id, |ui| {
                                ui.horizontal(|ui| {
                                    let visible = ui.checkbox(&mut layer.visible, "");
                                    self.widgets.insert(
                                        format!("layer_visible_{}", layer.id),
                                        rect_values(visible.rect),
                                    );
                                    let label = ui.add_sized(
                                        [139.0, 30.0],
                                        egui::Button::selectable(
                                            self.scene.selected == Some(layer.id),
                                            &layer.name,
                                        )
                                        .truncate(),
                                    );
                                    self.widgets.insert(
                                        format!("layer_select_{}", layer.id),
                                        rect_values(label.rect),
                                    );
                                    if label.clicked() {
                                        clicked = Some(layer.id);
                                    }
                                    label.on_hover_text(layer.source.display().to_string());
                                    let delete = ui.small_button("×").on_hover_text("删除此图层");
                                    self.widgets.insert(
                                        format!("layer_delete_{}", layer.id),
                                        rect_values(delete.rect),
                                    );
                                    if delete.clicked() {
                                        remove = Some(layer.id);
                                    }
                                });
                                ui.weak(format!(
                                    "{} 点 · {} 字段",
                                    layer.points.len(),
                                    layer.cloud.fields().len()
                                ));
                                ui.add_space(5.0);
                            });
                        }
                    });
                if let Some(id) = clicked {
                    self.select(id);
                }
                if let Some(id) = remove {
                    self.delete_id = Some(id);
                }
                if self.scene.layers.is_empty() {
                    ui.weak("导入或拖入 PCD 文件开始。");
                }
                ui.add_space(8.0);
                let delete = ui.add_enabled(
                    self.scene.selected.is_some(),
                    egui::Button::new("删除选中图层  Del"),
                );
                self.mark("delete_selected", &delete);
                if delete.clicked() {
                    self.delete_id = self.scene.selected;
                }
                ui.separator();
                let export = ui.add_enabled(
                    self.scene.selected.is_some() && self.pending == 0,
                    egui::Button::new("导出选中图层…"),
                );
                self.mark("export_button", &export);
                if export.clicked() {
                    if let Some(layer) = self.scene.selected_layer() {
                        self.path_action = Some(PathAction::Export(layer.id));
                        let stem = layer
                            .source
                            .file_stem()
                            .unwrap_or_default()
                            .to_string_lossy();
                        self.path_text = layer
                            .source
                            .with_file_name(format!("{stem}_edited.pcd"))
                            .to_string_lossy()
                            .into_owned();
                    }
                }
                ui.add_space(10.0);
                if let Some(layer) = self.scene.selected_layer() {
                    ui.weak("保留的 PCD 字段");
                    ui.label(
                        RichText::new(
                            layer
                                .cloud
                                .fields()
                                .iter()
                                .map(|f| f.name.as_str())
                                .collect::<Vec<_>>()
                                .join(" · "),
                        )
                        .small(),
                    );
                }
                ui.add_space(20.0);
                ui.weak(
                    "本地工作区
文件仅在此设备处理",
                );
            });
        let right = egui::SidePanel::right("processing")
            .exact_width(304.0)
            .resizable(false)
            .frame(
                egui::Frame::new()
                    .fill(theme::RIGHT_PANEL)
                    .inner_margin(10.0),
            )
            .show(ctx, |ui| {
                theme::paint_pattern(ui);
                ui.heading("点云处理");
                ui.weak("选择一种处理方式");
                let content = ui.available_rect_before_wrap();
                self.panels.insert("right".into(), rect_values(content));
                egui::ScrollArea::vertical()
                    .id_salt("tools_scroll")
                    .show(ui, |ui| {
                        let header = egui::CollapsingHeader::new("删除选中区域点云")
                            .default_open(true)
                            .show(ui, |ui| {
                                self.region_controls(ui, ctx);
                            });
                        self.mark("region_section", &header.header_response);
                        ui.separator();
                        let old_ranges = self.ranges;
                        let range_header = egui::CollapsingHeader::new("XYZ 作用范围 / 米")
                            .default_open(false)
                            .show(ui, |ui| {
                                ui.weak("限制区域选点、删除和体素滤波。");
                                egui::Grid::new("ranges")
                                    .num_columns(3)
                                    .spacing([8.0, 6.0])
                                    .show(ui, |ui| {
                                        ui.label("轴");
                                        ui.label("最小");
                                        ui.label("最大");
                                        ui.end_row();
                                        for (axis, range) in
                                            ["X", "Y", "Z"].iter().zip(self.ranges.iter_mut())
                                        {
                                            ui.label(*axis);
                                            ui.add(
                                                egui::DragValue::new(&mut range[0])
                                                    .speed(0.02)
                                                    .max_decimals(3),
                                            );
                                            ui.add(
                                                egui::DragValue::new(&mut range[1])
                                                    .speed(0.02)
                                                    .max_decimals(3),
                                            );
                                            ui.end_row();
                                        }
                                    });
                            });
                        self.mark("range_section", &range_header.header_response);
                        if self.ranges != old_ranges {
                            self.region.invalidate();
                            self.region.status = "XYZ 范围已改变，请重新计算区域。".into();
                        }
                        ui.separator();
                        let filter_header = egui::CollapsingHeader::new("体素滤波")
                            .default_open(true)
                            .show(ui, |ui| {
                                ui.weak("范围外保留，范围内每体素保留首点。");
                                ui.add_enabled_ui(
                                    self.scene.selected.is_some() && self.pending == 0,
                                    |ui| {
                                        ui.horizontal(|ui| {
                                            ui.label("体素边长 / 米");
                                            ui.add(
                                                egui::DragValue::new(&mut self.voxel)
                                                    .speed(0.005)
                                                    .range(0.001..=1000.0)
                                                    .max_decimals(3),
                                            );
                                        });
                                        let filter = ui.button("生成滤波图层");
                                        self.mark("filter_button", &filter);
                                        if filter.clicked() {
                                            self.filter(ctx);
                                        }
                                    },
                                );
                            });
                        self.mark("filter_section", &filter_header.header_response);
                        ui.separator();
                        ui.label(RichText::new("显示").strong());
                        ui.add(egui::Slider::new(&mut self.point_size, 1.0..=8.0).text("点大小"));
                        ui.weak(
                            "左键拖动：旋转 · 右键拖动：平移
滚轮：缩放 · Esc：清空选区",
                        );
                    });
            });
        // right.inner is unit; its response ensures this panel gets laid out before the viewport.
        let _ = right;
        if self.region.layer_id.is_some()
            && (self.region.layer_id != self.scene.selected
                || !self.scene.selected_layer().is_some_and(|l| l.visible))
        {
            self.region.clear();
        }
        egui::CentralPanel::default()
            .frame(egui::Frame::NONE)
            .show(ctx, |ui| {
                let rect = ui.available_rect_before_wrap();
                self.widgets.insert("viewport".into(), rect_values(rect));
                let layers = self
                    .scene
                    .layers
                    .iter()
                    .filter(|l| l.visible)
                    .map(|l| RenderLayer {
                        id: l.id,
                        points: l.points.clone(),
                        tint: [1.0, 1.0, 1.0],
                    })
                    .collect();
                let overlay = self.region.layer_id.map(|layer_id| SelectionOverlay {
                    layer_id,
                    picking: self.region.picking && self.pending == 0,
                    picks: self.region.picks.clone(),
                    ranges: self.ranges,
                    hull_edges: self
                        .region
                        .hull
                        .as_ref()
                        .map(|h| {
                            h.triangles
                                .iter()
                                .flat_map(|t| {
                                    [
                                        [h.vertices[t[0]], h.vertices[t[1]]],
                                        [h.vertices[t[1]], h.vertices[t[2]]],
                                        [h.vertices[t[2]], h.vertices[t[0]]],
                                    ]
                                })
                                .collect()
                        })
                        .unwrap_or_default(),
                });
                if let Some(point) = self.viewport.show(ui, layers, self.point_size, overlay) {
                    if self.region.picks.contains(&point) {
                        self.region.status = "该点已选择，请选择其他边界点。".into();
                    } else {
                        self.region.picks.push(point);
                        self.region.invalidate();
                        self.region.status = format!(
                            "已选择 {} 个点；选好后计算凸包区域。",
                            self.region.picks.len()
                        );
                    }
                }
                if self.telemetry.is_some() {
                    self.projected_candidates = self
                        .viewport
                        .project_points(rect, &self.qa_candidates)
                        .into_iter()
                        .flatten()
                        .map(|p| [p.x, p.y])
                        .collect();
                }
            });
        self.path_modal(ctx);
        self.delete_modal(ctx);
        if let Some(error) = self.error.clone() {
            let mut close = false;
            egui::Modal::new(egui::Id::new("error")).show(ctx, |ui| {
                ui.set_width(480.0);
                ui.heading("无法完成操作");
                ui.label(error);
                let response = ui.button("确定");
                self.mark("error_close", &response);
                close = response.clicked();
            });
            if close {
                self.error = None;
            }
        }
        self.telemetry(ctx);
        if self.pending > 0 {
            ctx.request_repaint_after(Duration::from_millis(50));
        }
    }

    fn on_exit(&mut self, gl: Option<&eframe::glow::Context>) {
        if let Some(gl) = gl {
            self.viewport.destroy(gl);
        }
        for job in self.jobs.drain(..) {
            let _ = job.join();
        }
    }
}

fn rect_values(rect: egui::Rect) -> [f32; 4] {
    [rect.min.x, rect.min.y, rect.width(), rect.height()]
}

fn main() -> eframe::Result {
    let mut paths = Vec::new();
    for arg in std::env::args_os().skip(1) {
        if arg == "--help" || arg == "-h" {
            println!("Taffy PCD Editor · Rust\n用法: taffy-pcd-editor [文件.pcd ...]\n无参数打开 GUI；支持导入、图层显隐/删除、凸包区域删除、体素滤波和字段完整导出。");
            return Ok(());
        }
        paths.push(PathBuf::from(arg));
    }
    let icon = eframe::icon_data::from_png_bytes(include_bytes!("../assets/icon.png"))
        .expect("valid embedded icon");
    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_inner_size([1280.0, 820.0])
            .with_min_inner_size([1000.0, 740.0])
            .with_icon(icon),
        renderer: eframe::Renderer::Glow,
        depth_buffer: 24,
        ..Default::default()
    };
    eframe::run_native(
        TITLE,
        options,
        Box::new(move |cc| {
            Ok(Box::new(
                Editor::new(cc, paths).map_err(std::io::Error::other)?,
            ))
        }),
    )
}

#[cfg(test)]
mod editor_state_tests {
    use super::*;

    #[test]
    fn changed_ranges_invalidate_preview_and_running_request_even_for_same_layer() {
        let small = [[0.0, 0.5]; 3];
        let full = [[0.0, 1.0]; 3];
        let mut state = RegionEdit {
            layer_id: Some(7),
            count: Some(10),
            computing: true,
            picks: vec![[0.0, 0.0, 0.0]],
            ..Default::default()
        };
        let request_revision = state.revision;
        state.ranges_changed(small, small);
        assert_eq!(state.count, Some(10));
        assert_eq!(state.revision, request_revision);
        state.ranges_changed(small, full);
        assert_eq!(state.layer_id, Some(7));
        assert_eq!(state.picks.len(), 1);
        assert!(state.count.is_none());
        assert!(!state.computing);
        assert_ne!(state.revision, request_revision);
    }
}
