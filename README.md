# Taffy PCD 编辑器：源码恢复与本机运行

基于 [taffy-editor v1.2 发布包](https://github.com/LYJX-robotic-CC/taffy-editor/releases/tag/v1.2) 恢复。当前已恢复 9 个核心函数和 2 个 Qt 滑块类，并完成本机 Qt/VTK UI 验证。主窗口和后台线程仍使用原始 Python 3.10 字节码，尚不能仅凭恢复源码运行。

## 统一启动

```bash
./start.sh              # 默认启动恢复代码集成版
./start.sh --original   # 原始 release 对照版
./start.sh --help
```

也可以从任意目录执行 `/path/to/taffy_pcd_editor/start.sh`。脚本会定位项目目录，首次缺少 `.venv` 时自动执行 `tools/setup-local.sh` 安装本机依赖；已有环境可直接启动。需要联网安装时正常下载，不使用 Docker，也不需要安装 deb。

需要 Linux 图形桌面及 X11 `DISPLAY`。默认软件渲染，可用 `LIBGL_ALWAYS_SOFTWARE=0 ./start.sh` 尝试硬件渲染。安装和运行不修改系统 Python 或 ROS：独立 Python 3.10 由 uv 管理，项目依赖位于 `.venv`；没有系统 uv 时，在 `.bootstrap` 安装备用 uv。

本机验证环境：Ubuntu 24.04、Python 3.10.22、PyQt5 5.15.11、VTK 9.3.1、Open3D 0.19.0。依赖固定在 `tools/requirements-runtime.txt`。`.venv` 约 2.2 GB，`.bootstrap` 约 53 MB，均不提交到 Git。需要重新安装依赖时执行 `./tools/setup-local.sh`。

启动使用 `python -E -s`，忽略外部 `PYTHONPATH` 和用户包；测试额外关闭第三方 pytest 插件自动加载，避免当前 ROS Jazzy 的 Python 3.12 包干扰 Python 3.10。这些设置只作用于本次子进程。

## 项目目录

| 路径 | 用途 |
| --- | --- |
| `start.sh` | 唯一应用启动脚本 |
| `recovered/source/` | 已恢复、经对照测试的核心函数和 Qt 控件 |
| `original/main.pyc`、`original/assets/` | 目前必需的原始主窗口、后台线程及图标 |
| `original/UPSTREAM-README.md` | 上游说明和权利归属 |
| `tools/` | 本机安装、集成加载、测试和源码恢复工具 |
| `tests/` | 原版对照、控件和真实桌面工作流测试 |
| `analysis/`、`recovered/depyf/` | 保留的反汇编、对象索引、待审查反编译文本和 UI 证据 |

旧 `docker/`、Docker 构建/恢复脚本、deb 安装布局、重复图标、失败的整文件反编译及可重新生成的逐对象字节码/旧碎片已经清理。原始运行文件已移到 `original/`，不再保留 `rootfs/` 下的系统安装目录层级。旧材料仍可从 Git 历史取回。

`recovered/depyf/` 是分析材料，不能直接当作可运行源码；完整反汇编和已核对的函数反汇编继续保留，便于恢复剩余主窗口。具体索引见 `analysis/INDEX.md`。

## 测试

```bash
./tools/test-runtime.sh
TAFFY_TEST_PCD=/path/to/map.pcd ./tools/test-runtime.sh
# 将新截图/报告写到仓库外：
TAFFY_TEST_PCD=/path/to/map.pcd TAFFY_UI_ARTIFACT_DIR=/tmp/taffy-ui ./tools/test-runtime.sh
```

测试入口运行 44 项核心/控件测试和 2 项示例 UI 工作流；设置 `TAFFY_TEST_PCD` 后增加原版、恢复版各 1 项真实点云工作流，共 48 项。UI 测试需要桌面显示。导出文件写入 pytest 临时目录，原始点云只读并检查 SHA-256。

2026-11-03 已通过完整 48 项测试；随后三轮 RMUC 工作流共 6 项也通过。清理目录后再次运行完整入口，48 项全部通过；从项目外调用 `start.sh` 的原版和恢复版均通过 7 秒启动存活检查。测试窗口退出现在等待全部后台线程结束并释放 Qt 对象，覆盖原先 `_editing_busy()` 不等待可见点数统计线程的清理缺口。

真实数据为 `RMUC2027_V1.0.0.pcd`，1,000,000 点，含 XYZ 和法线。两版均渲染全部百万点；范围内 5 cm 体素滤波后总点数均为 636,669，范围外点保持不变。区域删除 292 点、补全 999 点，导出并回读 1,000,707 点。原始文件 SHA-256 始终为 `3d738c081b66c2a9aca02b551125bd6d2d84efc8053164662c3ead8e725eaa17`。

UI 验证包括导入与后台完整载入、VTK 渲染、范围滑块、网格/投影/俯视、图层显隐、滤波及筛空保护、视口双击选点、凸包、删除、补全、导出回读和退出。文件对话框使用测试路径；区域编辑使用确定顶点，按钮和后台线程实际执行。截图和报告见 `analysis/ui/`。单次测试时间不代表帧率或长期性能保证。

## 恢复范围与限制

- `core.py`：`fmt_number`、`make_demo_cloud`、`load_pcd_data`、`load_full_xyz`、`range_mask`、`available_memory_bytes`、`complete_region`、`points_inside_region`、`write_full_pcd`。
- `widgets.py`：`HeightRangeSlider`、`DragOnlySlider`。源码自身没有字节码加载或回退，集成关系位于 `tools/run_editor.py`。
- 编辑导出延续 release 行为，仅写 XYZ，不保留法线或其他字段；原文件复制路径保留全部字节。
- 默认半径滤波参数（5 cm 内至少 20 点）可能筛空稀疏点云，程序提示并保留输入，参数应匹配点密度。
- 原始主窗口底部高度文字仍可能显示初始范围，与实际范围滑块不一致，尚未修复。
- 早前出现过一次 RMUC 集成版导入等待超时，状态文字已显示完整载入。后续完整及连续测试均通过；已补充图层/请求/线程诊断，尚未确认根因。窗口清理改进不能视为此问题已修复。
- 尚未验证长时间运行、全部硬件/高 DPI 配置及更大数据。

## Rust 点云核心原型

`rust/` 是独立的点云处理库和命令行工具，使用 Rust 标准库，无第三方 crate。现有 `start.sh` 仍启动 Python/Qt 编辑器；本轮没有把 GUI、点选、统计/半径滤波或补点迁移到 Rust。

```bash
cargo build --offline --release --manifest-path rust/Cargo.toml
rust/target/release/taffy-pcd-core /path/to/map.pcd --voxel 0.05 --output /tmp/filtered.pcd
# 只对范围内做体素滤波，范围外全部保留：
rust/target/release/taffy-pcd-core /path/to/map.pcd --voxel 0.05 --bounds -5 5 -10 10 0 3 --output /tmp/filtered-range.pcd
```

输出文件必须不存在，命令不会覆盖输入或已有输出。支持 binary PCD、任意字段排列和 COUNT，XYZ 必须为单值 F4/F8；坐标按 float32 处理，与当前编辑器一致。每个体素保留输入中的第一个点，按“范围外原序 + 范围内保留点原序”输出；法线、强度等额外字段随整条记录逐字节保留，VIEWPOINT 保留。编辑后 WIDTH/HEIGHT 改为非组织点云布局。ASCII、压缩 PCD、非有限 XYZ、无法表示为 float32 的坐标及越界体素编号会明确报错。

```bash
cargo test --offline --manifest-path rust/Cargo.toml
cargo clippy --offline --manifest-path rust/Cargo.toml --all-targets -- -D warnings
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -B -E -s -m pytest -q -p no:cacheprovider tests/test_rust_core.py
.venv/bin/python -B -E -s tools/benchmark-rust.py /path/to/map.pcd --repeats 5 --output /tmp/taffy-rust-benchmark.json
```

基准分别启动 Rust、现有编辑器后台处理、仅 NumPy 三种独立进程；每种预热一次，再顺序轮换测量五次，报告中位数和全部原始样本。读取计时包含完整 XYZ 的有限性检查与边界扫描，避免把 Python 内存映射的延迟读入漏计。计算阶段和包含依赖导入的进程总耗时分开记录，峰值 RSS 用 GNU time 采集；正确性比较在计时外完成，并检查原文件 SHA-256 未改变。

这是热文件缓存、单一百万点地图的 CPU 核心测试，不是完整 GUI 的内存或帧率测试。体素部分还包含从 NumPy 排序去重换为 Rust 哈希表首点选择的算法变化，结果不能归因于语言本身。原型可执行文件仅含核心逻辑，不能拿其大小当作完整编辑器的体积。

2026-11-03，在本机 Ryzen 7 H 255 上使用 RMUC 百万点地图，5 cm 体素、X 范围下界移至全长 20%，五轮中位数如下：

| 实现 | 读取并扫描 | 范围内体素筛选 | 两阶段合计 | 整进程峰值 RSS |
| --- | ---: | ---: | ---: | ---: |
| Rust 核心 | 24.1 ms | 144.4 ms | 169.7 ms | 42.7 MiB |
| 现有编辑器后台计算 | 58.5 ms | 574.7 ms | 632.4 ms | 576.9 MiB |
| 仅 NumPy 对照 | 61.1 ms | 563.9 ms | 624.8 ms | 121.0 MiB |

Rust 筛选单次耗时范围为 108.1–252.1 ms，存在波动；没有选择性剔除样本。峰值 RSS 包含依赖导入、处理和轻量校验，Python 后台进程加载了 Qt/VTK/Open3D，Rust 与 NumPy 输出索引而编辑器后台还会物化 XYZ 数组。

本次范围内有 795,134 点，输出 635,298 点。与独立 NumPy 参考逐完整记录相同，现有后台流程的 XYZ 摘要也相同，原始 RMUC SHA-256 未变。使用的是固定数值范围，与早前 UI 点击测试范围不同。release 可执行文件为 473,064 字节（约 462 KiB），仍依赖系统 libc/libgcc，不包含 GUI。原始测量与方法见 [RMUC 基准 JSON](analysis/rust/rmuc-benchmark.json)。

## 来源与校验

原始 deb SHA-256：`939b5d0fee7f89ebefe750ace0310acdf54b89704c18332c941ff80ed352b14b`。

`original/main.pyc` SHA-256：`f41ae9fda78b95f1a2e4cd4a835c5c3b19ccef331916478f805aa901cf1314a9`，清理目录没有改变其字节。

原包及恢复结果保留上游权利归属；本仓库不是上游原始源码，未为上游内容添加新的开源授权。
