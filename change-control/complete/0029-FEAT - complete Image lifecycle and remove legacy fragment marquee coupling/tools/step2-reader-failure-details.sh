#!/usr/bin/env bash
# Run in Windows Cygwin from the Diaries parent repository root.
# Read existing JUnit XML from previous reader run. No builds, DB changes or network access.
feature="change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling"
mkdir -p "$feature/evidence/step-2-build"
python - "$feature/evidence/step-2-build/reader-failure-details.txt" <<'PY2'
import pathlib,sys,xml.etree.ElementTree as ET
out=pathlib.Path(sys.argv[1]); root=pathlib.Path('diaries-web/build/test-results/test')
lines=[]
for p in sorted(root.glob('TEST-*.xml')):
 try: r=ET.parse(p).getroot()
 except Exception as exc: lines.append(f'{p}: parse error {exc}');continue
 for testcase in r.iter('testcase'):
  for err in list(testcase):
   if err.tag in ('failure','error'):
    lines.extend([f'FILE: {p}',f'CASE: {testcase.get("classname")} :: {testcase.get("name")}',f'MESSAGE: {err.get("message","")}',(err.text or '')[:5000],'-'*72])
content='\n'.join(lines) if lines else 'No JUnit failure XML found. Run reader tests first.'
out.write_text(content,encoding='utf-8')
print(content[:25000]);print(f'\nSaved {out}')
PY2
