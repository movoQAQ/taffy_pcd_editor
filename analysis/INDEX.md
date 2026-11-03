# 源码恢复材料索引

运行必需的原始字节码和图标位于 [original/](../original/)，恢复后可执行的源码位于 [recovered/source/](../recovered/source/)。完整主窗口仍依赖原始字节码。

| 材料 | 用途 |
|---|---|
| [main.disassembly.txt](main.disassembly.txt) | v1.2 完整静态反汇编 |
| [core-python310-disassembly.txt](core-python310-disassembly.txt) | 第二轮核心函数的 Python 3.10 原生反汇编 |
| [round3-python310-disassembly.txt](round3-python310-disassembly.txt) | 第三轮点云读取、补全和 Qt 滑块的原生反汇编 |
| [code-objects.json](code-objects.json) | 196 个代码对象的名称、原始行号、参数和引用名称 |
| [depyf-status.json](depyf-status.json) | depyf 反编译及语法检查结果；通过编译不代表行为等价 |
| [recovered/depyf/](../recovered/depyf/) | 保留的自动反编译草稿，仅供人工恢复时参考 |
| [package-contents.txt](package-contents.txt) | 原 deb 文件清单，记录清理前的包布局 |
| [ui/](ui/) | 原版与恢复集成版的 UI 截图及测试记录 |
| [上游说明](../original/UPSTREAM-README.md) | 发布来源及上游说明 |

旧 Docker 构建文件、deb 系统安装布局、失败的整文件反编译输出和逐对象碎片已从工作目录清理，历史版本仍可在 Git 中查看。

需要代码对象二进制时，在安装 `xdis==6.1.8` 的 Python 环境执行 `python tools/split-bytecode.py`，生成的 `analysis/code-objects/` 已忽略。需要重新生成 depyf 草稿时，使用 Python 3.10 安装 `tools/requirements-decompile.txt` 后执行 `python tools/decompile-depyf.py`。这两个脚本仅解析字节码，不执行目标应用。
