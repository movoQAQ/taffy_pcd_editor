"""Decompile original code objects with depyf; does not execute target code."""
import ast, json, marshal, types
from pathlib import Path
import depyf
root=Path(__file__).resolve().parents[1]
co=marshal.loads((root/'original/main.pyc').read_bytes()[16:])
out=root/'recovered/depyf'
out.mkdir(exist_ok=True)
rows=[]
def visit(code,parent):
    name=parent+'.'+code.co_name
    ident=f'{len(rows):03d}'
    row={'id':ident,'name':name}
    rows.append(row)
    try:
        source=depyf.decompile(code)
        (out/f'{ident}.py').write_text(source)
        compile(source, str(out/f'{ident}.py'), "exec")
        row['status']='compile_ok'
    except Exception as e:
        row['status']='failed'
        row['error']=str(e)
    for c in code.co_consts:
        if isinstance(c,types.CodeType): visit(c,name)
visit(co,'')
(root/'analysis/depyf-status.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False))
from collections import Counter
print(Counter(r['status'] for r in rows))
