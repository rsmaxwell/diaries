#!/usr/bin/env python3
"""Source-only validation for the 0047 operator interface (run against mango clone)."""
from pathlib import Path
import sys,yaml
r=Path(sys.argv[1] if len(sys.argv)>1 else '/home/richard/playbooks')
assert yaml.safe_load((r/'backup-collection.yaml').read_text())[0]['roles']==[{'role':'backup-collection'}]
assert yaml.safe_load((r/'snapshots.yaml').read_text())[0]['roles']==[{'role':'backup-collection'}]
for obsolete in ('local-backup.yaml','remote-backup.yaml','diaries-user-backup-cron.yaml','scripts/local-backup.sh','scripts/remote-backup.sh'):
    assert not (r/obsolete).exists(),obsolete
assert not (r/'roles/local-backup').exists()
assert not (r/'roles/remote-backup').exists()
print('PASS: 0047 expected source entry points, role names and retirement scope')
