# taffy-editor v1.2 源码恢复与 UI 验证

来源：https://github.com/LYJX-robotic-CC/taffy-editor/releases/tag/v1.2

本仓库从发布包中的 Python 3.10 字节码恢复源码，不是上游原始源码。当前已恢复 9 个核心函数和 2 个 Qt 滑块类，并接入原始主窗口完成本机 UI 验证；完整编辑器仍依赖原包 `main.pyc`，尚不能仅凭恢复源码运行。

## 本机运行（不需要 Docker）

在仓库根目录执行：

```bash
./tools/setup-local.sh        # 下载独立 Python 3.10，在 .venv 安装依赖
./tools/run-app.sh            # 恢复代码集成版，仍使用原始 UI 主窗口
./tools/run-app.sh --original # release 原始版本，对照使用
./tools/test-runtime.sh       # 44 项源码/控件测试 + 2 项桌面工作流
TAFFY_TEST_PCD=/home/lyu/下载/RMUC2027_V1.0.0.pcd ./tools/test-runtime.sh
```

没有 uv 时，安装脚本在仓库 `.bootstrap` 内安装 uv，由 uv 管理用户目录中的 Python 3.10；不修改系统 Python 或 ROS。依赖版本见 `tools/requirements-runtime.txt`。本次实际环境为 Ubuntu 24.04、Python 3.10.22、PyQt5 5.15.11、VTK 9.3.1、Open3D 0.19.0，虚拟环境约占 2.2 GB。

启动及 UI 测试需要 X11 `DISPLAY`，沿用当前桌面认证，默认软件渲染，不放宽 X server 权限。ROS Jazzy 的 `PYTHONPATH` 会带入 Python 3.12 测试插件，因此启动器使用 `python -E -s` 忽略外部 Python 环境变量和用户包，测试脚本同时关闭第三方 pytest 插件自动加载。这些设置仅作用于子进程。

## 第三轮恢复与桌面验证（2026-11-03）

- `recovered/source/core.py`：新增 `make_demo_cloud`、`load_pcd_data`、`load_full_xyz`、`complete_region`。恢复 binary PCD 多字段/COUNT/内存映射、ASCII 和压缩 PCD 回退、渲染抽样、完整点云读取和区域随机补全的控制流。
- `recovered/source/widgets.py`：恢复 `HeightRangeSlider` 和 `DragOnlySlider` 的信号、默认参数、绘制、鼠标和键盘事件。按字节码修正自动反编译文本中的错误分支，保留 release 行为。
- `tools/run_editor.py`：把上述源码函数和类接入原始模块。两个源码文件自身没有字节码加载或回退；主窗口及后台工作线程仍来自原包。
- `analysis/round3-python310-disassembly.txt`：这轮恢复对象的 Python 3.10 原生反汇编证据。

44 项源码/控件测试、2 项示例桌面工作流、2 项 RMUC 桌面工作流全部通过，共 48 项。源码测试覆盖 1,500,001 点读取、不同字段排列/数组步长、ASCII/压缩 PCD、异常输入、固定随机输入下 250,000 点补全，以及两种方向滑块的事件/信号/绘制像素一致性。测试在本机运行，没有禁网沙箱，不依赖 Docker。

示例 UI 验证覆盖导入按钮与后台完整载入、VTK 渲染、范围滑块和重置、网格/投影/俯视、图层显隐、滤波成功和筛空保护、视口双击选点、凸包预览、删除、补全、导出回读及正常退出。文件对话框返回临时路径；删除/补全使用确定的顶点输入，按钮和后台线程实际执行。截图通过原生窗口抓取；`QWidget.grab()` 无法正确抓取本机 VTK OpenGL 子窗口。

