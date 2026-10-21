#!/usr/bin/env python3
"""Step 11 regression: both guarded and planning inventory share the fast Snapper command."""
import ast, pathlib, sys, csv, io, unittest
p=pathlib.Path(sys.argv[1]); source=p.read_text(); tree=ast.parse(source)
function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='legacy_snapper_inventory')
commands=[]
for node in ast.walk(function):
    if not isinstance(node,ast.Call) or not isinstance(node.func,ast.Name) or node.func.id!='run': continue
    arg=node.args[0] if node.args else None
    if not isinstance(arg,ast.List): continue
    vals=[n.value if isinstance(n,ast.Constant) else '<dynamic>' for n in arg.elts]
    if vals and vals[0]=='snapper' and 'list' in vals: commands.append(vals)
assert len(commands)==1, f'Expected exactly one inventory command, found {commands}'
assert commands[0][-1]=='--disable-used-space', commands
assert 'used-space' not in {'type','date','cleanup','number'}
for header in ['config,subvolume,number,default,active,type,pre-number,date,user,cleanup,description,userdata',
               'number,type,date,cleanup,description']:
    rows=list(csv.DictReader(io.StringIO(header+'\n'+(','.join(['@data','/media/usb/@data','19605','no','no','single','','2026-09-28 00:00:38','root','timeline','timeline','']) if header.startswith('config,') else '19605,single,2026-09-28 00:00:38,timeline,pilot')+'\n')))
    columns={k.strip().lower().replace(' ','_') for k in rows[0]}
    assert {'type','date','cleanup','number'}.issubset(columns), columns
assert 'legacy_snapper_inventory(config, mappings)' in source
print('PASS: one common legacy inventory command disables used-space; named CSV headers remain supported')
