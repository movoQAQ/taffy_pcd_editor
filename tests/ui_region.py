#!/usr/bin/env python3
"""Native X11 region-selection/deletion regression using real mouse input.

Run with the project's Python UI-test environment (PyQt5, NumPy, SciPy, Pillow).
TAFFY_UI_STATE is read-only telemetry: picking, preview, deletion and exporting
are all invoked through the GUI. A separate SciPy hull checks the resulting
records, including normals, against the unchanged source PCD.
"""
from __future__ import annotations

import argparse
import ctypes
import itertools
import json
import os
from pathlib import Path
import subprocess
import time

import numpy as np
from scipy.spatial import ConvexHull

from ui_smoke import X11Driver, layer, pcd_parts, sha256


class RegionDriver(X11Driver):
    def activate(self):
        class ClientMessage(ctypes.Structure):
            _fields_ = [("type", ctypes.c_int), ("serial", ctypes.c_ulong),
                        ("send_event", ctypes.c_int), ("display", ctypes.c_void_p),
                        ("window", ctypes.c_ulong), ("message_type", ctypes.c_ulong),
                        ("format", ctypes.c_int), ("data", ctypes.c_long * 5)]
        self.x11.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
        self.x11.XInternAtom.restype = ctypes.c_ulong
        self.x11.XSendEvent.argtypes = [ctypes.c_void_p, ctypes.c_ulong,
                                       ctypes.c_int, ctypes.c_long, ctypes.c_void_p]
        event = (ctypes.c_long * 24)()
        message = ClientMessage.from_buffer(event)
        message.type, message.send_event = 33, 1
        message.display, message.window = self.display, self.window
        message.message_type = self.x11.XInternAtom(self.display, b"_NET_ACTIVE_WINDOW", False)
        message.format, message.data[0] = 32, 2
        self.x11.XSendEvent(self.display, self.root, False,
                            (1 << 19) | (1 << 20), ctypes.byref(event))
        self.x11.XSync(self.display, False)
        self.pump(0.15)

    def chord(self, *names):
        self.activate()
        super().chord(*names)

    def screenshot(self, path):
        self.activate()
        super().screenshot(path)

    def move_to(self, x: float, y: float):
        self.activate()
        scale = self.state().get("pixels_per_point", 1.0)
        ox, oy = self.origin()
        self.xtst.XTestFakeMotionEvent(
            self.display, 0, round(ox + x * scale), round(oy + y * scale), 0,
        )
        self.x11.XSync(self.display, False)
        self.pump(0.08)

    def double_click(self, x: float, y: float):
        self.move_to(x, y)
        for _ in range(2):
            self.xtst.XTestFakeButtonEvent(self.display, 1, True, 0)
            self.x11.XSync(self.display, False)
            self.pump(0.04)
            self.xtst.XTestFakeButtonEvent(self.display, 1, False, 0)
            self.x11.XSync(self.display, False)
            self.pump(0.08)
        self.pump(0.3)

    def ensure_visible(self, key: str):
        """Scroll the right tool panel, never aim at an off-screen control."""
        for _ in range(16):
            state = self.wait(lambda s: key in s.get("widgets", {}), f"widget {key}")
            x, y, width, height = self.rect_values(state["widgets"][key])
            panel = state.get("panels", {}).get("right")
            if panel is None:
                return
            px, py, pw, ph = self.rect_values(panel)
            if py + 12 < y and y + height < py + ph - 12:
                return
            self.move_to(px + pw * 0.7, py + ph * 0.5)
            button = 4 if y <= py + 12 else 5
            for _ in range(3):
                self.xtst.XTestFakeButtonEvent(self.display, button, True, 0)
                self.xtst.XTestFakeButtonEvent(self.display, button, False, 10)
                self.x11.XSync(self.display, False)
                self.pump(0.05)
            self.pump(0.6)
        raise AssertionError(f"Could not scroll {key} into the right panel")

    def click(self, key: str):
        self.activate()
        if key.startswith("region_") or key in ("filter_button", "filter_section", "range_section"):
            self.ensure_visible(key)
        super().click(key)

    def fill_number(self, key: str, value: str):
        self.ensure_visible(key)
        self.pump(0.6)
        x, y, width, height = self.rect_values(self.state()["widgets"][key])
        self.double_click(x + width / 2, y + height / 2)
        self.chord("Control_L", "a")
        self.qt.clipboard().setText(value)
        self.pump(0.1)
        self.chord("Control_L", "v")
        self.chord("Return")


