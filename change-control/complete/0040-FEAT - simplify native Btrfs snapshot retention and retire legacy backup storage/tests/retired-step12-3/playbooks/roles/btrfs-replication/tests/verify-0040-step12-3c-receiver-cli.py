#!/usr/bin/env python3
"""Regression of receiver command selection; no snapshot or approval files changed."""
import importlib.util
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

source=Path(__file__).resolve().parents[1] / 'files/btrfs-receiver-prune.py'
spec=importlib.util.spec_from_file_location('btrfs_receiver_prune', source)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

# Existing non-destructive command remains available.
with patch.object(m, 'verify_root_and_config', return_value={'mode':'receiver','receiver_prune_enabled':False}):
    m.main(['--verify-boundary'])

# No transaction arguments => reject before module loading or operation.
with patch.object(m, 'verify_root_and_config', return_value={'mode':'receiver','receiver_prune_enabled':False}), patch.object(m, 'load_installed_module', side_effect=AssertionError('unexpected load')):
    try: m.main(['--transaction'])
    except SystemExit as exc: assert exc.code == 2
    else: raise AssertionError('incomplete transaction permitted')

called=[]
manager=SimpleNamespace(load_config=lambda path: 'CONFIG')
receiver=SimpleNamespace()
with patch.object(m, 'verify_root_and_config', return_value={'mode':'receiver','receiver_prune_enabled':False}), patch.object(m, 'load_installed_module', side_effect=[manager,receiver]), patch.object(m, 'run_unattended_receiver_transaction', side_effect=lambda **kw: called.append(kw)):
    m.main(['--transaction','--protected-parent','20261028-000000Z','--parent-uuid','11111111-1111-1111-1111-111111111111','--candidate','20261020-000000Z'])
assert len(called)==1
assert 'approval_path' not in called[0]
assert 'consumed_dir' not in called[0]
assert called[0]['receiver_config']=='CONFIG'
print('PASS: receiver CLI selects explicit unattended transaction without approvals')
print('PASS: incomplete transaction rejected; no production deployment or Btrfs mutation')
