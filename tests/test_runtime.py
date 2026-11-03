import importlib.util
from importlib.machinery import SourcelessFileLoader
from pathlib import Path
import numpy as np
import pytest
from scipy.spatial import ConvexHull

@pytest.fixture(scope='session')
def app_module():
    path = Path(__file__).resolve().parents[1] / 'original/main.pyc'
    loader = SourcelessFileLoader('taffy_original', str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module

def test_format(app_module):
    assert app_module.fmt_number(1234567) == '1,234,567'

def test_range_mask_chunk_boundary(app_module):
    points = np.zeros((1000003, 3), dtype=np.float32)
    points[-2] = [2, 0, 0]
    points[-1] = [-1, 1, 1]
    result = app_module.range_mask(points, {a: (-1, 1) for a in 'xyz'})
    assert result.shape == (len(points),)
    assert result.sum() == len(points) - 1
    assert not result[-2] and result[-1]

def test_convex_region(app_module):
    vertices = np.array([[x,y,z] for x in (-1,1) for y in (-1,1) for z in (-1,1)], dtype=float)
    hull = ConvexHull(vertices)
    points = np.array([[0,0,0], [1,1,1], [2,0,0], [-.5,0,0]])
    bounds = (vertices.min(0), vertices.max(0))
    assert app_module.points_inside_region(points,hull.equations,bounds).tolist() == [True,True,False,True]
    visible = np.array([[0,1],[-1,1],[-1,1]])
    assert app_module.points_inside_region(points,hull.equations,bounds,visible).tolist() == [True,True,False,False]

@pytest.mark.parametrize('count', [0, 4, 1000003])
def test_binary_pcd_roundtrip(app_module,tmp_path,count):
    points = np.random.default_rng(7).normal(size=(count,3)).astype(np.float32)
    path = tmp_path / 'roundtrip.pcd'
    app_module.write_full_pcd(path, points)
    loaded = app_module.load_full_xyz(path)
    np.testing.assert_array_equal(loaded, points)
    assert not list(tmp_path.glob('.taffy-*'))

def test_original_file_copy(app_module,tmp_path):
    source = tmp_path/'source.pcd'
    target = tmp_path/'copy.pcd'
    app_module.write_full_pcd(source,np.array([[1,2,3]],dtype=np.float32))
    app_module.write_full_pcd(target,source_path=source)
    assert target.read_bytes() == source.read_bytes()
