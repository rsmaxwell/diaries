#!/usr/bin/env bash
# Run from the Windows Cygwin Diaries repository root. Read-only; no Gradle rerun.
root='diaries-web/build/test-results/test'
if [ ! -d "$root" ]; then echo "FAIL: missing $root (run reader tests first)" >&2; exit 1; fi
python3 - "$root" <<'PYTHON'
import sys, pathlib, xml.etree.ElementTree as ET
root = pathlib.Path(sys.argv[1])
keys = ('Unhandled HTTP rendering error', 'Unable to render template', 'PebbleException', 'Caused by:', 'Exception', 'ERROR')
found = 0
for f in sorted(root.glob('TEST-*.xml')):
    try: document = ET.parse(f).getroot()
    except ET.ParseError as exc: print(f'ERROR parsing {f}: {exc}'); continue
    for elem in document.iter():
        if elem.tag not in ('system-err', 'system-out'): continue
        lines = (elem.text or '').splitlines()
        for index, line in enumerate(lines):
            if any(k in line for k in keys):
                print(f'\nFILE {f} [{elem.tag}] line {index+1}:')
                print('\n'.join(lines[max(0,index-2):min(len(lines),index+12)]))
                found += 1
                if found >= 20: break
        if found >= 20: break
    if found >= 20: break
if not found:
    print('No rendering exception stacktrace found in the XML system-out/system-err. Re-run one reader HTTP test with --info and capture console logs.')
PYTHON
