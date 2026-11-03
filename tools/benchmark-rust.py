#!/usr/bin/env python3
"""Compare the Rust prototype with Taffy's actual worker and minimal NumPy.

Run with the project's Python 3.10: .venv/bin/python -E -s tools/benchmark-rust.py MAP.pcd
Each sample is a fresh process. The controller deliberately imports only stdlib.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import shutil
import statistics
import struct
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ('rust', 'python-editor', 'python-numpy')
THREAD_VARS = ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
               'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS')


def _sha256_file(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _header(path):
    header = {}
    with open(path, 'rb') as stream:
        while True:
            line = stream.readline(1024 * 1024)
            if not line or not line.endswith(b'\n'):
                raise ValueError('incomplete PCD header')
            parts = line.decode('ascii').strip().split()
            if not parts or parts[0].startswith('#'):
                continue
            header[parts[0].upper()] = parts[1:]
            if parts[0].upper() == 'DATA':
                offset = stream.tell()
                break
    fields = header.get('FIELDS', [])
    sizes = [int(value) for value in header.get('SIZE', [])]
    kinds = header.get('TYPE', [])
    counts = [int(value) for value in header.get('COUNT', ['1'] * len(fields))]
    if header.get('DATA') != ['binary']:
        raise ValueError('the benchmark requires DATA binary')
    if not fields or len(set(fields)) != len(fields):
        raise ValueError('missing or duplicate PCD fields')
    if not (len(fields) == len(sizes) == len(kinds) == len(counts)):
        raise ValueError('PCD field metadata lengths differ')
    if any(size <= 0 for size in sizes) or any(count <= 0 for count in counts):
        raise ValueError('PCD SIZE and COUNT must be positive')
    point_count = int(header.get('POINTS', ['-1'])[0])
    record_bytes = sum(size * count for size, count in zip(sizes, counts))
    if point_count < 0 or path.stat().st_size - offset != point_count * record_bytes:
        raise ValueError('PCD payload size does not match POINTS and fields')
    for axis in 'xyz':
        index = fields.index(axis)
        if kinds[index] != 'F' or sizes[index] not in (4, 8) or counts[index] != 1:
            raise ValueError('XYZ must each be a scalar float32 or float64')
    return {'fields': fields, 'sizes': sizes, 'types': kinds, 'counts': counts,
            'points': point_count, 'record_bytes': record_bytes, 'offset': offset,
            'viewpoint': header.get('VIEWPOINT', ['0', '0', '0', '1', '0', '0', '0'])}


def _read_numpy(path, np):
    """Read all payload bytes; expose interleaved float32 XYZ without a copy."""
    metadata = _header(path)
    formats = []
    for size, kind, count in zip(metadata['sizes'], metadata['types'], metadata['counts']):
        if (kind == 'F' and size not in (4, 8)) or kind not in ('F', 'I', 'U') or size not in (1, 2, 4, 8):
            raise ValueError('unsupported PCD field type')
        dtype = np.dtype('<' + kind.lower() + str(size))
        formats.append(dtype if count == 1 else (dtype, (count,)))
    dtype = np.dtype({'names': metadata['fields'], 'formats': formats})
    with open(path, 'rb') as stream:
        stream.seek(metadata['offset'])
        payload = stream.read()
    records = np.frombuffer(payload, dtype=dtype, count=metadata['points'])
    if metadata['fields'][:3] == ['x', 'y', 'z'] and all(
            metadata['types'][i] == 'F' and metadata['sizes'][i] == 4
            and metadata['counts'][i] == 1 for i in range(3)):
        points = np.ndarray((len(records), 3), dtype='<f4', buffer=payload,
                            strides=(dtype.itemsize, 4))
    else:
        points = np.column_stack([records[axis] for axis in 'xyz']).astype(np.float32, copy=False)
    return metadata, records, points


def _scan(points, np):
    if not np.isfinite(points).all():
        raise ValueError('PCD contains non-finite XYZ after float32 conversion')
    if not len(points):
        return [[0.0, 0.0] for _ in range(3)]
    low, high = points.min(axis=0), points.max(axis=0)
    return [[float(low[i]), float(high[i])] for i in range(3)]


def _mask(points, bounds, np):
    mask = np.ones(len(points), dtype=bool)
    for axis, (low, high) in enumerate(bounds):
        mask &= (points[:, axis] >= np.float32(low)) & (points[:, axis] <= np.float32(high))
    return mask


def _indices(points, bounds, voxel, np):
    """Independent NumPy oracle, matching the editor's ordered first-point rule."""
    mask = _mask(points, bounds, np)
    scoped = np.flatnonzero(mask)
    cells = np.floor(points[scoped] / np.float32(voxel))
    if (not np.isfinite(cells).all() or (cells < -2147483648.0).any()
            or (cells >= 2147483648.0).any()):
        raise ValueError('voxel cell is outside the supported signed int32 range')
    _, first = np.unique(cells.astype(np.int32), axis=0, return_index=True)
    return np.concatenate((np.flatnonzero(~mask), scoped[np.sort(first)])), len(scoped)


