"""Reviewed partial source recovery from v1.2 bytecode. No bytecode fallback.

range_mask/points_inside_region/fmt_number: depyf output, with defaults restored.
write_full_pcd/available_memory_bytes: reconstructed against disassembly.
load_pcd_data/load_full_xyz/complete_region/make_demo_cloud: reviewed against
analysis/round3-python310-disassembly.txt, including fallback and loop branches.
This is not the complete editor.
"""
import os
import shutil
import tempfile
from pathlib import Path
import numpy as np
import open3d as o3d
from scipy.spatial import ConvexHull

MAX_RENDER_POINTS = 1500000


def make_demo_cloud():
    rng = np.random.default_rng(18)
    count = 52000
    x = rng.uniform(-42, 42, count)
    y = rng.uniform(-31, 31, count)
    road = (np.abs(y - 2) < 2.4) | (np.abs(x + 8) < 2.1)
    terrain_z = (0.32 * np.sin(x / 8) + 0.22 * np.cos(y / 7)
                 + rng.normal(0, 0.09, count))
    parts = [np.column_stack((x[~road], y[~road], terrain_z[~road]))]
    buildings = [(-29, -20, -22, -12, 8), (-16, -7, -22, -14, 13),
                 (1, 10, -23, -14, 10), (18, 28, -21, -11, 16),
                 (-29, -20, 12, 21, 12), (-12, -3, 13, 22, 18),
                 (5, 15, 13, 22, 9), (23, 32, 10, 20, 14)]
    for x0, x1, y0, y1, height in buildings:
        n = 1400
        face = rng.integers(0, 4, n)
        bx = rng.uniform(x0, x1, n)
        by = rng.uniform(y0, y1, n)
        bz = rng.uniform(0.15, height, n)
        bx = np.where(face == 0, x0, np.where(face == 1, x1, bx))
        by = np.where(face == 2, y0, np.where(face == 3, y1, by))
        parts.append(np.column_stack((bx, by, bz)))
        roof_count = 350
        parts.append(np.column_stack((rng.uniform(x0, x1, roof_count),
                                     rng.uniform(y0, y1, roof_count),
                                     rng.normal(height, 0.08, roof_count))))
    return np.concatenate(parts).astype(np.float32)


def load_pcd_data(path):
    header = {}
    with open(path, 'rb') as stream:
        while True:
            line = stream.readline()
            if not line:
                raise ValueError('PCD 文件头不完整。')
            parts = line.decode('ascii', errors='strict').strip().split()
            if not parts or parts[0].startswith('#'):
                continue
            header[parts[0].upper()] = parts[1:]
            if parts[0].upper() == 'DATA':
                data_offset = stream.tell()
                break
    fields = header.get('FIELDS', [])
    point_count = int(header.get('POINTS', [0])[0])
    if not point_count:
        point_count = (int(header.get('WIDTH', ['0'])[0])
                       * int(header.get('HEIGHT', ['1'])[0]))
    if header.get('DATA') == ['binary'] and all(key in fields for key in ('x', 'y', 'z')):
        sizes = [int(value) for value in header.get('SIZE', [])]
        types = header.get('TYPE', [])
        counts = [int(value) for value in header.get('COUNT', ['1'] * len(fields))]
        type_map = {('F', 4): '<f4', ('F', 8): '<f8',
                    ('I', 1): 'i1', ('I', 2): '<i2', ('I', 4): '<i4', ('I', 8): '<i8',
                    ('U', 1): 'u1', ('U', 2): '<u2', ('U', 4): '<u4', ('U', 8): '<u8'}
        dtype_fields = []
        for name, size, kind, count in zip(fields, sizes, types, counts):
            dtype = type_map.get((kind, size))
            if dtype is None:
                break
            dtype_fields.append((name, dtype) if count == 1 else (name, dtype, (count,)))
        else:
            records = np.memmap(path, mode='r', dtype=np.dtype(dtype_fields),
                                offset=data_offset, shape=(point_count,))
            stride = max(1, int(np.ceil(point_count / MAX_RENDER_POINTS)))
            display_points = np.column_stack((records['x'][::stride], records['y'][::stride],
                                              records['z'][::stride])).astype(np.float32, copy=False)
            return display_points, display_points[:, 2], point_count
    cloud = o3d.io.read_point_cloud(str(path), remove_nan_points=True, remove_infinite_points=True)
    all_points = np.asarray(cloud.points)
    if not len(all_points):
        raise ValueError('文件中没有有效 XYZ 点。')
    total_points = len(all_points)
    stride = max(1, int(np.ceil(total_points / MAX_RENDER_POINTS)))
    display_points = np.ascontiguousarray(all_points[::stride, :3], dtype=np.float32)
    return display_points, display_points[:, 2], total_points


