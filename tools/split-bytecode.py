"""Static parsing only. Requires xdis==6.1.8; never executes target code."""
import json
from pathlib import Path
from xdis.load import load_module
from xdis import marsh
import struct
# xdis 6.1.8 marsh writer needs explicit UTF-8 encoding for Unicode constants.
def dump_unicode(self, value):
    data = value.encode("utf-8", "surrogatepass")
    self._write(marsh.TYPE_UNICODE)
    self.w_long(len(data))
    self._write(data)
marsh._Marshaller.dispatch[str] = dump_unicode
root = Path(__file__).resolve().parents[1]
version, timestamp, magic, code, *_ = load_module(str(root / 'original/main.pyc'))
out = root / 'analysis/code-objects'
out.mkdir(exist_ok=True)
rows = []
def visit(co, parent):
    name = parent + '.' + co.co_name
    ident = f'{len(rows):03d}'
    rows.append(dict(id=ident, name=name, line=co.co_firstlineno, args=list(co.co_varnames[:co.co_argcount]), names=list(co.co_names)))
    (out / (ident + ".pyc")).write_bytes(struct.pack("<H2sIII", magic, b"\r\n", 0, timestamp, 0) + marsh.dumps(co, python_version=(3, 10)))
    for c in co.co_consts:
        if hasattr(c, 'co_code'):
            visit(c, name)
visit(code, '')
(root / 'analysis/code-objects.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2))
print(f'Extracted {len(rows)} code objects')
