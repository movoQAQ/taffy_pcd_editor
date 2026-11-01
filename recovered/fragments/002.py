# Source Generated with Decompyle++
# File: 002.pyc (Python 3.10)

rng = np.random.default_rng(18)
count = 52000
x = rng.uniform(-42, 42, count)
y = rng.uniform(-31, 31, count)
road = (np.abs(y - 2) < 2.4) | (np.abs(x + 8) < 2.1)
terrain_z = 0.32 * np.sin(x / 8) + 0.22 * np.cos(y / 7) + rng.normal(0, 0.09, count)
ground = np.column_stack((x[~road], y[~road], terrain_z[~road]))
parts = [
    ground]
buildings = [
    (-29, -20, -22, -12, 8),
    (-16, -7, -22, -14, 13),
    (1, 10, -23, -14, 10),
    (18, 28, -21, -11, 16),
    (-29, -20, 12, 21, 12),
    (-12, -3, 13, 22, 18),
    (5, 15, 13, 22, 9),
    (23, 32, 10, 20, 14)]
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
    parts.append(np.column_stack((rng.uniform(x0, x1, roof_count), rng.uniform(y0, y1, roof_count), rng.normal(height, 0.08, roof_count))))
return np.concatenate(parts).astype(np.float32)