def load_full_xyz(path):
    header = {}
    with open(path, 'rb') as stream:
        while True:
            line = stream.readline()
            if not line:
                raise ValueError('PCD 文件头不完整。')
            parts = line.decode('ascii', errors='strict').strip().split()
            if not parts or parts[0].startswith('#'):
                continue
            header[parts[0].upper()] = parts[1:]
            if parts[0].upper() == 'DATA':
                offset = stream.tell()
                break
    fields = header.get('FIELDS', [])
    if not all(key in fields for key in ('x', 'y', 'z')):
        raise ValueError('PCD 中缺少 XYZ 字段。')
    count = int(header.get('POINTS', [0])[0])
    if header.get('DATA') == ['binary']:
        sizes = [int(value) for value in header.get('SIZE', [])]
        types = header.get('TYPE', [])
        counts = [int(value) for value in header.get('COUNT', ['1'] * len(fields))]
        type_map = {('F', 4): '<f4', ('F', 8): '<f8',
                    ('I', 1): 'i1', ('I', 2): '<i2', ('I', 4): '<i4', ('I', 8): '<i8',
                    ('U', 1): 'u1', ('U', 2): '<u2', ('U', 4): '<u4', ('U', 8): '<u8'}
        dtype_fields = []
        for name, size, kind, item_count in zip(fields, sizes, types, counts):
            dtype = type_map.get((kind, size))
            if dtype is None:
                raise ValueError(f'不支持 PCD 字段类型：{name}')
            dtype_fields.append((name, dtype) if item_count == 1 else (name, dtype, (item_count,)))
        records = np.memmap(path, mode='r', dtype=np.dtype(dtype_fields), offset=offset, shape=(count,))
        xyz_indices = [fields.index(axis) for axis in 'xyz']
        if xyz_indices == [0, 1, 2] and all(
                types[i] == 'F' and sizes[i] == 4 and counts[i] == 1 for i in xyz_indices):
            return np.ndarray((count, 3), dtype='<f4', buffer=records,
                              strides=(records.dtype.itemsize, 4))
        return np.column_stack((records['x'], records['y'], records['z'])).astype(np.float32, copy=False)
    cloud = o3d.io.read_point_cloud(str(path), remove_nan_points=True, remove_infinite_points=True)
    return np.asarray(cloud.points, dtype=np.float32)


