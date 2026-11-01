# taffy-editor v1.2 静态恢复记录

来源：https://github.com/LYJX-robotic-CC/taffy-editor/releases/tag/v1.2

本仓库是发布包的静态逆向分析材料，不是上游原始源码，也不是已验证可运行的重建版本。上游说明仅发布 Python 3.10 字节码。静态恢复阶段未运行应用；后续已对原始字节码版本执行非 UI 测试和无显示器启动检查，结果见下方。

## 环境

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

## 原始字节码运行与非 UI 测试

运行对象是 `original/rootfs/opt/taffy-editor/main.pyc`，不是不完整的 `recovered/main.py`。运行镜像基于 Ubuntu 24.04，使用独立 Python 3.10，不修改系统 Python。已补齐 Qt xcb 插件依赖和中文字体。

```bash
./tools/build-image.sh    # 静态分析基础镜像已存在时可省略
./tools/build-runtime.sh  # 主机需提供 uv 命令及 CA 信任包
./tools/test-runtime.sh   # 非 UI 测试和虚拟显示器启动检查
./tools/run-app.sh        # Linux X11 桌面上手动启动；需 DISPLAY 和 XAUTHORITY
```

手动启动脚本使用 Xauthority cookie，不放宽 X server 权限；默认软件渲染。文件选择器可访问挂载的仓库 `/work`，可将待测 PCD 放入仓库目录。云环境没有供用户直接操作的桌面；手动启动脚本未在真实桌面验证。

2026-11-01 验证结果：7 项 pytest 测试全部通过（3.87 秒）；覆盖数字格式化、百万点范围筛选分块边界、凸包/可视范围筛选、空/小/百万点二进制 PCD 读写往返和原文件复制。Xvfb 启动检查成功，5 秒内 51 次定时回调，正常退出。测试过程禁网。

这些结果不证明恢复源码可运行，也不代表真实数据下的帧率或 UI 功能已验收。界面功能测试留给用户。