def source_arrays(header: dict, payload: bytes):
    sizes = [int(value) for value in header["SIZE"]]
    counts = [int(value) for value in header.get("COUNT", ["1"] * len(sizes))]
    widths = [size * count for size, count in zip(sizes, counts)]
    stride = sum(widths)
    offsets = np.cumsum([0] + widths)
    formats, xyz_offsets = [], []
    for axis in ("x", "y", "z"):
        index = header["FIELDS"].index(axis)
        assert header["TYPE"][index] == "F" and counts[index] == 1
        formats.append(f"<f{sizes[index]}")
        xyz_offsets.append(int(offsets[index]))
    dtype = np.dtype({"names": ["x", "y", "z"], "formats": formats,
                      "offsets": xyz_offsets, "itemsize": stride})
    records = np.frombuffer(payload, dtype=dtype)
    xyz = np.column_stack([records[axis] for axis in ("x", "y", "z")]).astype(np.float32)
    raw = np.frombuffer(payload, dtype=np.dtype((np.void, stride)))
    return xyz, raw


def expected_region_mask(xyz: np.ndarray, state: dict) -> tuple[np.ndarray, dict]:
    region = state["region"]
    picks = np.asarray(region["picks"], dtype=np.float32).astype(np.float64)
    # Match the displayed cm -> metre conversion, then independently build hull.
    expansion = float(np.float32(np.float32(region["expand_cm"]) / np.float32(100.0)))
    offsets = np.asarray(list(itertools.product((-expansion, expansion), repeat=3)))
    vertices = np.unique((picks[:, None, :] + offsets).reshape(-1, 3), axis=0)
    hull = ConvexHull(vertices)
    low, high = vertices.min(axis=0), vertices.max(axis=0)
    ranges = np.asarray(state.get("ranges", region.get("ranges")), dtype=np.float32)
    assert ranges.shape == (3, 2), "Telemetry must include the actual XYZ limits"
    candidate = np.all((xyz >= ranges[:, 0]) & (xyz <= ranges[:, 1]), axis=1)
    candidate &= np.all((xyz.astype(np.float64) >= low) & (xyz.astype(np.float64) <= high), axis=1)
    mask = np.zeros(len(xyz), dtype=bool)
    indices = np.flatnonzero(candidate)
    # Chunk matrix products so large maps do not need an N * faces allocation.
    for begin in range(0, len(indices), 16384):
        batch = indices[begin:begin + 16384]
        distances = xyz[batch].astype(np.float64) @ hull.equations[:, :3].T
        distances += hull.equations[:, 3]
        mask[batch] = np.all(distances <= 1e-6, axis=1)
    return mask, {"expand_cm": region["expand_cm"], "picks": region["picks"],
                  "scipy_hull_vertices": len(hull.vertices),
                  "scipy_hull_faces": len(hull.simplices), "ranges": ranges.tolist()}