def _xyz_hash(points, np, indices=None):
    digest = hashlib.sha256()
    count = len(points) if indices is None else len(indices)
    for start in range(0, count, 65536):
        chunk = (points[start:start + 65536] if indices is None
                 else points[indices[start:start + 65536]])
        digest.update(memoryview(np.ascontiguousarray(chunk, dtype='<f4')).cast('B'))
    return digest.hexdigest()


def _editor_module():
    sys.path.insert(0, str(ROOT))
    from tools.run_editor import load_editor
    return load_editor(True)


def _editor_filter(module, points, bounds, voxel):
    completed, failed = [], []
    worker = module.DisplayFilterWorker(
        1, points, voxel, False, 20, 2.0, False, 20, 0.05,
        ranges=dict(zip('xyz', bounds)), auto=None)
    worker.completed.connect(lambda request_id, result: completed.append(result))
    worker.failed.connect(lambda request_id, message: failed.append(message))
    worker.run()
    if failed or len(completed) != 1:
        raise RuntimeError('DisplayFilterWorker did not complete: ' + repr(failed))
    return completed[0]


def _python_worker(args):
    import_start = time.perf_counter()
    import numpy as np
    module = _editor_module() if args.worker == 'python-editor' else None
    imports_ms = (time.perf_counter() - import_start) * 1000
    bounds = np.asarray(args.bounds, dtype=np.float32).reshape(3, 2).tolist()
    load_start = time.perf_counter()
    if module is None:
        metadata, records, points = _read_numpy(args.input, np)
    else:
        metadata = _header(args.input)
        points = module.load_full_xyz(args.input)
    source_bounds = _scan(points, np)
    load_end = time.perf_counter()
    if module is None:
        selected, scoped_count = _indices(points, bounds, args.voxel, np)
        output_count = len(selected)
    else:
        filtered = _editor_filter(module, points, bounds, args.voxel)
        output_count = len(filtered)
    filter_end = time.perf_counter()
    # These diagnostics are excluded from load/filter/work timings. Wall time and
    # peak RSS still include them. Never run a second np.unique for the editor.
    if module is None:
        index_sum = int(selected.sum(dtype=np.uint64))
        xyz_sha256 = _xyz_hash(points, np, selected)
    else:
        index_sum = None
        xyz_sha256 = _xyz_hash(filtered, np)
        scoped_count = sum(int(np.count_nonzero(_mask(points[start:start + 65536], bounds, np)))
                           for start in range(0, len(points), 65536))
    return {'engine': args.worker, 'input_points': len(points),
            'in_range_points': scoped_count, 'output_points': output_count,
            'record_bytes': metadata['record_bytes'], 'bounds': source_bounds,
            'load_scan_ms': (load_end - load_start) * 1000,
            'filter_ms': (filter_end - load_end) * 1000,
            'write_ms': 0.0, 'work_ms': (filter_end - load_start) * 1000,
            'dependencies_import_ms': imports_ms, 'index_sum': index_sum,
            'xyz_sha256': xyz_sha256}


def _rust_command(binary, source, voxel, bounds):
    return [str(binary), str(source), '--voxel', format(voxel, '.17g'), '--bounds',
            *[format(value, '.17g') for pair in bounds for value in pair]]


