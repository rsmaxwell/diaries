#!/usr/bin/env bash
# 0052-DEF formal closeout: documentation/status update and directory move only.
# Host: Windows 11 Cygwin terminal; launch from the Diaries parent repository root.
# Preserves the feature's complete contents, including private evidence/rollback records.
# Standalone non-interactive Bash: fail-fast cannot terminate the calling Cygwin terminal.
set -euo pipefail
  feature='0052-DEF - correct catalogue image content errors'
  source_dir="change-control/in-progress/$feature"
  closed_dir="change-control/complete/$feature"
  handoff='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/reports/0052-READER-VISIBILITY-ACCEPTANCE-HANDOFF-20261123.md'
  evidence="$source_dir/evidence/Step 3/private/20261123T130110Z-consumers/RESULT.txt"

  [[ -d .git || -f .git ]] || { echo 'FAIL: run from the Diaries parent Git checkout root' >&2; exit 1; }
  [[ -f .gitmodules ]] || { echo 'FAIL: expected Diaries parent .gitmodules file' >&2; exit 1; }
  [[ -d "$source_dir" ]] || { echo "FAIL: current in-progress feature directory missing: $source_dir" >&2; exit 1; }
  [[ ! -e "$closed_dir" ]] || { echo "FAIL: destination already exists; stop to avoid merging/overwriting: $closed_dir" >&2; exit 1; }
  [[ -f "$source_dir/README.md" && -f "$source_dir/IMPLEMENTATION-STEPS.md" ]] || {
    echo 'FAIL: feature README or implementation steps not found; do not create an incomplete archive' >&2; exit 1;
  }
  [[ -f "$source_dir/reports/FORMAL-CLOSURE-20261123.md" ]] || {
    echo 'FAIL: formal closure report missing; apply the ZIP before running this script' >&2; exit 1;
  }
  for needed in \
    "$source_dir/reports/STEP3-CLOSURE-READINESS-20261123.md" \
    "$source_dir/reports/STEP3-OWNER-READER-OBSERVATION-20261123.md" \
    "$source_dir/reports/STEP3-CONSOLIDATED-ACCEPTANCE-20261123.md" \
    "$handoff" \
    "$evidence"; do
    [[ -f "$needed" ]] || { echo "FAIL: required acceptance/handoff evidence missing: $needed" >&2; exit 1; }
  done
  grep -Fq 'PASS: 0052 production/development fragment-identity and direct-consumer checks.' "$evidence" || {
    echo 'FAIL: accepted Step 3 database PASS evidence not found' >&2; exit 1;
  }
  grep -Fq 'PASS: production public Reader index and page-owned IMAGE Fragment 2334 HTTP 200.' "$evidence" || {
    echo 'FAIL: accepted Step 3 Reader HTTP PASS evidence not found' >&2; exit 1;
  }
  command -v python3 >/dev/null || { echo 'FAIL: python3 is needed for safe status-document updates' >&2; exit 1; }

  echo '=== Authoritative Windows Diaries checkout ==='
  git branch --show-current
  git rev-parse HEAD
  echo '=== Submodule revisions (read-only) ==='
  git submodule status
  echo '=== Pre-closure 0052 working-tree state ==='
  git status --short -- "$source_dir" "$closed_dir"

  python3 - "$source_dir" "$closed_dir" <<'PYCODE'
import os, pathlib, re, sys
src = pathlib.Path(sys.argv[1])
dst = pathlib.Path(sys.argv[2])
if dst.exists(): raise SystemExit('FAIL: destination exists; not overwriting')
if not dst.parent.is_dir(): raise SystemExit('FAIL: complete directory missing')

notice_readme = ('**CLOSED — 23 November 2026.** Steps 1–3 accepted and formally approved by the '
    'content owner. See [formal closure](reports/FORMAL-CLOSURE-20261123.md). '
    'The public Reader omission of legacy Fragments 84, 598, 599 and 600 is accepted '
    '**only pending 0028-FEAT migration and post-migration visual verification**.')
notice_steps = ('**CLOSED — 23 November 2026.** Steps 1, 2 and 3 closed with the content-owner’s '
    'explicit approval. The existing acceptance qualifications and the mandatory 0028 '
    'handoff are recorded in [formal closure](reports/FORMAL-CLOSURE-20261123.md).')

updates = []
for filename, notice in [('README.md', notice_readme), ('IMPLEMENTATION-STEPS.md', notice_steps)]:
    p = src / filename
    raw = p.read_text(encoding='utf-8')
    s = raw
    # Replace one primary status line when present; leave historical data/evidence intact.
    pattern = r'(?m)^([ \t]*(?:-[ \t]*)?\*\*(?:Status|State):\*\*)[^\n\r]*'
    match = re.search(pattern, s)
    if match:
        s = s[:match.start()] + match.group(1) + ' CLOSED — 23 November 2026 (owner approved; Steps 1–3 closed; 0028 dependency remains open).' + s[match.end():]
    # An unambiguous superseding top-of-file closure note handles newer/different document formats.
    if 'FORMAL-CLOSURE-20261123.md' not in s:
        line_end = s.find('\n')
        if line_end == -1:
            s = s + '\n\n' + notice + '\n'
        else:
            s = s[:line_end+1] + '\n' + notice + '\n' + s[line_end+1:]
    # Correct only the current feature root references in live status docs; never rewrite raw evidence.
    s = s.replace('change-control/in-progress/0052-DEF - correct catalogue image content errors/',
                  'change-control/complete/0052-DEF - correct catalogue image content errors/')
    updates.append((p, s, raw))

# Write documentation files, then move the complete feature tree in one filesystem rename.
# No deletion or overwrite occurs; if a write fails, nothing is moved.
try:
    for p, new_text, old in updates:
        if new_text != old:
            tmp = p.with_name(p.name + '.0052-closure-tmp')
            if tmp.exists(): raise RuntimeError(f'Unsafe pre-existing temporary file: {tmp}')
            tmp.write_text(new_text, encoding='utf-8')
            os.replace(tmp, p)
    src.rename(dst)
except Exception:
    print('FAIL: closeout was not completed. Inspect the source/destination and status docs before retry.', file=sys.stderr)
    raise
print('PASS: owner-approved 0052 closed; all existing files/evidence moved intact to:')
print(f'  {dst}')
print('PASS: README and IMPLEMENTATION-STEPS have a CLOSED status and closure-report reference')
print('0028-FEAT remains IN PROGRESS and was not modified by this helper')
PYCODE

  echo '=== Post-closure Git working-tree state (review; do not auto-stage) ==='
  git status --short -- "$source_dir" "$closed_dir"
  echo 'PASS: 0052 formal closure directory move complete'