def run(args) -> dict:
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    state_path = output / "state.json"
    state_path.unlink(missing_ok=True)
    exported = output / "region-deleted.pcd"
    exported.unlink(missing_ok=True)
    source = args.pcd.resolve(strict=True)
    original_hash = sha256(source)
    original_header, original_payload = pcd_parts(source)
    xyz, raw_records = source_arrays(original_header, original_payload)
    points = len(xyz)
    report = {"input": str(source), "input_points": points, "input_sha256_before": original_hash,
              "binary": str(args.binary.resolve()), "steps": [], "passed": False}
    started = time.monotonic()
    env = dict(os.environ, TAFFY_UI_STATE=str(state_path), WINIT_UNIX_BACKEND="x11")
    driver = None
    process = None
    log = (output / "gui.log").open("w")

    def record(name):
        report["steps"].append({"name": name, "elapsed_s": round(time.monotonic() - started, 3)})
        print(name, flush=True)

    def idle_layers(count):
        return lambda s: len(s.get("layers", [])) == count and not s.get("busy", True)

    def pick_candidate(index):
        state = driver.state()
        candidates = state.get("projected_candidates", state["region"].get("projected_candidates", []))
        assert index < len(candidates), f"Not enough projected point candidates: {len(candidates)}"
        candidate = candidates[index]
        x, y = candidate[:2]
        before = len(state["region"]["picks"])
        driver.double_click(x, y)
        return driver.wait(lambda s: len(s.get("region", {}).get("picks", [])) == before + 1,
                           f"point {index} picked by viewport double-click", 5)

    try:
        process = subprocess.Popen([str(args.binary.resolve()), str(source)],
                                   env=env, stdout=log, stderr=subprocess.STDOUT)
        driver = RegionDriver(state_path)
        state = driver.wait(idle_layers(1), "source loaded", args.timeout)
        assert state["layers"][0]["points"] == points
        source_id = state["selected_layer_id"]
        driver.find_window(process.pid)
        driver.click("top_button")
        driver.screenshot(output / "01-original-assets.png")
        record("Opened native GUI with original assets and the complete source cloud")

        driver.click("region_convex_mode")
        driver.click("region_start")
        driver.wait(lambda s: s.get("region", {}).get("picking"), "region picking enabled")
        pick_candidate(0)
        pick_candidate(1)
        driver.click("region_undo_pick")
        driver.wait(lambda s: len(s["region"]["picks"]) == 1, "last picked point undone")
        driver.click("region_clear")
        state = driver.wait(lambda s: not s["region"]["picks"] and s["region"].get("count") is None,
                            "selection cleared")
        assert len(state["layers"]) == 1 and state["layers"][0]["points"] == points
        record("Double-clicked actual cloud points; undo and clear leave the source intact")

        if not state["region"]["picking"]:
            driver.click("region_start")
        driver.fill_number("region_expand", "20")
        driver.wait(lambda s: abs(s["region"].get("expand_cm", -1) - 20.0) < 1e-5,
                    "XYZ expansion edited to 20 cm")
        for index in range(6):
            pick_candidate(index)
        driver.click("region_calculate")
        state = driver.wait(lambda s: s.get("region", {}).get("count") is not None
                            and not s["region"].get("computing", True),
                            "convex selection preview computed", args.timeout)
        assert state.get("error") is None, state.get("error")
        expected_mask, reference = expected_region_mask(xyz, state)
        deleted = int(expected_mask.sum())
        assert 0 < deleted < points, f"Reference selection should remove part of the map: {deleted}"
        assert state["region"]["count"] == deleted, (
            f"Preview count differs from SciPy: GUI={state['region']['count']}, SciPy={deleted}")
        assert layer(state, source_id)["points"] == points, "Preview mutated the source layer"
        report["reference"] = reference
        report["deleted_points"] = deleted
        driver.screenshot(output / "02-region-preview.png")
        record(f"Six actual double-click picks yield a SciPy-verified convex preview of {deleted} points")

        driver.click("region_delete")
        state = driver.wait(idle_layers(2), "region deletion produced an edited layer", args.timeout)
        edited_id = state["selected_layer_id"]
        assert edited_id != source_id
        assert layer(state, source_id)["points"] == points
        assert not layer(state, source_id)["visible"]
        assert layer(state, edited_id)["visible"]
        assert layer(state, edited_id)["points"] == points - deleted
        assert not state["region"]["picks"] and state["region"].get("count") is None
        driver.screenshot(output / "03-region-deleted.png")
        record("Delete Region created the survivor layer and retained the hidden original")

        driver.modal("export", exported)
        driver.wait(lambda s: exported.exists() and not s.get("busy", True),
                    "edited layer export completed", args.timeout)
        header, payload = pcd_parts(exported)
        for key in ("FIELDS", "SIZE", "TYPE", "COUNT"):
            assert header.get(key) == original_header.get(key), f"Export changed {key}"
        assert int(header["POINTS"][0]) == points - deleted
        expected_payload = raw_records[~expected_mask].tobytes()
        assert payload == expected_payload, "Export survivors or full field records differ from SciPy"
        report["surviving_points"] = points - deleted
        report["exported_fields"] = header["FIELDS"]
        report["export_sha256"] = sha256(exported)
        record("Export matches independent SciPy survivor records byte-for-byte, including normals")

        # A pending edit must not carry across the selected layer boundary.
        driver.click("region_start")
        pick_candidate(0)
        driver.click(f"layer_select_{source_id}")
        state = driver.wait(lambda s: s.get("selected_layer_id") == source_id,
                            "switched selection back to original")
        assert not state["region"]["picks"] and state["region"].get("count") is None
        assert state["region"].get("layer_id") in (None, source_id)
        record("Switching layers clears stale picked geometry and preview state")

        report["input_sha256_after"] = sha256(source)
        assert report["input_sha256_after"] == original_hash, "Original PCD was modified"
        record("Confirmed source file hash is unchanged")
        driver.chord("Alt_L", "F4")
        report["gui_exit_code"] = process.wait(timeout=10)
        assert report["gui_exit_code"] == 0
        report["passed"] = True
        record("Closed the real GUI cleanly")
    except Exception as error:
        report["error"] = f"{type(error).__name__}: {error}"
        if driver:
            report["last_state"] = driver.state()
            if driver.window and process and process.poll() is None:
                try:
                    driver.screenshot(output / "failure.png")
                except Exception as capture_error:
                    report["screenshot_error"] = str(capture_error)
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
        (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path,
                        default=Path(__file__).resolve().parents[1] / "taffy-pcd-editor")
    parser.add_argument("--pcd", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("/tmp/taffy-rust-region-check"))
    parser.add_argument("--timeout", type=float, default=45.0)
    args = parser.parse_args()
    print(json.dumps(run(args), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
