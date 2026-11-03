"""Differential checks: recovered Python source versus original bytecode."""
import importlib.util
from pathlib import Path
import numpy as np
import pytest
from scipy.spatial import ConvexHull
from test_runtime import app_module

@pytest.fixture(scope='module')
def source():
    path=Path(__file__).resolve().parents[1]/'recovered/source/core.py'
    spec=importlib.util.spec_from_file_location('recovered_core',path)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

@pytest.mark.parametrize('count',[0, 37, 1000003])
def test_ranges(source,app_module,count):
    p=np.random.default_rng(6).normal(size=(count,3)).astype(np.float32)
    for ranges in ({a:(-1,1) for a in 'xyz'}, {a:(2,-2) for a in 'xyz'}):
        np.testing.assert_array_equal(source.range_mask(p,ranges),app_module.range_mask(p,ranges))

@pytest.mark.parametrize('visible',[None,np.array([[-.3,.4],[-.5,.6],[-.7,.8]])])
def test_hull(source,app_module,visible):
    rng=np.random.default_rng(8)
    vertices=rng.normal(size=(30,3))
    hull=ConvexHull(vertices)
    p=rng.normal(size=(250003,3))
    bounds=vertices.min(0),vertices.max(0)
    np.testing.assert_array_equal(source.points_inside_region(p,hull.equations,bounds,visible),app_module.points_inside_region(p,hull.equations,bounds,visible))

@pytest.mark.parametrize('count',[0,8,1000003])
def test_write_exact_bytes(source,app_module,tmp_path,count):
    p=np.random.default_rng(5).normal(size=(count,3))
    a,b=tmp_path/'original.pcd',tmp_path/'source.pcd'
    assert app_module.write_full_pcd(a,p)==str(a)
    assert source.write_full_pcd(b,p)==str(b)
    assert a.read_bytes()==b.read_bytes()
    np.testing.assert_array_equal(app_module.load_full_xyz(b),p.astype(np.float32))
    source.write_full_pcd(b,source_path=a)
    assert a.read_bytes()==b.read_bytes()

@pytest.mark.parametrize('which',['source','original'])
def test_write_failure_cleanup(source,app_module,tmp_path,which):
    m=source if which=='source' else app_module
    dest=tmp_path/'preserve.pcd'
    dest.write_bytes(b'preserve existing data')
    with pytest.raises(FileNotFoundError):
        m.write_full_pcd(dest,source_path=tmp_path/'missing')
    assert dest.read_bytes()==b'preserve existing data'
    assert not list(tmp_path.glob('.taffy-*'))

def test_memory(source,app_module,monkeypatch):
    import io
    monkeypatch.setattr('builtins.open',lambda *a,**kw: io.StringIO('MemTotal: 999 kB\nMemAvailable: 123 kB\n'))
    assert source.available_memory_bytes()==app_module.available_memory_bytes()==123*1024

def test_format(source,app_module):
    for value in (-12345,0,1234567,1.5):
        assert source.fmt_number(value)==app_module.fmt_number(value)


def test_demo_cloud(source, app_module):
    np.testing.assert_array_equal(source.make_demo_cloud(), app_module.make_demo_cloud())


@pytest.mark.parametrize('count', [0, 11, 1500001])
def test_load_binary(source, app_module, tmp_path, count):
    points = np.random.default_rng(19).normal(size=(count, 3)).astype(np.float32)
    path = tmp_path / 'binary.pcd'
    app_module.write_full_pcd(path, points)
    full = source.load_full_xyz(path)
    expected = app_module.load_full_xyz(path)
    np.testing.assert_array_equal(full, expected)
    np.testing.assert_array_equal(full, points)
    assert full.dtype == expected.dtype and full.strides == expected.strides
    assert full.flags.writeable == expected.flags.writeable
    actual = source.load_pcd_data(path)
    original = app_module.load_pcd_data(path)
    for a, b in zip(actual, original):
        np.testing.assert_array_equal(a, b)
    assert actual[2] == count
    assert len(actual[0]) <= source.MAX_RENDER_POINTS == app_module.MAX_RENDER_POINTS