def _run_json(command, env, rss_file=None):
    if rss_file is not None:
        command = ['/usr/bin/time', '-f', '%M', '-o', str(rss_file), *command]
    started = time.perf_counter()
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True,
                            text=True, timeout=180)
    wall_ms = (time.perf_counter() - started) * 1000
    if result.returncode:
        raise RuntimeError(f'command exited {result.returncode}: {command!r}\n'
                           f'{result.stdout[-4000:]}\n{result.stderr[-4000:]}')
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f'non-JSON stdout: {result.stdout[-4000:]}') from exc
    if rss_file is not None:
        data.update(process_wall_ms=wall_ms, peak_rss_kib=int(rss_file.read_text().strip()))
    if result.stderr.strip():
        data['stderr'] = result.stderr[-4000:]
    return data


def _validation_worker(args):
    import numpy as np
    before = _sha256_file(args.input)
    metadata, records, points = _read_numpy(args.input, np)
    source_bounds = _scan(points, np)
    bounds = [pair[:] for pair in source_bounds]
    bounds[0][0] = float(np.float32(bounds[0][0] + 0.2 * (bounds[0][1] - bounds[0][0])))
    indices, scoped = _indices(points, bounds, args.voxel, np)
    if not scoped:
        raise ValueError('benchmark needs a nonempty filter range; the editor rejects empty ranges')
    with tempfile.TemporaryDirectory(prefix='taffy-rust-validation-') as temporary:
        output = Path(temporary) / 'filtered.pcd'
        result = _run_json(_rust_command(args.rust_bin, args.input, args.voxel, bounds)
                           + ['--output', str(output)], _environment())
        output_meta, output_records, output_points = _read_numpy(output, np)
        if any(output_meta[key] != metadata[key]
               for key in ('fields', 'sizes', 'types', 'counts', 'record_bytes', 'viewpoint')):
            raise AssertionError('Rust output changed PCD field schema or viewpoint')
        expected_bytes = records[indices].tobytes()
        if output_records.tobytes() != expected_bytes:
            raise AssertionError('Rust output differs from independently selected complete records')
        if not np.array_equal(output_points, points[indices]):
            raise AssertionError('Rust output XYZ differs from NumPy reference')
        reference_index_sum = int(indices.sum(dtype=np.uint64))
        if result['index_sum'] != reference_index_sum:
            raise AssertionError('Rust selected-index checksum differs from NumPy reference')
        output_sha256 = _sha256_file(output)
    after = _sha256_file(args.input)
    if before != after:
        raise AssertionError('input file changed during correctness validation')
    return {'input_points': len(points), 'in_range_points': scoped,
            'output_points': len(indices), 'record_bytes': metadata['record_bytes'],
            'source_bounds': source_bounds, 'filter_bounds': bounds,
            'reference_index_sum': reference_index_sum,
            'reference_xyz_sha256': _xyz_hash(points, np, indices),
            'selected_records_sha256': hashlib.sha256(expected_bytes).hexdigest(),
            'output_file_sha256': output_sha256, 'input_sha256_before': before,
            'input_sha256_after_validation': after, 'field_schema': {
                key: metadata[key] for key in ('fields', 'sizes', 'types', 'counts')},
            'full_records_byte_equal': True, 'xyz_equal': True,
            'all_extra_fields_preserved': True, 'numpy_version': np.__version__}


