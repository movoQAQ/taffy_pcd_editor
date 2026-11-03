#!/usr/bin/env python3
"""Exercise the real Rust GUI on X11 with XTest mouse/key input.

Run with a Python containing PyQt5, Pillow and NumPy, for example:
  python3 -B -E -s tests/ui_smoke.py \
      --pcd /path/to/input.pcd --output-dir /tmp/taffy-rust-ui-check

The application exposes read-only widget rectangles/state only when the
TAFFY_UI_STATE environment variable is set. Every mutation below is performed
by a real X11 mouse click or keyboard event, never by writing application state.
The input point cloud is hashed before and after and is never modified.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from typing import Callable

from PIL import Image, ImageChops
import numpy as np
from PyQt5.QtWidgets import QApplication


class X11Driver:
    def __init__(self, state_path: Path):
        self.state_path = state_path
        self.qt = QApplication.instance() or QApplication([])
        self.x11 = ctypes.CDLL("libX11.so.6")
        self.xtst = ctypes.CDLL("libXtst.so.6")
        self.x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
        self.x11.XOpenDisplay.restype = ctypes.c_void_p
        self.x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
        self.x11.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
        self.x11.XDefaultRootWindow.restype = ctypes.c_ulong
        self.x11.XTranslateCoordinates.argtypes = [
            ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong,
            ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_ulong),
        ]
        self.x11.XRaiseWindow.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        self.x11.XSetInputFocus.argtypes = [
            ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong,
        ]
        self.x11.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.x11.XStringToKeysym.argtypes = [ctypes.c_char_p]
        self.x11.XStringToKeysym.restype = ctypes.c_ulong
        self.x11.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        self.x11.XKeysymToKeycode.restype = ctypes.c_uint
        self.xtst.XTestFakeMotionEvent.argtypes = [
            ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_ulong,
        ]
        self.xtst.XTestFakeButtonEvent.argtypes = [
            ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong,
        ]
        self.xtst.XTestFakeKeyEvent.argtypes = [
            ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong,
        ]
        self.display = self.x11.XOpenDisplay(None)
        if not self.display:
            raise RuntimeError("Cannot connect to X11 DISPLAY; run in the local desktop session")
        self.root = self.x11.XDefaultRootWindow(self.display)
        self.window = None

    def close(self):
        if self.display:
            self.x11.XCloseDisplay(self.display)
            self.display = None

    def pump(self, duration: float = 0.05):
        end = time.monotonic() + duration
        while time.monotonic() < end:
            self.qt.processEvents()
            time.sleep(0.01)

    def state(self) -> dict:
        try:
            return json.loads(self.state_path.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def wait(self, predicate: Callable[[dict], bool], description: str,
             timeout: float = 30.0) -> dict:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            state = self.state()
            if state and predicate(state):
                self.pump(0.15)
                return self.state()
            self.pump(0.05)
        raise AssertionError(f"Timed out: {description}; last state={self.state()}")

    def find_window(self, process_id: int | None = None):
        title = self.state().get("window_title", "Taffy PCD Editor")
        listing = subprocess.check_output(["xwininfo", "-root", "-tree"], text=True)
        candidates = []
        for line in listing.splitlines():
            if title in line and "mutter-x11-frames" not in line:
                found = re.match(r"\s*(0x[0-9a-fA-F]+) ", line)
                if found:
                    window = int(found.group(1), 16)
                    if process_id is not None:
                        properties = subprocess.check_output(
                            ["xprop", "-id", hex(window), "_NET_WM_PID"], text=True,
                        )
                        match = re.search(r"=\s*(\d+)", properties)
                        if not match or int(match.group(1)) != process_id:
                            continue
                    candidates.append(window)
        if len(candidates) != 1:
            raise RuntimeError(f"Expected one {title!r} window, found {candidates}")
        self.window = candidates[0]
        self.x11.XRaiseWindow(self.display, self.window)
        self.x11.XSetInputFocus(self.display, self.window, 2, 0)
        self.x11.XSync(self.display, False)
        self.pump(0.3)

    def origin(self) -> tuple[int, int]:
        x, y, child = ctypes.c_int(), ctypes.c_int(), ctypes.c_ulong()
        self.x11.XTranslateCoordinates(
            self.display, self.window, self.root, 0, 0,
            ctypes.byref(x), ctypes.byref(y), ctypes.byref(child),
        )
        return x.value, y.value

    @staticmethod
    def rect_values(rect):
        if isinstance(rect, dict):
            return [rect[key] for key in ("x", "y", "w", "h")]
        return rect

    def click(self, key: str):
        state = self.wait(lambda s: key in s.get("widgets", {}), f"widget {key}")
        # A ScrollArea may keep animating after its first near-target frame.
        # Require stable widget and native-window geometry before aiming input.
        stable_since = time.monotonic()
        stable_deadline = stable_since + 5.0
        previous = None
        while time.monotonic() - stable_since < 0.6:
            if time.monotonic() > stable_deadline:
                raise AssertionError(f"Widget/window geometry did not settle: {key}")
            state = self.state()
            geometry = (state["widgets"][key], self.origin(),
                        state["widgets"].get("viewport"), state.get("pixels_per_point", 1.0))
            if geometry != previous:
                stable_since = time.monotonic()
                previous = geometry
            self.pump(0.03)
        x, y, width, height = self.rect_values(state["widgets"][key])
        scale = state.get("pixels_per_point", 1.0)
        ox, oy = self.origin()
        sx, sy = round(ox + (x + width / 2) * scale), round(oy + (y + height / 2) * scale)
        print(f"Click {key} at ({sx}, {sy}), origin=({ox}, {oy}), rect=({x}, {y}, {width}, {height})", flush=True)
        self.xtst.XTestFakeMotionEvent(self.display, 0, sx, sy, 0)
        self.x11.XSync(self.display, False)
        self.pump(0.08)
        self.xtst.XTestFakeButtonEvent(self.display, 1, True, 0)
        self.xtst.XTestFakeButtonEvent(self.display, 1, False, 30)
        self.x11.XSync(self.display, False)
        self.pump(0.2)

    def scroll(self, key: str, ticks: int):
        state = self.wait(lambda s: key in s.get("widgets", {}), f"scroll target {key}")
        self.scroll_rect(state["widgets"][key], ticks)

    def scroll_panel(self, panel: str, ticks: int):
        state = self.wait(lambda s: panel in s.get("panels", {}), f"scroll panel {panel}")
        self.scroll_rect(state["panels"][panel], ticks)

    def scroll_rect(self, rect, ticks: int):
        state = self.state()
        x, y, width, height = self.rect_values(rect)
        scale = state.get("pixels_per_point", 1.0)
        ox, oy = self.origin()
        sx, sy = round(ox + (x + width / 2) * scale), round(oy + (y + height / 2) * scale)
        self.xtst.XTestFakeMotionEvent(self.display, 0, sx, sy, 0)
        self.x11.XSync(self.display, False)
        self.pump(0.08)
        button = 5 if ticks > 0 else 4
        for _ in range(abs(ticks)):
            self.xtst.XTestFakeButtonEvent(self.display, button, True, 0)
            self.xtst.XTestFakeButtonEvent(self.display, button, False, 10)
            self.x11.XSync(self.display, False)
            self.pump(0.05)
        self.pump(0.4)

    def key(self, name: str, pressed: bool):
        symbol = self.x11.XStringToKeysym(name.encode("ascii"))
        code = self.x11.XKeysymToKeycode(self.display, symbol)
        if not code:
            raise RuntimeError(f"Cannot map X11 key {name}")
        self.xtst.XTestFakeKeyEvent(self.display, code, pressed, 0)
        self.x11.XSync(self.display, False)

    def chord(self, *names: str):
        for name in names:
            self.key(name, True)
        for name in reversed(names):
            self.key(name, False)
        self.pump(0.15)

    def fill(self, widget: str, text: str):
        self.click(widget)
        self.chord("Control_L", "a")
        self.qt.clipboard().setText(text)
        self.pump(0.1)
        self.chord("Control_L", "v")
        self.pump(0.2)

    def screenshot(self, path: Path):
        self.x11.XRaiseWindow(self.display, self.window)
        self.x11.XSync(self.display, False)
        self.pump(0.3)
        picture = self.qt.primaryScreen().grabWindow(self.window)
        if picture.isNull() or not picture.save(str(path)):
            raise RuntimeError(f"Could not capture application screenshot to {path}")

    def modal(self, kind: str, path: Path):
        self.click(f"{kind}_button")
        self.wait(lambda s: f"{kind}_path_input" in s.get("widgets", {}), f"{kind} modal")
        self.fill(f"{kind}_path_input", str(path))
        self.click(f"{kind}_path_confirm")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pcd_parts(path: Path) -> tuple[dict, bytes]:
    header = {}
    with path.open("rb") as stream:
        for _ in range(10000):
            line = stream.readline()
            if not line:
                raise AssertionError(f"Missing DATA header: {path}")
            fields = line.decode("ascii").strip().split()
            if fields and not fields[0].startswith("#"):
                header[fields[0]] = fields[1:]
                if fields[0] == "DATA":
                    assert fields[1:] == ["binary"], "Smoke test requires binary PCD"
                    return header, stream.read()
    raise AssertionError(f"PCD header is too long: {path}")


def layer(state: dict, layer_id) -> dict:
    return next(item for item in state["layers"] if item["id"] == layer_id)


def run(args) -> dict:
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    state_path = output_dir / "state.json"
    state_path.unlink(missing_ok=True)
    exported = output_dir / "roundtrip.pcd"
    exported.unlink(missing_ok=True)
    filtered_export = output_dir / "filtered.pcd"
    filtered_export.unlink(missing_ok=True)
    source = args.pcd.resolve(strict=True)
    original_hash = sha256(source)
    original_header, original_payload = pcd_parts(source)
    points = int(original_header["POINTS"][0])
    report = {"input": str(source), "input_points": points, "input_sha256_before": original_hash,
              "binary": str(args.binary.resolve()), "steps": [], "passed": False}
    started = time.monotonic()
    env = dict(os.environ, TAFFY_UI_STATE=str(state_path), WINIT_UNIX_BACKEND="x11")
    driver = None
    process = None
    log = (output_dir / "gui.log").open("w")

    def record(name):
        report["steps"].append({"name": name, "elapsed_s": round(time.monotonic() - started, 3)})
        print(name, flush=True)

    def idle_count(count):
        return lambda s: len(s.get("layers", [])) == count and not s.get("busy", True)

    try:
        process = subprocess.Popen([str(args.binary.resolve()), str(source), str(source), str(source)],
                                   env=env, stdout=log, stderr=subprocess.STDOUT)
        driver = X11Driver(state_path)
        state = driver.wait(idle_count(3), "three source layers loaded", args.timeout)
        assert all(item["points"] == points for item in state["layers"])
        ids = [item["id"] for item in state["layers"]]
        active = state["selected_layer_id"]
        first = next(item for item in ids if item != active)
        driver.find_window(process.pid)
        driver.screenshot(output_dir / "01-loaded.png")
        report["viewport_rect"] = state.get("widgets", {}).get("viewport")
        report["pixels_per_point"] = state.get("pixels_per_point", 1.0)
        record("Opened native GUI and loaded three full point-cloud layers")

        right_tools = "right" in state.get("panels", {})
        if right_tools:
            # Expand XYZ controls to exercise overflow in the original-style
            # right panel; point fields now live in the separate left panel.
            driver.click("range_section")
            driver.pump(0.8)
            state = driver.state()
        filter_y = driver.rect_values(state["widgets"]["filter_button"])[1]
        if right_tools:
            driver.scroll_panel("right", 4)
        else:
            driver.scroll("filter_button", 4)
        driver.wait(lambda s: driver.rect_values(s["widgets"]["filter_button"])[1] < filter_y - 5,
                    "sidebar scrolls to lower controls")
        driver.screenshot(output_dir / "01-sidebar-scrolled.png")
        if right_tools:
            driver.scroll_panel("right", -12)
        else:
            driver.scroll("filter_button", -12)
        driver.wait(lambda s: abs(driver.rect_values(s["widgets"]["filter_button"])[1] - filter_y) < 2,
                    "sidebar returned to top")
        driver.pump(0.7)
        if right_tools:
            driver.click("range_section")
        record("Scrolled the processing tools panel down and back to the top")

        driver.click(f"layer_visible_{first}")
        driver.wait(lambda s: not layer(s, first)["visible"], "first layer hidden")
        driver.click(f"layer_visible_{first}")
        driver.wait(lambda s: layer(s, first)["visible"], "first layer visible")
        record("Toggled layer visibility off and on")

        driver.click(f"layer_delete_{first}")
        driver.click("delete_cancel")
        state = driver.wait(idle_count(3), "cancel deletion")
        assert state["selected_layer_id"] == active
        record("Cancelled deletion; all layers and active selection retained")

        driver.click(f"layer_delete_{first}")
        driver.click("delete_confirm")
        state = driver.wait(idle_count(2), "nonactive layer deleted")
        assert first not in [item["id"] for item in state["layers"]]
        assert state["selected_layer_id"] == active
        record("Deleted nonactive layer without changing active selection")

        driver.click(f"layer_delete_{active}")
        driver.click("delete_confirm")
        state = driver.wait(idle_count(1), "active layer deleted")
        remaining = state["layers"][0]["id"]
        assert state["selected_layer_id"] == remaining
        record("Deleted active layer and selected the remaining layer")

        driver.click(f"layer_delete_{remaining}")
        driver.click("delete_confirm")
        state = driver.wait(idle_count(0), "last layer deleted")
        assert state["selected_layer_id"] is None
        driver.screenshot(output_dir / "02-empty.png")
        record("Deleted final layer; scene is empty and selection is cleared")

        driver.modal("import", source)
        state = driver.wait(idle_count(1), "source reimported", args.timeout)
        assert state["layers"][0]["points"] == points
        assert state["selected_layer_id"] == state["layers"][0]["id"]
        driver.screenshot(output_dir / "03-reimported.png")
        record("Reimported point cloud through the real path dialog")

        reimported_id = state["layers"][0]["id"]
        driver.click(f"layer_visible_{reimported_id}")
        driver.wait(lambda s: not layer(s, reimported_id)["visible"], "single layer hidden")
        driver.screenshot(output_dir / "04-hidden.png")
        driver.click(f"layer_visible_{reimported_id}")
        driver.wait(lambda s: layer(s, reimported_id)["visible"], "single layer visible again")
        record("Hid and restored the only layer, exercising renderer visibility")

        driver.modal("export", exported)
        driver.wait(lambda s: exported.exists() and not s.get("busy", True), "export completed", args.timeout)
        exported_header, exported_payload = pcd_parts(exported)
        for key in ("FIELDS", "SIZE", "TYPE", "COUNT", "POINTS"):
            assert exported_header.get(key) == original_header.get(key), f"Export header differs: {key}"
        assert exported_payload == original_payload, "Export changed point records or normal fields"
        report["exported_points"] = int(exported_header["POINTS"][0])
        report["exported_fields"] = exported_header["FIELDS"]
        report["export_payload_sha256"] = hashlib.sha256(exported_payload).hexdigest()
        record("Exported all points; full binary records and all fields match input")

        viewport = report.get("viewport_rect")
        if viewport:
            x, y, w, h = driver.rect_values(viewport)
            scale = report["pixels_per_point"]
            bounds = tuple(round(value * scale) for value in (x, y, x + w, y + h))
            loaded = Image.open(output_dir / "01-loaded.png").convert("RGB").crop(bounds)
            empty = Image.open(output_dir / "02-empty.png").convert("RGB").crop(bounds)
            difference = ImageChops.difference(loaded, empty).convert("L")
            changed_pixels = sum(difference.histogram()[13:])
            report["viewport_changed_pixels"] = changed_pixels
            assert changed_pixels > 1000, "Loaded and empty viewport appear identical"
            record("Verified populated and empty GPU viewports differ visibly")
            shown = Image.open(output_dir / "03-reimported.png").convert("RGB").crop(bounds)
            hidden = Image.open(output_dir / "04-hidden.png").convert("RGB").crop(bounds)
            visibility_difference = ImageChops.difference(shown, hidden).convert("L")
            visibility_pixels = sum(visibility_difference.histogram()[13:])
            report["visibility_changed_pixels"] = visibility_pixels
            assert visibility_pixels > 1000, "Visibility checkbox did not change rendered points"
            record("Verified visibility checkbox actually removes points from the viewport")

        # Independent reference for the default full-bounds 5 cm voxel filter.
        sizes = [int(value) for value in original_header["SIZE"]]
        counts = [int(value) for value in original_header.get("COUNT", ["1"] * len(sizes))]
        stride = sum(size * count for size, count in zip(sizes, counts))
        offsets = np.cumsum([0] + [size * count for size, count in zip(sizes, counts)])
        formats, xyz_offsets = [], []
        for axis in ("x", "y", "z"):
            index = original_header["FIELDS"].index(axis)
            assert original_header["TYPE"][index] == "F" and counts[index] == 1
            formats.append(f"<f{sizes[index]}")
            xyz_offsets.append(int(offsets[index]))
        dtype = np.dtype({"names": ["x", "y", "z"], "formats": formats,
                          "offsets": xyz_offsets, "itemsize": stride})
        records = np.frombuffer(original_payload, dtype=dtype)
        xyz = np.column_stack([records[axis] for axis in ("x", "y", "z")]).astype(np.float32)
        cells = np.floor(xyz / np.float32(0.05)).astype(np.int32)
        _, first_indices = np.unique(cells, axis=0, return_index=True)
        expected_indices = np.sort(first_indices)
        raw_records = np.frombuffer(original_payload, dtype=np.dtype((np.void, stride)))
        expected_payload = raw_records[expected_indices].tobytes()

        driver.click("filter_button")
        state = driver.wait(idle_count(2), "filtered layer generated", args.timeout)
        filtered_id = state["selected_layer_id"]
        assert filtered_id != reimported_id
        assert not layer(state, reimported_id)["visible"]
        assert layer(state, filtered_id)["points"] == len(expected_indices)
        driver.screenshot(output_dir / "05-filtered.png")
        record("Generated a filtered layer with the actual filter button")
        driver.modal("export", filtered_export)
        driver.wait(lambda s: filtered_export.exists() and not s.get("busy", True),
                    "filtered export completed", args.timeout)
        filtered_header, filtered_payload = pcd_parts(filtered_export)
        for key in ("FIELDS", "SIZE", "TYPE", "COUNT"):
            assert filtered_header.get(key) == original_header.get(key), f"Filtered export header differs: {key}"
        assert int(filtered_header["POINTS"][0]) == len(expected_indices)
        assert filtered_payload == expected_payload, "Filtered export differs from independent NumPy reference"
        report["filtered_points"] = len(expected_indices)
        report["filtered_payload_sha256"] = hashlib.sha256(filtered_payload).hexdigest()
        record("Edited export matches independent NumPy reference, including every normal field")

        report["input_sha256_after"] = sha256(source)
        assert report["input_sha256_after"] == original_hash, "Original PCD was modified"
        record("Confirmed original point-cloud file remains unchanged")
        driver.chord("Alt_L", "F4")
        report["gui_exit_code"] = process.wait(timeout=10)
        assert report["gui_exit_code"] == 0, "Native window close did not exit cleanly"
        record("Closed the native window with Alt+F4; application exited normally")
        report["passed"] = True
    except Exception as error:
        report["error"] = f"{type(error).__name__}: {error}"
        if driver:
            report["last_state"] = driver.state()
            if driver.window and process and process.poll() is None:
                try:
                    driver.screenshot(output_dir / "failure.png")
                except Exception as screenshot_error:
                    report["screenshot_error"] = str(screenshot_error)
        raise
    finally:
        report["duration_s"] = round(time.monotonic() - started, 3)
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        if driver:
            driver.close()
        log.close()
        (output_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path,
                        default=Path(__file__).resolve().parents[1] / "taffy-pcd-editor")
    parser.add_argument("--pcd", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("/tmp/taffy-rust-ui-check"))
    parser.add_argument("--timeout", type=float, default=45.0)
    args = parser.parse_args()
    report = run(args)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
