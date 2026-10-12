import struct, sys, os
def entries(p):
    f = open(p, 'rb'); h = f.read(16)
    assert h[:4] == b'VPVP'
    _, off, n = struct.unpack('<3i', h[4:])
    f.seek(off); path = []
    for _ in range(n):
        o, s, name, ts = struct.unpack('<ii32si', f.read(44))
        name = name.split(b'\0')[0].decode('latin1')
        if s == 0 and ts == 0:
            if name == '..': path.pop()
            else: path.append(name)
            continue
        yield '/'.join(path + [name]), o, s
if __name__ == '__main__':
    p = sys.argv[1]; want = sys.argv[2:]
    for name, o, s in entries(p):
        if not want:
            print(name, s)
        elif any(w.lower() in name.lower() for w in want):
            f = open(p, 'rb'); f.seek(o); d = f.read(s)
            out = os.path.join(os.environ['OUTD'], os.path.basename(name)); open(out, 'wb').write(d); print('->', out, s)
