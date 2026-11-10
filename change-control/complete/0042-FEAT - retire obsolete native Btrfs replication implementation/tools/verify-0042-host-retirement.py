#!/usr/bin/env python3
"""Read-only 0042 host verification against accepted 0040 exact candidate paths."""
import json, subprocess, sys
from pathlib import Path

feature=Path(__file__).resolve().parents[1]
manifest=json.loads(Path(__file__).with_name('accepted-0040-host-retirement-paths.json').read_text())
hosts=manifest['hosts']
for host in ('mars','backup'):
    paths=hosts[host]
    assert all(p.startswith(('/usr/local/bin/','/usr/local/libexec/','/usr/local/sbin/','/etc/systemd/system/')) for p in paths), host
    remote='''import json, os, sys
paths=json.load(sys.stdin)
present=[p for p in paths if os.path.lexists(p)]
print(json.dumps({'present':present,'expected_absent':len(paths)}))
sys.exit(1 if present else 0)
'''
    cp=subprocess.run(['ssh',host,'sudo -n python3 -c '+__import__('shlex').quote(remote)],
                      input=json.dumps(paths),text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    print(host,cp.stdout.strip())
    if cp.returncode:
        print('FAIL:',host,cp.stderr.strip(),file=sys.stderr)
        sys.exit(1)
    status=subprocess.run(['ssh',host,'sudo -n /usr/local/bin/btrfs-simplified-replication '+('sender' if host=='mars' else 'receiver')+' status'],
                          capture_output=True,text=True)
    if status.returncode:
        print('FAIL: simplified status on',host,status.stderr.strip(),file=sys.stderr)
        sys.exit(1)
    print('simplified_status',host,status.stdout.strip())
print('PASS: obsolete 0040 host paths still absent; simplified status working on both hosts')
