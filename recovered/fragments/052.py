# Source Generated with Decompyle++
# File: 052.pyc (Python 3.10)

destination = Path(path)
(fd, temporary) = tempfile.mkstemp('.taffy-', str(destination.parent), **('prefix', 'dir'))

try:
    with os.fdopen(fd, 'wb') as stream:
        if source_path is not None:
            with open(source_path, 'rb') as source:
                shutil.copyfileobj(source, stream, 8388608)
                None(None, None, None)
            with None:
                if not None:
                    pass
        else:
            count = len(points)
            header = '# .PCD v0.7\nVERSION 0.7\nFIELDS x y z\nSIZE 4 4 4\nTYPE F F F\nCOUNT 1 1 1\nWIDTH %d\nHEIGHT 1\nVIEWPOINT 0 0 0 1 0 0 0\nPOINTS %d\nDATA binary\n' % (count, count)
            stream.write(header.encode('ascii'))
            for start in range(0, count, 1000000):
                chunk = np.ascontiguousarray(points[start:start + 1000000], '<f4', **('dtype',))
                stream.write(memoryview(chunk).cast('B'))
    stream.flush()
    os.fsync(stream.fileno())
finally:
    None(None, None, None)
with None:
    if not None:
        pass

os.replace(temporary, destination)
:
    destination = Path(path)
    (fd, temporary) = tempfile.mkstemp('.taffy-', str(destination.parent), **('prefix', 'dir'))
    
    try:
        with os.fdopen(fd, 'wb') as stream:
            if source_path is not None:
                with open(source_path, 'rb') as source:
                    shutil.copyfileobj(source, stream, 8388608)
                    None(None, None, None)
                with None:
                    if not None:
                        pass
            else:
                count = len(points)
                header = '# .PCD v0.7\nVERSION 0.7\nFIELDS x y z\nSIZE 4 4 4\nTYPE F F F\nCOUNT 1 1 1\nWIDTH %d\nHEIGHT 1\nVIEWPOINT 0 0 0 1 0 0 0\nPOINTS %d\nDATA binary\n' % (count, count)
                stream.write(header.encode('ascii'))
                for start in range(0, count, 1000000):
                    chunk = np.ascontiguousarray(points[start:start + 1000000], '<f4', **('dtype',))
                    stream.write(memoryview(chunk).cast('B'))
        stream.flush()
        os.fsync(stream.fileno())
    finally:
        None(None, None, None)
    with None:
        if not None:
            pass

    os.replace(temporary, destination)
    
