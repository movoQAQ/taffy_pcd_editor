#!/usr/bin/env python3
"""Compare Rust convex-region masks with independent SciPy/Qhull results.

Run with a Python environment containing NumPy and SciPy:
    python3 -E -s tests/region_differential.py

Requires rustc on PATH. Compiles only the dependency-free region module into a
TemporaryDirectory; does not modify the source tree or need a GUI. Standard
output is a JSON validation report. An assertion or compiler error fails the run.
"""

import itertools
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

import numpy as np
import scipy
from scipy.spatial import ConvexHull, QhullError


SEED = 147
CASE_COUNT = 240


def generate_cases():
    rng = np.random.default_rng(SEED)
    cases = []
    for case_index in range(CASE_COUNT):
        count = int(rng.integers(4, 70))
        picks = rng.uniform(-1, 1, (count, 3)).astype(np.float32)
        scale = 10.0 ** rng.uniform(-3, 3)
        picks = (picks * scale).astype(np.float32)
        expansion = np.float32(0 if case_index % 3 == 0 else 0.01 * scale)
        if case_index % 11 == 0:
            picks[:, 2] = 0
        if case_index % 13 == 0:
            picks[:, 2] *= 1e-8
        if case_index % 17 == 0:
            picks += np.float32(1_000_000)
        if case_index % 19 == 0:
            picks = np.concatenate([picks, picks[:3]])
        low = picks.min(axis=0).astype(float) - float(expansion)
        high = picks.max(axis=0).astype(float) + float(expansion)
        queries = rng.uniform(
            low - (high - low) * 0.1, high + (high - low) * 0.1, (2000, 3)
        ).astype(np.float32)
        queries = np.concatenate([queries, picks])
        ranges = np.stack([low - (high - low), high + (high - low)], axis=1).astype(
            np.float32
        )
        if case_index % 5 == 0:
            ranges[0, 0] = np.float32((low[0] + high[0]) / 2)
        expected = None
        if len(np.unique(picks, axis=0)) >= 4:
            offsets = np.array(
                list(itertools.product([-float(expansion), float(expansion)], repeat=3))
            )
            expanded = (picks.astype(float)[:, None, :] + offsets[None, :, :]).reshape(
                -1, 3
            )
            try:
                hull = ConvexHull(expanded)
                clipped_low = np.maximum(expanded.min(axis=0), ranges[:, 0])
                clipped_high = np.minimum(expanded.max(axis=0), ranges[:, 1])
                expected = np.all(
                    (queries >= clipped_low) & (queries <= clipped_high), axis=1
                ) & np.all(
                    queries @ hull.equations[:, :3].T + hull.equations[:, 3] <= 1e-6,
                    axis=1,
                )
            except QhullError:
                pass
        cases.append((picks, queries, expansion, ranges, expected))
    return cases


def probe_input(cases):
    lines = [str(len(cases))]
    for picks, queries, expansion, ranges, _ in cases:
        lines.append(f"{len(picks)} {len(queries)} {expansion:.9g}")
        for points in (picks, queries):
            lines.extend(" ".join(f"{float(x):.9g}" for x in row) for row in points)
        lines.append(" ".join(f"{float(x):.9g}" for x in ranges.ravel()))
    return "\n".join(lines)


def main():
    rustc = shutil.which("rustc")
    if rustc is None:
        raise SystemExit("rustc is required on PATH")
    source = Path(__file__).resolve().with_name("region_probe.rs")
    cases = generate_cases()
    with tempfile.TemporaryDirectory(prefix="taffy-region-differential-") as temporary:
        binary = Path(temporary) / "region-probe"
        subprocess.run(
            [rustc, "--edition=2021", "-O", str(source), "-o", str(binary)], check=True
        )
        completed = subprocess.run(
            [str(binary)], input=probe_input(cases), text=True, capture_output=True, check=True
        )
    results = completed.stdout.splitlines()
    assert len(results) == len(cases), (len(results), len(cases), completed.stderr)
    comparisons = valid = degenerate = 0
    for index, (case, result) in enumerate(zip(cases, results)):
        _, queries, _, _, expected = case
        if expected is None:
            assert result.startswith("ERROR"), f"case {index}: Rust accepted a degenerate hull"
            degenerate += 1
            continue
        assert not result.startswith("ERROR"), f"case {index}: {result}"
        assert len(result) == len(queries), f"case {index}: wrong result length"
        assert set(result) <= {"0", "1"}, f"case {index}: malformed mask"
        actual = np.fromiter((value == "1" for value in result), bool)
        mismatch = np.flatnonzero(actual != expected)
        assert len(mismatch) == 0, (
            f"case {index}: {len(mismatch)} mismatches; first coordinates "
            f"{queries[mismatch[:10]].tolist()}"
        )
        comparisons += len(queries)
        valid += 1
    print(
        json.dumps(
            {
                "status": "passed",
                "reference": "scipy.spatial.ConvexHull (Qhull)",
                "seed": SEED,
                "cases": len(cases),
                "valid_hulls": valid,
                "degenerate_hulls_rejected": degenerate,
                "containment_comparisons": comparisons,
                "numpy": np.__version__,
                "scipy": scipy.__version__,
                "coverage": [
                    "XYZ cube expansion and zero expansion",
                    "coplanar and nearly coplanar picks",
                    "duplicate picks",
                    "large coordinate offsets and multiple scales",
                    "inclusive XYZ clipping and selected-point boundaries",
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