@pytest.mark.parametrize('layout', ['xyz_extra', 'reordered', 'default_count', 'width_height'])
def test_load_pcd_field_layouts(source, app_module, tmp_path, layout):
    if layout == 'reordered':
        fields, sizes, types, counts = 'z tag x y', '8 2 4 4', 'F U I F', '1 1 1 1'
        dtype = [('z', '<f8'), ('tag', '<u2'), ('x', '<i4'), ('y', '<f4')]
    else:
        fields, sizes, types, counts = 'x y z tag', '4 4 4 2', 'F F F U', '1 1 1 3'
        dtype = [('x', '<f4'), ('y', '<f4'), ('z', '<f4'), ('tag', '<u2', (3,))]
        if layout == 'default_count':
            dtype[-1] = ('tag', '<u2')
    records = np.zeros(12, dtype=dtype)
    for i, axis in enumerate('xyz'):
        records[axis] = np.arange(12) + i
    header = f'# test\n\nVERSION 0.7\nFIELDS {fields}\nSIZE {sizes}\nTYPE {types}\n'
    if layout != 'default_count':
        header += f'COUNT {counts}\n'
    header += 'WIDTH 4\nHEIGHT 3\n'
    if layout != 'width_height':
        header += 'POINTS 12\n'
    path = tmp_path / 'layout.pcd'
    path.write_bytes((header + 'DATA binary\n').encode('ascii') + records.tobytes())
    for name in ('load_pcd_data', 'load_full_xyz'):
        actual = getattr(source, name)(path)
        original = getattr(app_module, name)(path)
        if isinstance(actual, tuple):
            for a, b in zip(actual, original):
                np.testing.assert_array_equal(a, b)
        else:
            np.testing.assert_array_equal(actual, original)
            assert actual.strides == original.strides
            assert actual.flags.writeable == original.flags.writeable


@pytest.mark.parametrize('encoding', ['ascii', 'binary_compressed'])
def test_load_open3d_fallback(source, app_module, tmp_path, encoding):
    import open3d as o3d
    points = np.random.default_rng(23).normal(size=(101, 3))
    points[-1, 0] = np.nan
    points[-2, 2] = np.inf
    cloud = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(points))
    path = tmp_path / f'{encoding}.pcd'
    assert o3d.io.write_point_cloud(str(path), cloud, write_ascii=encoding == 'ascii',
                                    compressed=encoding == 'binary_compressed')
    np.testing.assert_array_equal(source.load_full_xyz(path), app_module.load_full_xyz(path))
    actual, original = source.load_pcd_data(path), app_module.load_pcd_data(path)
    for a, b in zip(actual, original):
        np.testing.assert_array_equal(a, b)
    assert actual[2] == 99


@pytest.mark.parametrize('content', [
    b'', b'FIELDS x y z\n', b'\xff\nDATA binary\n',
    b'FIELDS x y\nDATA binary\n',
    b'FIELDS x y z\nSIZE 4 4 4\nTYPE F F F\nPOINTS 2\nDATA binary\n',
    b'FIELDS x y z\nSIZE 3 4 4\nTYPE F F F\nPOINTS 1\nDATA binary\n',
])
def test_load_errors(source, app_module, tmp_path, content):
    path = tmp_path / 'invalid.pcd'
    path.write_bytes(content)
    with pytest.raises(Exception) as expected:
        app_module.load_full_xyz(path)
    with pytest.raises(type(expected.value)) as actual:
        source.load_full_xyz(path)
    assert str(actual.value) == str(expected.value)


@pytest.mark.parametrize('spacing', [2.0, 0.02])
def test_completion_seeded(source, app_module, monkeypatch, spacing):
    # Fix only the random input; both real implementations perform all sampling.
    default_rng = np.random.default_rng
    monkeypatch.setattr(np.random, 'default_rng', lambda: default_rng(41))
    vertices = np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], dtype=float)
    equations = ConvexHull(vertices).equations
    points = np.array([[5, 6, 7]], dtype=np.float32)
    ranges = {a: (-0.75, 0.75) for a in 'xyz'}
    actual, count = source.complete_region(points, equations, vertices, ranges, spacing)
    expected, expected_count = app_module.complete_region(points, equations, vertices, ranges, spacing)
    assert count == expected_count == (300 if spacing == 2.0 else 250000)
    np.testing.assert_array_equal(actual, expected)
    np.testing.assert_array_equal(actual[:len(points)], points)
    assert np.all(np.abs(actual[len(points):]) <= 0.75)


@pytest.mark.parametrize('failure', ['memory', 'no_overlap', 'no_samples'])
def test_completion_errors(source, app_module, monkeypatch, failure):
    vertices = np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], dtype=float)
    equations = ConvexHull(vertices).equations
    ranges = {a: (-1, 1) for a in 'xyz'}
    if failure == 'memory':
        monkeypatch.setattr(source, 'available_memory_bytes', lambda: 1)
        monkeypatch.setattr(app_module, 'available_memory_bytes', lambda: 1)
    elif failure == 'no_overlap':
        ranges['x'] = (2, 3)
    else:
        equations = np.array([[0, 0, 0, 1]])
    args = (np.empty((0, 3), np.float32), equations, vertices, ranges, 1)
    with pytest.raises((ValueError, MemoryError)) as expected:
        app_module.complete_region(*args)
    with pytest.raises(type(expected.value)) as actual:
        source.complete_region(*args)
    assert str(actual.value) == str(expected.value)
