# 原版 GUI 素材来源

- `icon.png`：逐字节复用 `taffy_pcd_editor/original/assets/tafei-pcd-editor.png`，用于窗口图标及 GUI 顶部品牌图。
- `original-style.qss`：直接从原版 `original/main.pyc` 顶层常量提取的完整 QSS，作为 Rust 主题的颜色和形状来源；Rust 运行不加载 QSS，也不依赖 Python。
- `../src/theme.rs`：按照上述 QSS 适配 egui 主题；背景猫耳、十字星和小圆环逐项移植自 `TaffyPatternFrame.paintEvent`（原始文件 `/opt/taffy-editor/main.py` 的第 352–366 行，已核对 Python 3.10 字节码）。它们是原版绘图代码，不是图片文件或 AI 生成素材。
- 原版界面参照：`taffy_pcd_editor/analysis/ui/rmuc-original-window.png`。原版的左侧图层、右侧处理工具和粉色浅色主题用于 Rust GUI 布局。

SHA-256：

```text
icon.png  689a900adadbf65bd9b5ebfc3d80d34f6d85a0ecc2720e41960d3bb486f6df9c
original/main.pyc  f41ae9fda78b95f1a2e4cd4a835c5c3b19ccef331916478f805aa901cf1314a9
original-style.qss  d39e1e2ede25400133f40eb14e80f896ae74dfb4ac81e5e7025182e0de268636
```

上游原有说明见 `UPSTREAM-README.md`。这些记录只说明素材来源，不声明上游未授予的许可。原版来源不随 Rust 窗口改写而改变。

原 Python 目录已从当前主版本移除；上述原始文件及参考截图可在 [历史提交 7931863](https://github.com/movoQAQ/taffy_pcd_editor/tree/7931863d52f222c5ef7bb191f576426a473d0297) 中核验。