def _environment():
    env = os.environ.copy()
    env.update({name: '2' for name in THREAD_VARS})
    env.update(QT_QPA_PLATFORM='offscreen', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
    return env


def _python_command(args, profile, bounds=None):
    command = [sys.executable, '-B', '-E', '-s', str(Path(__file__).resolve()),
               str(args.input), '--worker', profile, '--voxel', format(args.voxel, '.17g'),
               '--rust-bin', str(args.rust_bin)]
    if bounds is not None:
        command.extend(['--bounds', *[format(value, '.17g') for pair in bounds for value in pair]])
    return command


def _check_sample(sample, reference, profile):
    for key in ('input_points', 'in_range_points', 'output_points', 'record_bytes'):
        if sample[key] != reference[key]:
            raise AssertionError(f'{profile} {key} differs from independent reference')
    # Rust formats f32 with the shortest round-tripping decimal; decoding JSON
    # as Python f64 does not by itself preserve f32 equality.
    decoded_bounds = [[struct.unpack('<f', struct.pack('<f', value))[0] for value in pair]
                      for pair in sample['bounds']]
    if decoded_bounds != reference['source_bounds']:
        raise AssertionError(f'{profile} loaded bounds differ from independent reference')
    if profile == 'python-editor':
        if sample['index_sum'] is not None:
            raise AssertionError('editor must not claim a measured source-index checksum')
    elif sample['index_sum'] != reference['reference_index_sum']:
        raise AssertionError(f'{profile} index checksum differs from independent reference')
    if profile != 'rust' and sample['xyz_sha256'] != reference['reference_xyz_sha256']:
        raise AssertionError(f'{profile} XYZ differs from independent reference')
    for key in ('load_scan_ms', 'filter_ms', 'write_ms', 'work_ms', 'process_wall_ms', 'peak_rss_kib'):
        if not isinstance(sample[key], (int, float)) or not math.isfinite(sample[key]) or sample[key] < 0:
            raise AssertionError(f'{profile} invalid measurement: {key}')


def _machine(args):
    cpu_model = None
    cpu_info = Path('/proc/cpuinfo')
    if cpu_info.is_file():
        for line in cpu_info.read_text().splitlines():
            if line.startswith('model name'):
                cpu_model = line.split(':', 1)[1].strip()
                break
    rustc = shutil.which('rustc')
    if rustc is None and (Path.home() / '.cargo/bin/rustc').is_file():
        rustc = str(Path.home() / '.cargo/bin/rustc')
    version = subprocess.run([rustc, '--version'], capture_output=True, text=True,
                             timeout=30).stdout.strip() if rustc else None
    return {'platform': platform.platform(), 'cpu_model': cpu_model,
            'logical_cpus': os.cpu_count(), 'python': sys.version,
            'python_executable': sys.executable, 'rustc': version,
            'rust_executable': str(args.rust_bin),
            'rust_executable_bytes': args.rust_bin.stat().st_size,
            'thread_environment': {key: '2' for key in THREAD_VARS}}


def _benchmark(args):
    if not args.rust_bin.is_file():
        raise ValueError(f'build the release executable first: cargo build --release --manifest-path {ROOT / "rust/Cargo.toml"}')
    if not Path('/usr/bin/time').is_file():
        raise ValueError('GNU /usr/bin/time is required for independent peak RSS measurements')
    if args.output is not None and args.output.exists():
        raise ValueError('report output already exists; choose a new path')
    env = _environment()
    print('Validating complete PCD records against NumPy outside timed runs...', file=sys.stderr, flush=True)
    reference = _run_json(_python_command(args, 'validate'), env)
    bounds = reference['filter_bounds']
    warmups, samples = [], []
    with tempfile.TemporaryDirectory(prefix='taffy-rust-benchmark-') as temporary:
        for iteration in range(args.repeats + 1):
            warmup = iteration == 0
            shift = 0 if warmup else (iteration - 1) % len(PROFILES)
            order = PROFILES[shift:] + PROFILES[:shift]
            for profile in order:
                print(f'{"Warmup" if warmup else f"Run {iteration}/{args.repeats}"}: {profile}',
                      file=sys.stderr, flush=True)
                command = (_rust_command(args.rust_bin, args.input, args.voxel, bounds)
                           if profile == 'rust' else _python_command(args, profile, bounds))
                rss_file = Path(temporary) / f'{iteration}-{profile}.rss'
                result = _run_json(command, env, rss_file)
                _check_sample(result, reference, profile)
                result.update(profile=profile, repeat=iteration)
                (warmups if warmup else samples).append(result)
    after = _sha256_file(args.input)
    if after != reference['input_sha256_before']:
        raise AssertionError('input file changed during benchmark')
    reference['input_sha256_after_benchmark'] = after
    fields = ('load_scan_ms', 'filter_ms', 'write_ms', 'work_ms', 'process_wall_ms', 'peak_rss_kib')
    medians = {profile: {key: statistics.median(row[key] for row in samples if row['profile'] == profile)
                         for key in fields} for profile in PROFILES}
    return {'schema_version': 1, 'created_at_utc': datetime.now(timezone.utc).isoformat(),
            'input': str(args.input), 'input_bytes': args.input.stat().st_size,
            'voxel_size': args.voxel, 'repeats': args.repeats,
            'environment': _machine(args), 'correctness': reference,
            'method': {
                'scope': 'binary PCD load + full finite/bounds scan + range-limited voxel first-point selection',
                'filter_range': 'full source bounds with x lower bound moved 20% inward, rounded to float32',
                'filter_bounds': bounds, 'bounds_inclusive': True,
                'output_order': 'out-of-range records in original order, then first in-range point per cell in original order',
                'processes': 'fresh subprocess per sample, sequential, rotating profile order; one warmup per profile',
                'cache': 'warm filesystem page cache; correctness pass reads input before measurements; no cache dropping',
                'rss': 'Linux GNU time %M maximum resident set size in KiB per complete subprocess',
                'wall': 'controller perf_counter including process startup, Python imports, diagnostics, and exit',
                'stages': 'load_scan includes data load, finite validation and full XYZ bounds scan; filter selects; work excludes imports and diagnostics',
                'loading': 'Rust and minimal NumPy read the binary payload; editor uses its actual load_full_xyz (memmap where supported) followed by the same full XYZ scan',
                'python_editor': 'actual recovered load_full_xyz plus original DisplayFilterWorker.run; statistical/radius filters and auto tuning disabled; no QApplication or rendering',
                'python_numpy': 'NumPy only; range mask + floor(float32 XYZ / float32 voxel) + unique(axis=0, return_index=True)',
                'selection_results': 'Rust and minimal NumPy select source-record indices; the actual editor worker materializes the resulting XYZ array',
                'selection_algorithms': 'Rust uses a hash set to retain first-seen cells; NumPy and the current editor use np.unique sorting, so algorithm and buffer design differ as well as language',
                'diagnostics': 'XYZ SHA256 and index checksum run outside stage timers but remain in wall/RSS; editor has no indices, so index_sum is null and XYZ is checked independently',
                'export': 'not timed in repeated samples (write_ms=0); separate untimed Rust export checked byte-for-byte against original complete records',
            },
            'limits': [
                'This is a core prototype comparison, not a Rust GUI, GUI FPS, or full application memory benchmark.',
                'NumPy and the current editor already execute native C/C++ operations; this is not Rust versus purely interpreted Python.',
                'Results depend on this machine, build, input, voxel size and filesystem cache; no cold disk or parallel throughput claim.',
                'Peak RSS includes imports, selection and lightweight diagnostics; only stage timings exclude diagnostics.',
                'Process wall measurements have unequal diagnostic work: Python profiles also hash output XYZ, while Rust computes only an index sum. Stage timings exclude both.',
                'Selection output representations and algorithms differ (record indices versus materialized XYZ; hash set versus sorted unique). Results cannot isolate programming language alone.',
                'Correctness of other editing features, statistical/radius outlier removal and non-binary PCD is outside this benchmark.',
                'No repeated export speed comparison; the current editor exports XYZ only while this Rust prototype preserves complete records.',
            ],
            'median': medians, 'warmups': warmups, 'samples': samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--repeats', type=int, default=5)
    parser.add_argument('--voxel', type=float, default=0.05)
    parser.add_argument('--output', type=Path, help='new JSON report file; never overwrites an existing file')
    parser.add_argument('--rust-bin', type=Path, default=ROOT / 'rust/target/release/taffy-pcd-core')
    parser.add_argument('--worker', choices=(*PROFILES[1:], 'validate'), help=argparse.SUPPRESS)
    parser.add_argument('--bounds', nargs=6, type=float, help=argparse.SUPPRESS)
    args = parser.parse_args()
    args.input = args.input.resolve()
    args.rust_bin = args.rust_bin.resolve()
    if args.repeats < 1 or not math.isfinite(args.voxel) or args.voxel <= 0:
        parser.error('--repeats must be positive and --voxel must be finite and positive')
    if args.worker in PROFILES[1:] and args.bounds is None:
        parser.error('internal worker requires --bounds')
    try:
        result = (_validation_worker(args) if args.worker == 'validate' else
                  _python_worker(args) if args.worker else _benchmark(args))
        text = json.dumps(result, indent=None if args.worker else 2, ensure_ascii=False, allow_nan=False)
        if args.output is not None and not args.worker:
            with args.output.open('x', encoding='utf-8') as stream:
                stream.write(text + '\n')
        print(text)
    except (ValueError, OSError, RuntimeError, AssertionError, subprocess.SubprocessError) as exc:
        print(f'benchmark error: {exc}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