真实数据为 `/home/lyu/下载/RMUC2027_V1.0.0.pcd`，24,000,221 字节，1,000,000 点，含 XYZ 和法线。两版均渲染全部 1,000,000 点；一次本机软件渲染记录中导入约 1.5–1.7 秒，范围内 5 cm 体素滤波约 0.9 秒。两版的范围内点数均为 792,514，滤波后总点数为 636,669；区域删除 292 点、补全 999 点，导出并回读 1,000,707 点。时间是单次测试记录，不是帧率或性能保证。导出写入临时文件，输入 SHA-256 前后一致：`3d738c081b66c2a9aca02b551125bd6d2d84efc8053164662c3ead8e725eaa17`。

截图及结果在 `analysis/ui/`：`rmuc-recovered-window.png`、`rmuc-original-window.png` 和 `rmuc-*-report.json`；示例数据记录为 `original-*` 与 `recovered-*`。

当前限制：

- 完整 GUI 和后台线程尚未恢复为源码；下一步重点是载入/滤波/删除工作类及主窗口。
- 编辑导出延续原版行为，仅写 XYZ，不保留法线或其他字段；原文件复制路径可以保留全部字节。
- 默认半径滤波参数（5 cm 内至少 20 点）会筛空稀疏示例点云，程序会提示并保留输入；参数需要匹配实际点密度。
- RMUC 截图底部“显示高度区间”仍显示初始值 −1.2～8.4 m，与顶部和轴滑块的实际 0.0～3.8 m 不一致；本轮未改动该原版主窗口显示问题。
- 未验证长时间运行、所有错误对话框、全部硬件/高 DPI 配置及超出本轮规模的数据。
- 重复执行完整测试入口时，RMUC 集成版曾出现一次自动化等待导入超时（状态文字已显示完整载入）；随后两版实测均重新通过。根因尚未确认，测试已增加图层和后台线程状态诊断，因此不能据一次通过认定 UI 长期稳定。

2026-11-03 另对本机 `/home/lyu/bit` 做只读兼容性核查：GICP 的 `gicp_ros_interface.cpp:407` 按 `pcl::PointXYZ` 读取 PCD，`gicp_filter.cpp:135–137` 从点位置自行计算协方差；`pcd2pgm`、`pcd2ele` 也按 XYZ 读取。因此这些入口不需要 PCD 自带法线。Point-LIO 的 `common_lib.h:168` 从邻域 XYZ 拟合平面；其仿真配置关闭先验 PCD。当前 RMUC 2027 的 `worlds.yaml` 也关闭 ICP，此结论不代表已将导出地图接入导航运行。ROGMap 使用 XYZI，是否启用强度阈值需要另行按配置判断；法线字段不参与其占据更新。

## 历史静态分析环境

Ubuntu 24.04 Docker 镜像已成功构建，标签 `taffy-recovery:ubuntu24.04`。Dockerfile 固定基础镜像摘要，pycdc 固定提交 `b4289760970dbc399684f1e155ec6d1ea1cc787e`。使用 HTTPS、CA 信任和 apt 签名校验安装分析工具。静态分析镜像不含应用运行依赖。另有 `taffy-runtime:ubuntu24.04` 运行镜像，独立安装 Python 3.10 与 PyQt5、NumPy、SciPy、VTK、Open3D，避免与 Ubuntu 24.04 默认 Python 3.12 的字节码不兼容。

## 恢复结果

- `original/`：deb 中提取的原始文件、包元数据和上游说明。
- `analysis/main.disassembly.txt`：成功静态反汇编，23,934 行。
- `recovered/main.py`：整文件反编译的截断输出（工具退出 139），不可作为完整程序。
- `recovered/fragments/`：196 个代码对象的独立反编译输出。181 个退出 0，8 个退出 1，7 个崩溃；退出 0 不保证结果完整或正确，必须结合 stderr 和字节码审阅。
- `analysis/INDEX.md`：对象名称、原始行号、输出和诊断索引。碎片通常是函数体，不能直接拼接成源码；函数签名、默认参数、装饰器和闭包等仍需人工恢复。
- `analysis/code-objects/`：由 xdis 静态拆分的 Python 3.10 代码对象。

