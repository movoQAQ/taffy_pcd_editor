"""Integration runner: recovered core/sliders with the original v1.2 GUI.

Explicitly still requires main.pyc; this is not a complete source rebuild.
"""
import argparse
import importlib.util
from importlib.machinery import SourcelessFileLoader
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def load_editor(use_recovered=True):
    if sys.version_info[:2] != (3, 10):
        raise RuntimeError('原始 UI 字节码需要 Python 3.10；请运行 tools/setup-local.sh。')
    path = ROOT / 'original/main.pyc'
    name = 'taffy_integrated' if use_recovered else 'taffy_release'
    loader = SourcelessFileLoader(name, str(path))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader))
    loader.exec_module(module)
    if use_recovered:
        from recovered.source import core, widgets
        for name in ('fmt_number', 'make_demo_cloud', 'load_pcd_data', 'load_full_xyz',
                     'range_mask', 'available_memory_bytes', 'complete_region',
                     'points_inside_region', 'write_full_pcd'):
            setattr(module, name, getattr(core, name))
        module.HeightRangeSlider = widgets.HeightRangeSlider
        module.DragOnlySlider = widgets.DragOnlySlider
    return module


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original', action='store_true', help='仅运行 release 原始字节码，作为对照')
    args = parser.parse_args()
    print('原始 release 模式' if args.original else '恢复代码集成模式（UI 主窗口仍依赖原始字节码）', flush=True)
    load_editor(not args.original).main()
