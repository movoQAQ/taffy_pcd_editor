"""Reviewed partial source recovery from v1.2 bytecode. No bytecode fallback.

range_mask/points_inside_region/fmt_number: depyf output, with defaults restored.
write_full_pcd/available_memory_bytes: reconstructed against disassembly.
This is not the complete editor.
"""
import os
import shutil
import tempfile
from pathlib import Path
import numpy as np

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
