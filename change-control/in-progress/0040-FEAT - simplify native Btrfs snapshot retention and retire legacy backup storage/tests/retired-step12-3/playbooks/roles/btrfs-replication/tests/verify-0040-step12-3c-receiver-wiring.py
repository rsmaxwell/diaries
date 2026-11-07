#!/usr/bin/env python3
"""Source-only 0040 Step 12.3c receiver callback integration regression."""
import importlib.util
import io
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

source = Path(__file__).resolve().parents[1] / 'files/btrfs-receiver-prune.py'
spec = importlib.util.spec_from_file_location('receiver_prune', source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
parent='20261025-030000Z'; candidate='20261024-030000Z'
root=Path('/@data/mars-received/@data')
import re
receiver = SimpleNamespace(ROOT=root, STAMP=re.compile(r'^[0-9]{8}-[0-9]{6}Z$'), protected_retention_plan=lambda *a: {})
config = SimpleNamespace(mode='receiver',receiver_prune_enabled=False,
    receiver_state_dir=Path('/fixture/state'),writer_lock_path=Path('/fixture/state/writer.lock'),
    lock_path=Path('/fixture/manager.lock'))
commands=[]

def command(argv, **kw):
    commands.append((argv,kw))

def adapter(stamp,uuid,selected,**kw):
    assert selected==candidate and stamp==parent
    assert kw['planner'] is receiver.protected_retention_plan
    kw['delete_subvolume'](root / candidate)
    assert len(commands)==1
    try:
        kw['delete_subvolume'](Path('/not-managed') / candidate)
    except RuntimeError:
        pass
    else:
        raise AssertionError('Unmanaged snapshot accepted')
    return {'production_authorized':False,'result':{}}

kwargs=dict(receiver_module=receiver,manager=object(),receiver_config=config,
    incoming=io.StringIO(),outgoing=io.StringIO(),stamp=parent,
    uuid='00000000-0000-0000-0000-000000000001',candidate=candidate,
    approval_path=Path('/fixture/approval'),consumed_dir=Path('/fixture/consumed'),
    run_command=command,approved_adapter=adapter)
with patch.object(module, 'verify_root_and_config',return_value={'mode':'receiver'}):
    module.run_receiver_prune_transaction(**kwargs)
assert commands==[(['/usr/local/libexec/btrfs-native-endpoint','--role','delete-receiver','--snapshot',candidate],{'check':True})]
try:
    module.run_receiver_prune_transaction(**{**kwargs,'candidate':'../../escape'})
except RuntimeError:
    pass
else:
    raise AssertionError('Invalid candidate accepted')
assert len(commands)==1
main=source.read_text().split('def main(argv=None):',1)[1]
assert 'run_unattended_receiver_transaction(' in main
assert 'run_receiver_prune_transaction(' not in main
print('PASS: receiver transaction callback uses fixed managed path and endpoint')
print('PASS: invalid candidates and unmanaged callback paths rejected')
print('PASS: explicit receiver transaction CLI wiring verified')
