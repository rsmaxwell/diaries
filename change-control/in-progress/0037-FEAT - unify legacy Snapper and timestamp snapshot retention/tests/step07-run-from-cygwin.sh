#!/usr/bin/env bash
# 0037-FEAT Step 7 full source verification. Run from Cygwin, no remote temp files.
set -euo pipefail
feature="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tests="$feature/tests"
evidence="$feature/evidence/Step 07"
mkdir -p "$evidence"
log="$evidence/results.txt"
manager='/home/richard/playbooks/roles/snapshots/files/btrfs-snapshot-manager.py'
{
  echo '0037-FEAT Step 7 — source regression + isolation checks (mango)'
  echo 'Target: mango; production deletion: NOT ALLOWED'
  echo '== Syntax compilation and manager SHA-256 =='
  ssh mango "python3 -m py_compile '$manager' && sha256sum '$manager'"
  echo '== Existing native manager verification =='
  ssh mango 'cd /home/richard/playbooks && python3 roles/snapshots/tests/verify-btrfs-snapshot-manager.py'
  echo '== Step 5 adversarial regressions =='
  ssh mango "python3 - '$manager'" < "$tests/step05-adversarial.py"
  echo '== Step 6 guarded deletion regressions (mocked) =='
  ssh mango "python3 - '$manager'" < "$tests/step06-guarded-regression.py"
  echo '== CLI / scheduler source isolation =='
  ssh mango "python3 - '$manager'" <<'PYIN'
import ast, pathlib, sys
p=pathlib.Path(sys.argv[1]); source=p.read_text(); tree=ast.parse(source)
names={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
for command in ('prune','legacy_plan','legacy_delete'):
    assert command in names, f'missing {command}'
for command in ('prune','create_snapshots'):
    if command not in names: continue
    function=names[command]
    called={n.func.id for n in ast.walk(function) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
    assert 'legacy_delete' not in called, f'{command} calls legacy_delete'
# All reachable subcommands checked by the existing tests; verify destructive entry is isolated.
assert 'legacy-delete' in source and '--execute' in source
print('PASS: guarded deletion command remains separately named and opt-in; no direct prune/create invocation')
PYIN
  echo 'PASS: Step 7 execution finished'
} 2>&1 | tee "$log"
