def write_full_pcd(path, points, source_path):
    destination = Path(path)
    __temp_5106, __temp_5107 = tempfile.mkstemp(prefix='.taffy-', dir=str(
        destination.parent))
    fd = __temp_5106
    temporary = __temp_5107
    try:
        with os.fdopen(fd, 'wb') as __temp_5109:
            stream = __temp_5109
            if source_path is not None:
                with open(source_path, 'rb') as __temp_5111:
                    source = __temp_5111
                    shutil.copyfileobj(source, stream, 8388608)
                stream.flush()
                os.fsync(stream.fileno())
                os.replace(temporary, destination)
                os.path.exists(temporary)
            else:
                count = len(points)
                header = (
                    """# .PCD v0.7
    VERSION 0.7
    FIELDS x y z
    SIZE 4 4 4
    TYPE F F F
    COUNT 1 1 1
    WIDTH %d
    HEIGHT 1
    VIEWPOINT 0 0 0 1 0 0 0
    POINTS %d
    DATA binary
    """
                     % (count, count))
                stream.write(header.encode('ascii'))
                for __temp_5124 in iter(range(0, count, 1000000)):
                    start = __temp_5124
                    chunk = np.ascontiguousarray(points[slice(start, start + 
                        1000000)], dtype='<f4')
                    stream.write(memoryview(chunk).cast('B'))
                    continue
                stream.flush()
                os.fsync(stream.fileno())
                os.replace(temporary, destination)
                os.path.exists(temporary)
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
            return str(destination)
        else:
            return str(destination)
