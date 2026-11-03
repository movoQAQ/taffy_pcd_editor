//! Original Taffy colors and background ornaments, ported from the release GUI.
//! See assets/ORIGINAL-GUI.md for bytecode/source attribution.

use eframe::egui::{self, Color32, Stroke};

pub const HEADER: Color32 = Color32::from_rgb(255, 245, 251);
pub const SIDEBAR: Color32 = Color32::from_rgb(251, 248, 255);
pub const RIGHT_PANEL: Color32 = Color32::from_rgb(251, 250, 255);
pub const TOOLBAR: Color32 = Color32::from_rgb(255, 250, 253);
pub const BRAND: Color32 = Color32::from_rgb(167, 61, 112);
pub const SECTION: Color32 = Color32::from_rgb(106, 77, 109);
pub const MUTED: Color32 = Color32::from_rgb(146, 132, 146);
pub const ACCENT: Color32 = Color32::from_rgb(217, 97, 150);
pub const PRIMARY: Color32 = Color32::from_rgb(248, 220, 233);
pub const BORDER: Color32 = Color32::from_rgb(234, 221, 235);

pub fn configure(ctx: &egui::Context) {
    let mut fonts = egui::FontDefinitions::default();
    for path in [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    ] {
        if let Ok(data) = std::fs::read(path) {
            fonts
                .font_data
                .insert("chinese".into(), egui::FontData::from_owned(data).into());
            fonts
                .families
                .get_mut(&egui::FontFamily::Proportional)
                .unwrap()
                .push("chinese".into());
            break;
        }
    }
    ctx.set_fonts(fonts);
    ctx.set_theme(egui::Theme::Light);
    let mut style = (*ctx.style()).clone();
    let mut visuals = egui::Visuals::light();
    visuals.panel_fill = TOOLBAR;
    visuals.window_fill = Color32::from_rgb(255, 248, 253);
    visuals.window_stroke = Stroke::new(1.0_f32, BORDER);
    visuals.window_corner_radius = 12.into();
    visuals.menu_corner_radius = 8.into();
    visuals.weak_text_color = Some(MUTED);
    visuals.hyperlink_color = BRAND;
    visuals.faint_bg_color = Color32::from_rgb(252, 233, 243);
    visuals.extreme_bg_color = Color32::from_rgb(255, 254, 254);
    visuals.text_edit_bg_color = Some(Color32::from_rgb(255, 254, 254));
    visuals.code_bg_color = HEADER;
    visuals.selection.bg_fill = PRIMARY;
    visuals.selection.stroke = Stroke::new(1.0_f32, BRAND);
    visuals.widgets.noninteractive.bg_stroke = Stroke::new(1.0_f32, BORDER);
    visuals.widgets.noninteractive.fg_stroke =
        Stroke::new(1.0_f32, Color32::from_rgb(115, 93, 114));
    visuals.widgets.inactive.bg_fill = Color32::from_rgb(234, 223, 234);
    visuals.widgets.inactive.weak_bg_fill = Color32::from_rgb(255, 254, 254);
    visuals.widgets.inactive.bg_stroke = Stroke::new(1.0_f32, Color32::from_rgb(234, 221, 232));
    visuals.widgets.inactive.fg_stroke = Stroke::new(1.0_f32, SECTION);
    visuals.widgets.inactive.corner_radius = 8.into();
    visuals.widgets.hovered.bg_fill = Color32::from_rgb(255, 240, 247);
    visuals.widgets.hovered.weak_bg_fill = Color32::from_rgb(255, 240, 247);
    visuals.widgets.hovered.bg_stroke = Stroke::new(1.0_f32, Color32::from_rgb(228, 169, 200));
    visuals.widgets.hovered.fg_stroke = Stroke::new(1.5_f32, BRAND);
    visuals.widgets.hovered.corner_radius = 8.into();
    visuals.widgets.active.bg_fill = PRIMARY;
    visuals.widgets.active.weak_bg_fill = PRIMARY;
    visuals.widgets.active.bg_stroke = Stroke::new(1.0_f32, ACCENT);
    visuals.widgets.active.fg_stroke = Stroke::new(1.5_f32, Color32::from_rgb(127, 49, 89));
    visuals.widgets.active.corner_radius = 8.into();
    visuals.widgets.open = visuals.widgets.active;
    visuals.error_fg_color = Color32::from_rgb(165, 51, 103);
    style.visuals = visuals;
    style.spacing.item_spacing = egui::vec2(8.0, 7.0);
    style.spacing.button_padding = egui::vec2(10.0, 7.0);
    for text_style in [egui::TextStyle::Body, egui::TextStyle::Button] {
        style
            .text_styles
            .insert(text_style, egui::FontId::proportional(14.0));
    }
    style
        .text_styles
        .insert(egui::TextStyle::Small, egui::FontId::proportional(11.0));
    style
        .text_styles
        .insert(egui::TextStyle::Heading, egui::FontId::proportional(18.0));
    ctx.set_style(style);
}

/// Draw before the panel's controls so opaque controls cover the decoration.
/// This translates the release's TaffyPatternFrame.paintEvent coordinates;
/// the original pattern was procedural, not an image asset.
pub fn paint_pattern(ui: &egui::Ui) {
    let rect = ui.max_rect().intersect(ui.clip_rect());
    if !rect.is_finite() || rect.is_negative() {
        return;
    }
    let painter = ui.painter().with_clip_rect(rect);
    let stroke = Stroke::new(1.2_f32, Color32::from_rgba_unmultiplied(217, 97, 150, 28));
    let mut row = 0;
    let mut y = rect.top() + 22.0;
    while y < rect.bottom() + 55.0 {
        let offset = if row % 2 == 1 { 16.0 } else { 58.0 };
        let mut x = rect.left() + offset;
        while x < rect.right() + 55.0 {
            let p = |dx, dy| egui::pos2(x + dx, y + dy);
            painter.add(egui::Shape::ellipse_stroke(
                p(6.0, 12.0),
                egui::vec2(6.0, 5.0),
                stroke,
            ));
            painter.add(egui::Shape::line(
                vec![p(1.0, 9.0), p(4.0, 0.0), p(7.0, 8.0)],
                stroke,
            ));
            painter.add(egui::Shape::line(
                vec![p(6.0, 8.0), p(10.0, 0.0), p(12.0, 9.0)],
                stroke,
            ));
            painter.line_segment([p(22.0, 7.0), p(28.0, 7.0)], stroke);
            painter.line_segment([p(25.0, 4.0), p(25.0, 10.0)], stroke);
            painter.circle_stroke(p(44.5, 5.5), 1.5, stroke);
            x += 94.0;
        }
        row += 1;
        y += 72.0;
    }
}
