#!/usr/bin/env bash
set -euo pipefail
feature="change-control/in-progress/0037-FEAT - unify legacy Snapper and timestamp snapshot retention"
if [[ ! -d "$feature" ]]; then
  echo "ERROR: Run from the Diaries repository root in Cygwin" >&2; exit 2
fi
out="$feature/evidence/Step 12/qgroup-preflight"
mkdir -p "$out"
# Every remote command is observational. Do not add clear-stale, rescan, or destroy here.
capture() {
  local name="$1"; shift
  echo "Capturing $name on mars"
  if ssh mars "$@" >"$out/$name.txt" 2>&1; then
    echo "exit=0" >>"$out/COMMAND-RESULTS.txt"
  else
    local ec=$?
    echo "FAILED $name exit=$ec" >&2
    echo "$name exit=$ec" >>"$out/COMMAND-RESULTS.txt"
    return "$ec"
  fi
}
: >"$out/COMMAND-RESULTS.txt"
capture host 'hostname; date -u +%Y-%m-%dT%H:%M:%SZ; uname -r; btrfs --version'
capture mount 'findmnt -T /media/usb -o TARGET,SOURCE,FSTYPE,OPTIONS; sudo btrfs filesystem show /media/usb'
capture capabilities 'btrfs qgroup help 2>&1 || btrfs qgroup 2>&1 || true'
capture qgroups 'sudo timeout 120s btrfs qgroup show /media/usb'
capture qgroups-detailed 'sudo timeout 120s btrfs qgroup show -reF /media/usb'
capture device-stats 'sudo btrfs device stats /media/usb'
capture native-state 'sudo btrfs-snapshot-manager status; sudo btrfs-snapshot-manager prune --dry-run; sudo btrfs-snapshot-manager hold-list'
capture legacy-state 'sudo timeout 90s btrfs-snapshot-manager legacy-plan --legacy-map root=root --legacy-map @data=@data'
capture timers 'systemctl list-timers --all --no-pager | grep -E "snapper|btrfs-snapshot|diaries" || true'
capture processes 'ps -eo pid,ppid,stat,etime,args | grep -E "[s]napper|[b]trfs (send|receive)|[b]trfs-snapshot-manager|[d]iaries.*(push|pull)|[b]trfs quota" || true'
capture kernel 'sudo journalctl -k --since "2026-10-20 06:00:00" --no-pager | grep -Ei "btrfs|usb|I/O error|blocked for|hung task|reset|timeout" || true'
python3 - "$out/qgroups.txt" "$out/qgroup-summary.txt" <<'PYTHON'
import re,sys
from pathlib import Path
p=Path(sys.argv[1]); output=Path(sys.argv[2])
lines=p.read_text(errors='replace').splitlines()
rows=[line for line in lines if re.match(r'^\s*\d+/\d+\s+',line)]
stale=[line for line in rows if re.search(r'<stale>\s*$',line)]
under=[line for line in rows if re.search(r'<under deletion>\s*$',line)]
active=[line for line in rows if line not in stale and line not in under]
nonzero=[]
for line in stale:
    cols=line.split()
    if len(cols)<4 or cols[1]!='0.00B' or cols[2]!='0.00B':nonzero.append(line)
summary=f'rows_total={len(rows)}\nstale={len(stale)}\nunder_deletion={len(under)}\nnon_stale={len(active)}\nstale_nonzero_usage={len(nonzero)}\n'
output.write_text(summary)
print(summary,end='')
if nonzero:
    Path(sys.argv[2]).with_name('stale-nonzero-examples.txt').write_text('\n'.join(nonzero[:40])+'\n')
PYTHON
(cd "$out" && sha256sum *.txt > SHA256SUMS.txt)
echo "PASS: read-only Step 12 qgroup preflight captured under $out"
echo 'No quota metadata changes, snapshot changes, or approval performed.'