原 deb SHA-256：`939b5d0fee7f89ebefe750ace0310acdf54b89704c18332c941ff80ed352b14b`。

## 复现

在仓库根目录执行 `tools/build-image.sh` 构建镜像，然后 `tools/recover.sh` 重做整文件静态分析。构建要求 Docker、Git 和 `/etc/ssl/certs/ca-certificates.crt` 信任包；构建上下文临时下载固定版本的 pycdc。

拆分需要 Python 虚拟环境中安装 `xdis==6.1.8`，然后运行 `python tools/split-bytecode.py`。该脚本只解析字节码，不导入目标模块，并包含该版本 Unicode marshal 写出兼容处理。逐对象恢复命令见 `tools/recover-fragments.sh`。

原包与恢复结果保留上游权利归属；本仓库未为上游内容添加新的开源授权。上游说明见 `original/UPSTREAM-README.md`。

## 第一轮原始字节码运行与非 UI 测试（历史记录）

运行对象是 `original/rootfs/opt/taffy-editor/main.pyc`，不是不完整的 `recovered/main.py`。运行镜像基于 Ubuntu 24.04，使用独立 Python 3.10，不修改系统 Python。已补齐 Qt xcb 插件依赖和中文字体。

当时在容器中执行测试并通过 Xvfb 检查启动，未验证真实桌面。当前 `run-app.sh`、`test-runtime.sh` 已改为上方的本机虚拟环境流程；Dockerfile 和静态分析脚本保留用于历史复现。

2026-11-01 验证结果：7 项 pytest 测试全部通过（3.87 秒）；覆盖数字格式化、百万点范围筛选分块边界、凸包/可视范围筛选、空/小/百万点二进制 PCD 读写往返和原文件复制。Xvfb 启动检查成功，5 秒内 51 次定时回调，正常退出。测试过程禁网。

第一轮结果仅覆盖原字节码的非 UI 行为和启动；当前桌面验证见第三轮记录。

## 第二轮源码恢复（2026-11-02）

使用 Python 3.10 + depyf 0.20.0 重新处理全部 196 个代码对象。结果见 `analysis/depyf-status.json`：101 个输出可通过 Python `compile`，95 个反编译或编译失败。`recovered/depyf/` 保存原始工具输出，包括失败输出，仅供审查；不代表 101 个函数已行为等价。默认参数、闭包、类作用域和异常处理仍可能错误。

`recovered/source/core.py` 是可独立导入的部分恢复源码，无字节码加载或回退，包含 5 个函数：`fmt_number`、`range_mask`、`points_inside_region`、`available_memory_bytes`、`write_full_pcd`。前三项基于 depyf 输出并恢复默认参数；后两项依据原始指令人工重建。保留原版写入语义，包括原子替换、异常传播和临时文件清理；修正了自动反编译输出中重复替换文件、错误缩进字符串、吞掉异常的问题。

12 项源码对照测试全部通过（3.74 秒）：比较百万点分块筛选、跨 250000 点边界凸包筛选、PCD 字节级一致性、读取往返、文件复制、失败清理、内存信息解析和数字格式化。对照基准为原包字节码，测试中没有模拟或跳过恢复函数。尚未将恢复源码接入 GUI，完整编辑器仍依赖原字节码。

复现新的反编译：在 Python 3.10 环境安装 `tools/requirements-decompile.txt`，运行 `python tools/decompile-depyf.py`；该命令只解析代码对象，不执行目标模块。工具版本固定，但生成的临时变量名称可能变化。

在既有运行镜像中复现源码对照测试：

```bash
docker run --rm --network none -e QT_QPA_PLATFORM=offscreen -v "$PWD:/work" taffy-runtime:ubuntu24.04 python -m pytest -q -p no:cacheprovider tests/test_recovered_source.py
```

第二轮提出的 `load_pcd_data`、`load_full_xyz`、`complete_region` 及部分 Qt 控件已在第三轮恢复。早期指令证据保存在 `analysis/core-python310-disassembly.txt` 和完整反汇编中。
