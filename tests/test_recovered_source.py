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
