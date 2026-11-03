"""Black-box NumPy differential tests for the optional Rust prototype.

Build once with `cargo build --release --manifest-path rust/Cargo.toml`.
The ordinary Python suite remains usable without a Rust build.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
BINARY = Path(os.environ.get('TAFFY_RUST_BIN', ROOT / 'rust/target/release/taffy-pcd-core'))
pytestmark = pytest.mark.skipif(not BINARY.is_file(), reason='build rust/target/release/taffy-pcd-core first')

XYZ = np.dtype([('x', '<f4'), ('y', '<f4'), ('z', '<f4')])
EXTRA = np.dtype([('tag', '<u2'), ('z', '<f4'), ('histogram', 'u1', (3,)),
                  ('x', '<f8'), ('normal', '<f4', (3,)), ('y', '<f4'), ('intensity', 'u1')])


def write_pcd(path, records, *, omit_count=False):
    sizes, kinds, counts = [], [], []
    for name in records.dtype.names:
        dtype = records.dtype.fields[name][0]
        base, shape = dtype.subdtype or (dtype, ())
        sizes.append(str(base.itemsize))
        kinds.append(base.kind.upper())
        counts.append(str(int(np.prod(shape)) if shape else 1))
    lines = ['# differential fixture', 'VERSION 0.7',
             'FIELDS ' + ' '.join(records.dtype.names), 'SIZE ' + ' '.join(sizes),
             'TYPE ' + ' '.join(kinds)]
    if not omit_count:
        lines.append('COUNT ' + ' '.join(counts))
    lines.extend([f'WIDTH {len(records)}', 'HEIGHT 1', 'VIEWPOINT 1 2 3 1 0 0 0',
                  f'POINTS {len(records)}', 'DATA binary'])
    path.write_bytes(('\n'.join(lines) + '\n').encode('ascii') + records.tobytes())


def read_payload(path):
    header = {}
    with path.open('rb') as stream:
        while True:
            parts = stream.readline().decode('ascii').strip().split()
            if not parts or parts[0].startswith('#'):
                continue
            header[parts[0]] = parts[1:]
            if parts[0] == 'DATA':
                return header, stream.read()


def xyz(records):
    return np.column_stack([records[axis] for axis in 'xyz']).astype(np.float32)


def reference_indices(records, voxel, bounds):
    points = xyz(records)
    in_range = np.all((points >= np.asarray(bounds, dtype=np.float32)[:, 0])
                      & (points <= np.asarray(bounds, dtype=np.float32)[:, 1]), axis=1)
    scope = np.flatnonzero(in_range)
    # Independent NumPy implementation, not a reimplementation of Rust's hash set.
    cells = np.floor(points[scope] / np.float32(voxel)).astype(np.int32)
    _, indices = np.unique(cells, axis=0, return_index=True)
    return np.concatenate([np.flatnonzero(~in_range), scope[np.sort(indices)]]), int(in_range.sum())


def run_cli(source, *arguments):
    return subprocess.run([str(BINARY), str(source), *map(str, arguments)], capture_output=True,
                          text=True, timeout=15)


def assert_matches(source, records, output, bounds=None, voxel=0.05):
    original = hashlib.sha256(source.read_bytes()).hexdigest()
    arguments = ['--voxel', format(voxel, '.17g'), '--output', str(output)]
    if bounds is not None:
        arguments.extend(['--bounds', *[format(value, '.17g') for pair in bounds for value in pair]])
    points = xyz(records)
    effective_bounds = (bounds if bounds is not None else
                        np.column_stack([points.min(0), points.max(0)]).tolist() if len(points) else
                        [[0, 0], [0, 0], [0, 0]])
    indices, scoped = reference_indices(records, voxel, effective_bounds)
    result = run_cli(source, *arguments)
    assert result.returncode == 0, result.stderr
    metrics = json.loads(result.stdout)
    assert metrics['input_points'] == len(records)
    assert metrics['in_range_points'] == scoped
    assert metrics['output_points'] == len(indices)
    assert metrics['record_bytes'] == records.dtype.itemsize
    assert metrics['index_sum'] == int(indices.sum(dtype=np.uint64))
    source_header, _ = read_payload(source)
    output_header, payload = read_payload(output)
    for key in ('FIELDS', 'SIZE', 'TYPE', 'VIEWPOINT'):
        assert output_header[key] == source_header[key]
    assert output_header['COUNT'] == source_header.get('COUNT', ['1'] * len(records.dtype.names))
    assert output_header['WIDTH'] == [str(len(indices))]
    assert output_header['HEIGHT'] == ['1']
    assert output_header['POINTS'] == [str(len(indices))]
    assert payload == records[indices].tobytes()  # Every field, not only XYZ.
    np.testing.assert_array_equal(xyz(np.frombuffer(payload, dtype=records.dtype)), points[indices])
    assert hashlib.sha256(source.read_bytes()).hexdigest() == original
    for name in ('load_scan_ms', 'filter_ms', 'write_ms', 'work_ms'):
        assert np.isfinite(metrics[name]) and metrics[name] >= 0
    return metrics


def test_reordered_mixed_width_xyz_extra_count_fields_and_voxel_boundaries(tmp_path):
    epsilon_left = np.nextafter(np.float32(0.05), np.float32(0))
    epsilon_negative = np.nextafter(np.float32(-0.05), np.float32(-1))
    coordinates = np.array([[0, 0, 0], [0.01, 0, 0], [-0.01, 0, 0], [-0.05, 0, 0],
                            [epsilon_negative, 0, 0], [epsilon_left, 0, 0], [0.05, 0, 0],
                            [1, 2, 3], [1.01, 2, 3], [-1, -1, -1]], dtype=np.float32)
    records = np.zeros(len(coordinates), dtype=EXTRA)
    for index, axis in enumerate('xyz'):
        records[axis] = coordinates[:, index]
    records['tag'] = np.arange(len(records), dtype=np.uint16) + 100
    records['histogram'] = np.arange(len(records) * 3, dtype=np.uint8).reshape(-1, 3)
    records['normal'] = np.arange(len(records) * 3, dtype=np.float32).reshape(-1, 3) / 7
    records['intensity'] = np.arange(len(records), dtype=np.uint8)
    source = tmp_path / 'mixed.pcd'
    write_pcd(source, records)
    assert_matches(source, records, tmp_path / 'filtered.pcd', [[-0.06, 0.06], [-1, 3], [-1, 3]])


@pytest.mark.parametrize('mode', ['full', 'empty-range', 'empty-cloud', 'count-default'])
def test_default_range_empty_cases_and_default_counts(tmp_path, mode):
    coordinates = [] if mode == 'empty-cloud' else [(0, 0, 0), (0.01, 0, 0), (1, 1, 1)]
    records = np.array(coordinates, dtype=XYZ)
    source = tmp_path / 'source.pcd'
    write_pcd(source, records, omit_count=mode == 'count-default')
    bounds = [[10, 11], [10, 11], [10, 11]] if mode == 'empty-range' else None
    metrics = assert_matches(source, records, tmp_path / 'output.pcd', bounds)
    if mode == 'empty-cloud':
        assert metrics['bounds'] == [[0, 0], [0, 0], [0, 0]]


@pytest.mark.parametrize('change', ['truncated', 'extra-byte', 'missing-z', 'integer-x',
                                  'duplicate-field', 'count-zero', 'ascii', 'bad-width',
                                  'nan-xyz', 'infinite-xyz'])
def test_invalid_pcd_is_rejected_without_creating_output(tmp_path, change):
    records = np.array([(0, 0, 0), (1, 1, 1)], dtype=XYZ)
    if change == 'nan-xyz':
        records['x'][0] = np.nan
    elif change == 'infinite-xyz':
        records['z'][0] = np.inf
    source = tmp_path / 'bad.pcd'
    write_pcd(source, records)
    content = source.read_bytes()
    replacements = {'missing-z': (b'FIELDS x y z', b'FIELDS x y q'),
                    'integer-x': (b'TYPE F F F', b'TYPE I F F'),
                    'duplicate-field': (b'FIELDS x y z', b'FIELDS x x z'),
                    'count-zero': (b'COUNT 1 1 1', b'COUNT 1 0 1'),
                    'ascii': (b'DATA binary', b'DATA ascii'),
                    'bad-width': (b'WIDTH 2', b'WIDTH 3')}
    if change in replacements:
        content = content.replace(*replacements[change], 1)
    elif change == 'truncated':
        content = content[:-1]
    elif change == 'extra-byte':
        content += b'X'
    source.write_bytes(content)
    output = tmp_path / 'must-not-exist.pcd'
    result = run_cli(source, '--output', output)
    assert result.returncode == 2
    assert result.stderr.strip()
    assert not result.stdout.strip()
    assert not output.exists()
    assert source.read_bytes() == content


@pytest.mark.parametrize('kind', ['input', 'existing', 'symlink', 'hardlink'])
def test_output_never_overwrites_source_or_existing_file(tmp_path, kind):
    source = tmp_path / 'source.pcd'
    write_pcd(source, np.array([(0, 0, 0), (0.01, 0, 0)], dtype=XYZ))
    before = source.read_bytes()
    output = source if kind == 'input' else tmp_path / 'output.pcd'
    if kind == 'existing':
        output.write_bytes(b'keep this file')
    elif kind == 'symlink':
        output.symlink_to(source)
    elif kind == 'hardlink':
        os.link(source, output)
    output_before = output.read_bytes()
    result = run_cli(source, '--output', output)
    assert result.returncode == 2 and result.stderr.strip()
    assert output.read_bytes() == output_before
    assert source.read_bytes() == before
    assert sorted(path.name for path in tmp_path.iterdir()) == (
        ['source.pcd'] if kind == 'input' else ['output.pcd', 'source.pcd'])


@pytest.mark.parametrize('arguments', [('--voxel', '0'), ('--voxel', '-1'), ('--voxel', 'nan'),
                                       ('--voxel', '1e-100'), ('--voxel', '1e-20'),
                                       ('--bounds', '2', '1', '0', '1', '0', '1'),
                                       ('--bounds', '0', 'inf', '0', '1', '0', '1')])
def test_invalid_filter_parameters_are_errors(tmp_path, arguments):
    source = tmp_path / 'source.pcd'
    write_pcd(source, np.array([(1, 1, 1)], dtype=XYZ))
    result = run_cli(source, *arguments)
    assert result.returncode == 2 and result.stderr.strip()
    assert not result.stdout.strip()
