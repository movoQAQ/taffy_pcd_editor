#!/usr/bin/env python3
"""Compare every PCD in a directory against the independent PCL reader.

Requires rustc, g++, pkg-config and PCL development files. For optional real GUI
checks, also requires X11, PyQt5, Pillow and NumPy (used by ui_smoke.X11Driver).
Nothing in the source-data directory is written. Temporary converted files live
in the chosen output directory and are removed after successful comparison.

    python3 -B -E -s tests/pcd_formats.py --pcd-dir /path/to/pcds --gui
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import time


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_pcd(path, allow_pcl_page_padding=False):
    header = {}
    with path.open("rb") as stream:
        for _ in range(10000):
            line = stream.readline()
            if not line:
                raise AssertionError(f"Missing DATA header: {path}")
            tokens = line.decode("ascii").strip().split()
            if not tokens or tokens[0].startswith("#"):
                continue
            header[tokens[0]] = tokens[1:]
            if tokens[0] == "DATA":
                digest = hashlib.sha256()
                size = 0
                # PCL's mmap writer can leave zero-filled page padding after
                # the declared records. Compare those records, not page slack.
                remaining = None
                if allow_pcl_page_padding:
                    remaining = int(header["POINTS"][0]) * sum(
                        int(size) * int(count) for size, count
                        in zip(header["SIZE"], header["COUNT"]))
                while remaining is None or remaining:
                    chunk = stream.read(1024 * 1024 if remaining is None
                                        else min(1024 * 1024, remaining))
                    if not chunk:
                        assert remaining is None or remaining == 0, "Truncated PCL reference"
                        break
                    size += len(chunk)
                    digest.update(chunk)
                    if remaining is not None:
                        remaining -= len(chunk)
                if allow_pcl_page_padding:
                    assert not any(stream.read()), "Nonzero bytes after PCL records"
                return {"header": header, "payload_bytes": size,
                        "payload_sha256": digest.hexdigest()}
    raise AssertionError(f"PCD header is too long: {path}")


def compare_headers(reference, actual):
    for key in ("FIELDS", "SIZE", "TYPE", "COUNT", "POINTS"):
        assert reference["header"][key] == actual["header"][key], key
    assert list(map(float, reference["header"]["VIEWPOINT"])) == list(
        map(float, actual["header"]["VIEWPOINT"])), "VIEWPOINT"


def compare(reference, actual):
    compare_headers(reference, actual)
    assert actual["header"]["DATA"] == ["binary"]
    for key in ("payload_bytes", "payload_sha256"):
        assert reference[key] == actual[key], f"Full point records differ: {key}"


def verify_gui(args, entries, output):
    import ctypes
    import numpy as np
    from ui_smoke import X11Driver, pcd_parts

    class FocusedDriver(X11Driver):
        # Mutter may keep a newly focused Codex window above an XRaiseWindow
        # client. Request activation through the window manager before input.
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
            self.pump(0.2)

        def click(self, key):
            self.activate()
            super().click(key)

        def chord(self, *names):
            self.activate()
            super().chord(*names)

        def screenshot(self, path):
            self.activate()
            super().screenshot(path)

    # Load every file, including the largest ASCII cloud; leave compressed last
    # for a real filter/export check with its nontrivial intensity values.
    selected = sorted(entries, key=lambda entry: entry["encoding"] == "binary_compressed")
    small_ascii = min((entry for entry in entries if entry["encoding"] == "ascii"),
                      key=lambda entry: entry["points"])
    state_path = output / "gui-state.json"
    state_path.unlink(missing_ok=True)
    env = dict(os.environ, TAFFY_UI_STATE=str(state_path), WINIT_UNIX_BACKEND="x11")
    process = driver = None
    report = {"passed": False, "layers": []}
    with (output / "gui.log").open("w") as log:
        try:
            process = subprocess.Popen([str(args.binary.resolve())], env=env,
                                       stdout=log, stderr=subprocess.STDOUT)
            driver = FocusedDriver(state_path)
            driver.wait(lambda s: not s.get("busy", True), "empty GUI started")
            driver.find_window(process.pid)
            for index, entry in enumerate(selected):
                driver.modal("import", Path(entry["input"]))
                state = driver.wait(
                    lambda s: not s.get("busy", True), "PCD import finished", 120)
                assert not state.get("error"), state.get("error")
                assert len(state["layers"]) == index + 1, state
                layer = next(item for item in state["layers"]
                             if item["id"] == state["selected_layer_id"])
                assert layer["points"] == entry["points"], layer
                driver.click("fit_button")
                driver.screenshot(output / f"gui-{index}-{entry['encoding']}.png")
                layer_report = {"input": entry["input"], "encoding": entry["encoding"],
                                "points": layer["points"]}
                report["layers"].append(layer_report)
                if entry is not small_ascii and entry["encoding"] != "binary_compressed":
                    continue
                exported = output / f"gui-{entry['encoding']}.pcd"
                exported.unlink(missing_ok=True)
                driver.modal("export", exported)
                state = driver.wait(
                    lambda s: not s.get("busy", True), "GUI export finished", 120)
                assert not state.get("error"), state.get("error")
                assert exported.exists(), "GUI export did not create the PCD"
                compare(entry["reference"], inspect_pcd(exported))
                layer_report["full_records_match_pcl"] = True
                if entry["encoding"] == "binary_compressed":
                    # This fixture has F32 x/y/z/intensity, all COUNT 1. Compare
                    # 5 cm voxel selection independently using NumPy.
                    header, payload = pcd_parts(exported)
                    assert header["FIELDS"] == ["x", "y", "z", "intensity"]
                    assert header["SIZE"] == ["4"] * 4 and header["COUNT"] == ["1"] * 4
                    records = np.frombuffer(payload, dtype="<f4").reshape(-1, 4)
                    cells = np.floor(records[:, :3] / np.float32(0.05)).astype(np.int32)
                    _, first = np.unique(cells, axis=0, return_index=True)
                    expected_payload = records[np.sort(first)].tobytes()
                    driver.click("filter_button")
                    state = driver.wait(lambda s: len(s.get("layers", [])) == len(entries) + 1
                                        and not s.get("busy", True), "filtered cloud", 120)
                    assert not state.get("error"), state.get("error")
                    filtered = next(item for item in state["layers"]
                                    if item["id"] == state["selected_layer_id"])
                    assert filtered["points"] == len(first)
                    filtered_path = output / "gui-filtered.pcd"
                    filtered_path.unlink(missing_ok=True)
                    driver.modal("export", filtered_path)
                    driver.wait(lambda s: filtered_path.exists() and not s.get("busy", True),
                                "filtered export", 120)
                    filtered_header, filtered_payload = pcd_parts(filtered_path)
                    for key in ("FIELDS", "SIZE", "TYPE", "COUNT", "VIEWPOINT"):
                        assert filtered_header[key] == header[key], key
                    assert filtered_payload == expected_payload, "Filtered records differ from NumPy"
                    report["filter"] = {"input_encoding": entry["encoding"],
                                        "points": len(first), "full_records_match_numpy": True,
                                        "payload_sha256": hashlib.sha256(filtered_payload).hexdigest()}
                    driver.screenshot(output / "gui-filtered.png")
                    filtered_path.unlink()
                exported.unlink()
            driver.chord("Alt_L", "F4")
            report["exit_code"] = process.wait(timeout=10)
            assert report["exit_code"] == 0
            report["passed"] = True
        except Exception:
            if driver and driver.window and process and process.poll() is None:
                driver.screenshot(output / "gui-failure.png")
            raise
        finally:
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            if driver:
                driver.close()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pcd-dir", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path,
                        default=Path("/tmp/taffy-pcd-formats-check"))
    parser.add_argument("--binary", type=Path,
                        default=Path(__file__).resolve().parents[1] / "taffy-pcd-editor")
    parser.add_argument("--reference-only", action="store_true")
    parser.add_argument("--gui", action="store_true")
    args = parser.parse_args()
    assert not (args.reference_only and args.gui)
    source_dir = args.pcd_dir.resolve(strict=True)
    output = args.output_dir.resolve()
    assert output != source_dir, "Keep test outputs outside the source-data directory"
    output.mkdir(parents=True, exist_ok=True)
    sources = sorted(source_dir.glob("*.pcd"))
    assert sources, "No PCD files found"
    tests = Path(__file__).resolve().parent
    reference = output / "pcd-reference"
    pkg = subprocess.check_output(["pkg-config", "--cflags", "--libs", "pcl_io"], text=True)
    subprocess.run(["g++", "-std=c++17", "-O2", str(tests / "pcd_reference.cpp"),
                    "-o", str(reference), *shlex.split(pkg)], check=True)
    probe = output / "pcd-read-probe"
    if not args.reference_only:
        library = output / "libtaffy_pcd_core.rlib"
        subprocess.run(["rustc", "--edition=2021", "-O", "--crate-type=rlib",
                        "--crate-name=taffy_pcd_core", str(tests.parent / "core/src/lib.rs"),
                        "-o", str(library)], check=True)
        subprocess.run(["rustc", "--edition=2021", "-O", str(tests / "pcd_read_probe.rs"),
                        "--extern", f"taffy_pcd_core={library}", "-o", str(probe)], check=True)
    report = {"passed": False, "reference_only": args.reference_only,
              "reference": "PCL PCDReader / PCDWriter binary output",
              "pcl_version": subprocess.check_output(
                  ["pkg-config", "--modversion", "pcl_io"], text=True).strip(),
              "files": []}
    started = time.monotonic()
    try:
        for index, source in enumerate(sources):
            before = sha256(source)
            original = inspect_pcd(source)
            ref_path = output / f"reference-{index}.pcd"
            actual_path = output / f"rust-{index}.pcd"
            actual_path.unlink(missing_ok=True)
            subprocess.run([str(reference), str(source), str(ref_path)], check=True)
            expected = inspect_pcd(ref_path, allow_pcl_page_padding=True)
            compare_headers(expected, original)
            if original["header"]["DATA"] == ["binary"]:
                compare(expected, original)
            entry = {"input": str(source), "input_sha256_before": before,
                     "encoding": original["header"]["DATA"][0],
                     "points": int(original["header"]["POINTS"][0]),
                     "reference": expected}
            if not args.reference_only:
                subprocess.run([str(probe), str(source), str(actual_path)], check=True)
                compare(expected, inspect_pcd(actual_path))
                entry["full_records_match_pcl"] = True
                actual_path.unlink()
            entry["input_sha256_after"] = sha256(source)
            assert entry["input_sha256_after"] == before, f"Input changed: {source}"
            report["files"].append(entry)
            ref_path.unlink()
            print(f"Verified {source.name}: {entry['points']} {entry['encoding']} points", flush=True)
        if args.gui:
            report["gui"] = verify_gui(args, report["files"], output)
            for entry in report["files"]:
                assert sha256(Path(entry["input"])) == entry["input_sha256_before"]
        report["passed"] = True
    except Exception as error:
        report["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        report["duration_s"] = round(time.monotonic() - started, 3)
        (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
