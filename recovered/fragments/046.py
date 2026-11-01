# Source Generated with Decompyle++
# File: 046.pyc (Python 3.10)

available = available_memory_bytes()
if available and (len(points) + 250000) * 12 > available * 0.75:
    raise MemoryError('完整点云补全结果超出安全内存预算，请先释放内存后再补全。')
low = None(None, (lambda .0 = None: [ ranges[axis][0] for axis in .0 ])('xyz'))
high = None(None, (lambda .0 = None: [ ranges[axis][1] for axis in .0 ])('xyz'))
if np.any(high <= low):
    raise ValueError('凸包区域与当前 XYZ 范围没有交集。')
box_volume = float(np.prod(high - low))
volume = min(float(ConvexHull(vertices).volume), box_volume)
target = int(np.clip(volume / max(spacing ** 3, 1e-09), 300, 250000))
ratio = max(volume / box_volume, 0.001)
rng = np.random.default_rng()
batches = []
remaining = target
for _ in range(16):
    if remaining <= 0:
        pass
    else:
        size = min(max(int((remaining / ratio) * 1.2), 10000), 60000)
        batch = rng.uniform(low, high, (size, 3)).astype(np.float32)
        inside = np.ones(size, bool, **('dtype',))
        for plane in equations:
            inside &= ((batch @ plane[:3]) + plane[3] <= 1e-06)
        accepted = batch[inside][:remaining]
        if len(accepted):
            batches.append(accepted)
            remaining -= len(accepted)
    if not batches:
        raise ValueError('随机采样没有命中凸包区域，请重新计算。')
    candidates = np.concatenate(batches)
    return (np.concatenate((points, candidates)), len(candidates))