def complete_region(points, equations, vertices, ranges, spacing):
    available = available_memory_bytes()
    if available and (len(points) + 250000) * 12 > available * 0.75:
        raise MemoryError('完整点云补全结果超出安全内存预算，请先释放内存后再补全。')
    low = np.maximum(vertices.min(axis=0), [ranges[axis][0] for axis in 'xyz'])
    high = np.minimum(vertices.max(axis=0), [ranges[axis][1] for axis in 'xyz'])
    if np.any(high <= low):
        raise ValueError('凸包区域与当前 XYZ 范围没有交集。')
    box_volume = float(np.prod(high - low))
    volume = min(float(ConvexHull(vertices).volume), box_volume)
    target = int(np.clip(volume / max(spacing ** 3, 1e-9), 300, 250000))
    ratio = max(volume / box_volume, 0.001)
    rng = np.random.default_rng()
    batches = []
    remaining = target
    for _ in range(16):
        if remaining <= 0:
            break
        size = min(max(int(remaining / ratio * 1.2), 10000), 60000)
        batch = rng.uniform(low, high, (size, 3)).astype(np.float32)
        inside = np.ones(size, dtype=bool)
        for plane in equations:
            inside &= batch @ plane[:3] + plane[3] <= 1e-6
        accepted = batch[inside][:remaining]
        if len(accepted):
            batches.append(accepted)
            remaining -= len(accepted)
    if not batches:
        raise ValueError('随机采样没有命中凸包区域，请重新计算。')
    candidates = np.concatenate(batches)
    return np.concatenate((points, candidates)), len(candidates)

def fmt_number(value):
    return format(value, ',.0f')


def range_mask(points, ranges):
    result = np.ones(len(points), dtype=bool)
    for __temp_5044 in iter(range(0, len(points), 1000000)):
        start = __temp_5044
        chunk = points[slice(start, start + 1000000)]
        inside = result[slice(start, start + len(chunk))]
        for __temp_5047 in iter(enumerate('xyz')):
            __temp_5048, __temp_5049 = __temp_5047
            column = __temp_5048
            axis = __temp_5049
            __temp_5050, __temp_5051 = ranges[axis]
            low = __temp_5050
            high = __temp_5051
            inside &= (chunk[slice(None, None), column] >= low) & (chunk[slice(
                None, None), column] <= high)
            continue
        continue
    return result


def points_inside_region(points, equations, bounds, visible_ranges=None):
    __temp_5157, __temp_5158 = bounds
    low = __temp_5157
    high = __temp_5158
    if visible_ranges is not None:
        low = np.maximum(low, visible_ranges[slice(None, None), 0])
        high = np.minimum(high, visible_ranges[slice(None, None), 1])
    result = np.zeros(len(points), dtype=bool)
    if np.any(low > high):
        return result
    for __temp_5166 in iter(range(0, len(points), 250000)):
        start = __temp_5166
        chunk = points[slice(start, start + 250000)]
        candidates = np.flatnonzero(np.all((chunk >= low) & (chunk <= high),
            axis=1))
        if len(candidates):
            subset = chunk[candidates]
            result[start + candidates] = np.all(subset @ equations[slice(None,
                None), slice(None, 3)].T + equations[slice(None, None), 3] <= 
                1e-06, axis=1)
        continue
    return result


def available_memory_bytes():
    with open('/proc/meminfo', encoding='ascii') as stream:
        for line in stream:
            if line.startswith('MemAvailable:'):
                return int(line.split()[1]) * 1024
    return 0


def write_full_pcd(path, points=None, source_path=None):
    destination = Path(path)
    fd, temporary = tempfile.mkstemp(prefix='.taffy-', dir=str(destination.parent))
    try:
        with os.fdopen(fd, 'wb') as stream:
            if source_path is not None:
                with open(source_path, 'rb') as source:
                    shutil.copyfileobj(source, stream, 8388608)
            else:
                count = len(points)
                header = ('# .PCD v0.7\nVERSION 0.7\nFIELDS x y z\nSIZE 4 4 4\n'
                          'TYPE F F F\nCOUNT 1 1 1\nWIDTH %d\nHEIGHT 1\n'
                          'VIEWPOINT 0 0 0 1 0 0 0\nPOINTS %d\nDATA binary\n') % (count, count)
                stream.write(header.encode('ascii'))
                for start in range(0, count, 1000000):
                    chunk = np.ascontiguousarray(points[start:start + 1000000], dtype='<f4')
                    stream.write(memoryview(chunk).cast('B'))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return str(destination)
