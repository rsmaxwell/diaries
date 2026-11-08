#!/usr/bin/env python3
"""Synthetic regression of Step 12 read-only receipt and explicit removal scope."""
import importlib.machinery
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch
import tempfile

FEATURE = Path(__file__).resolve().parents[1]

def load(name):
    file = FEATURE / 'tools' / name
    loader = importlib.machinery.SourceFileLoader(name.replace('.','_'), str(file))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module

retire = load('retire-0040-obsolete-code.py')
accept = load('verify-0040-step12-first-unattended-prune.py')
with patch.object(retire, 'CANDIDATES', FEATURE / 'tools/legacy-code-candidate-paths.json'):
    files = retire.allowed_paths()
assert len(files['mars']) == 39
assert len(files['backup']) == 35
assert not any('simplified-replication' in path or '@snapshots' in path or 'mars-received' in path
               for values in files.values() for path in values)
try:
    retire.apply(files, None, None, None)
    raise AssertionError('missing confirmation erroneously accepted')
except RuntimeError as exc:
    assert 'explicit operator acceptance absent' in str(exc)

with tempfile.TemporaryDirectory() as temp:
    state = {'schema': 1, 'parent': {'timestamp':'20261108-030001Z', 'uuid':'a'}, 'prior': None}
    plan = 'RECEIVER-SIMPLE-PLAN {"parent": {}, "prior": null, "candidates": 0}\n'
    def ssh_fake(host, command, **kwargs):
        if command.startswith('systemctl show btrfs-receiver-simple-prune.service'):
            stdout = 'Result=success\nExecMainStatus=0\nExecMainStartTimestamp=Sun 2026-11-08 04:15:00 UTC\nExecMainExitTimestamp=Sun 2026-11-08 04:15:01 UTC\n'
        elif 'journalctl' in command:
            stdout = 'Nov 08 04:15:01 backup btrfs-snapshot-manager[12]: RECEIVER-SIMPLE-DELETED count=0\n'
        elif 'receiver-simple-plan' in command:
            stdout = plan
        elif command.endswith('receiver status'):
            stdout = json.dumps({'state':state})
        elif command.startswith('sudo -n cat'):
            stdout = json.dumps(state)
        elif command.startswith('systemctl show') and 'btrfs-receiver-simple-prune.timer' in command:
            stdout = 'ActiveState=active\nUnitFileState=enabled\nLastTriggerUSec=Sun 2026-11-08 04:15:00 UTC\n'
        elif command.startswith('systemctl show') and 'btrfs-native-push.timer' in command:
            stdout = 'ActiveState=active\nUnitFileState=enabled\n'
        else:
            stdout = 'ok\n'
        return {'exit':0, 'stdout':stdout, 'stderr':''}
    def fake_host(argv, **kwargs):
        return type('Completed', (), {'stdout':'mango\n', 'returncode':0})()
    with patch.object(accept, 'ssh', side_effect=ssh_fake), \
         patch.object(accept, 'EVIDENCE', Path(temp)), \
         patch.object(accept.subprocess, 'run', side_effect=fake_host), \
         patch.object(accept.Path, 'cwd', return_value=Path('/home/richard/diaries')):
        assert accept.main() == 0
    receipts = list(Path(temp).glob('*.json'))
    assert len(receipts) == 1
    receipt = json.loads(receipts[0].read_text())
    assert receipt['diagnostic_pass'] is True
    assert receipt['formal_acceptance'] == 'PENDING_OPERATOR_REVIEW'
    assert receipt['deleted_count'] == 0
print('PASS: fixed code-only allowlist, deletion refusal without approval, and synthetic zero-delete unattended receipt')
