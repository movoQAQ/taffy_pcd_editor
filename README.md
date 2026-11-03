# Taffy PCD Editor · Rust

原生 Rust 点云编辑器，采用 egui / eframe + OpenGL。仓库主版本已从 Python 字节码恢复工程迁移到 Rust；运行 GUI 无需 Python、ROS、Docker 或 deb。原版图标、粉色主题、猫耳底纹和左右工具栏布局已复用，素材来源见 [assets/ORIGINAL-GUI.md](assets/ORIGINAL-GUI.md)。

## 启动

```bash
./start.sh
# 启动时载入点云，可传入多个文件：
./start.sh /path/to/map.pcd
```

`start.sh` 可从任意目录执行；已有根目录二进制时直接打开 GUI，首次缺少二进制时调用 `build.sh`。源码更新后运行 `./build.sh`，生成可直接执行的 `./taffy-pcd-editor`。编译产物不提交到 Git。

本机独立工作空间：`/home/lyu/taffy_pcd_editor_rust`；原仓库目录 `/home/lyu/taffy_pcd_editor` 同样替换为 Rust 版。`taffy-pcd-editor.code-workspace` 可供代码编辑器打开，`Taffy-Rust.desktop` 是指向本机独立工作空间的快捷方式；移动目录时需调整其中 Exec、Icon 和 Path。

## 区域点云删除

1. 导入并选中可见图层，在右侧点击 **开始选点区域**。
2. 在点云上**双击**选择至少 4 个不同边界点；左键拖动可旋转视角，右键拖动平移，滚轮缩放。支持撤销最后一个选点、清空选点以及 Esc 清空选区。
3. 设置 **XYZ 外扩 / 厘米**，点击 **计算凸包区域**，查看编号选点、凸包边线和命中点数。
4. 点击 **删除区域点**。结果成为新的编辑图层，原图层隐藏并保留，可重新显示对照。
5. 选中结果图层，点击 **导出选中图层**，写入一个新的 PCD 文件。

几何语义沿用原版：对每个边界点加入 XYZ 各方向的八角偏移，再计算三维凸包。外扩为 0 时不能全部共面；正外扩可使平面上的选点形成体积。删除范围是凸包与当前 **XYZ 作用范围** 的交集，区域外点保持原序。完全覆盖图层时会拒绝删除，至少保留一个点。

范围、外扩或选点改变后需要重新计算；切换、隐藏或移除目标图层会清除旧选区。后台任务检查来源图层和预览版本，迟到结果不会恢复已删除图层。法线、强度及其他字段随剩余原始记录逐字节保留，不重新估算法线。

## 其他操作

- 导入支持粘贴路径、原生文件选择器和拖入文件。
- 图层复选框控制显隐；行尾 ×、「删除选中图层」或 Delete 移除整个场景图层，不删除磁盘 PCD。
- F /「适配视图」显示全部可见图层；「俯视」切换顶视角。
- 体素滤波在 XYZ 范围内每个体素保留第一个点，范围外全部保留；结果成为新图层。连续滤波和区域删除只处理当前图层剩余的点。
- 导出保留所有选中点的原始字段、COUNT 和 VIEWPOINT，输出 HEIGHT=1 的非组织点云；不会覆盖已有文件或源文件。

读取、凸包计数、删除、滤波与导出在后台运行。已启动的导出完成其快照；关闭窗口时等待已启动的数据任务结束。

## 构建与测试

本机已配置 Rust stable 和 Linux 图形依赖。运行需图形桌面、OpenGL 3.3，以及 Noto Sans CJK 或 Droid Sans Fallback 中文字体。

```bash
./build.sh
cargo test --locked --workspace
cargo clippy --locked --workspace --all-targets -- -D warnings
cargo fmt --all -- --check
```

首次构建联网下载 crates；`Cargo.lock` 固定依赖，之后可加 `--offline`。其他 Linux 机器如缺编译依赖，可安装 `build-essential pkg-config libx11-dev libxkbcommon-dev libwayland-dev libgl1-mesa-dev fonts-noto-cjk`。

独立验证脚本使用 Python，仅作为开发测试工具，不参与 GUI 运行。测试环境需要 NumPy、SciPy；桌面回归另需 PyQt5、Pillow 和 X11/XTest：

```bash
python3 -B -E -s tests/region_differential.py
python3 -B -E -s tests/ui_region.py --pcd /path/to/map.pcd --output-dir /tmp/taffy-region-ui
python3 -B -E -s tests/ui_smoke.py --pcd /path/to/map.pcd --output-dir /tmp/taffy-smoke-ui
```

`TAFFY_UI_STATE` 仅在测试时启用只读状态和控件坐标；测试通过真实鼠标键盘完成操作，SciPy 独立计算凸包删除结果，NumPy 独立计算体素滤波结果，并核对导出的全部记录和源文件哈希。测试结果与地图不提交到 Git。

本机验证（2026-11-03）：45 项 Rust 测试、Clippy 与格式检查通过；240 组凸包案例、466,033 次点包含判断与 SciPy 一致。使用 `RMUC2027_V1.0.0.pcd` 的 100 万点地图完成真实 GUI 选区删除：删除 112,724 点，剩余 887,276 点，导出包含 `normal_x/y/z` 的所有原始记录与独立参考逐字节一致，源文件哈希不变。

## 支持范围与历史

支持 `DATA binary` PCD；XYZ 为单值 F4/F8，编辑坐标按 float32 计算。ASCII、binary_compressed、非有限或不能表示为 float32 的 XYZ 会明确报错。区域补点、统计离群点和半径滤波尚未迁移。

Python 源码恢复版保留在 Git 历史提交 [`7931863`](https://github.com/movoQAQ/taffy_pcd_editor/tree/7931863d52f222c5ef7bb191f576426a473d0297)，当前目录不需要原版字节码、虚拟环境或 Python 运行模块。Rust 核心最初由该提交中的 `rust/` 独立原型迁入。上游素材来自 [taffy-editor v1.2](https://github.com/LYJX-robotic-CC/taffy-editor/releases/tag/v1.2)，原有说明见 `assets/UPSTREAM-README.md`；本仓库没有为原素材重新声明许可。
