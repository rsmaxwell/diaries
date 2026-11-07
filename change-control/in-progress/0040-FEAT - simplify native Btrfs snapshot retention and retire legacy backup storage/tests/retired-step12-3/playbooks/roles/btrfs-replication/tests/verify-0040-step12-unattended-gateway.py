#!/usr/bin/env python3
"""Non-destructive unattended receiver adapter regression."""
import importlib.util
import io
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

src = Path(__file__).resolve().parents[1] / 'files' / 'btrfs-receiver-prune.py'
spec = importlib.util.spec_from_file_location('unattended_gateway_test', src)
gateway = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gateway)
root = Path('/@data/mars-received/@data')
parent = '20261028-030000Z'
candidate = '20261027-030000Z'
uuid = '00000000-0000-0000-0000-000000000001'
config = SimpleNamespace(mode='receiver', receiver_prune_enabled=False,
    receiver_state_dir=Path('/fixture/state'), writer_lock_path=Path('/fixture/state/writer.lock'),
    lock_path=Path('/fixture/manager.lock'))
receiver = SimpleNamespace(ROOT=root, STAMP=__import__('re').compile(r'^[0-9]{8}-[0-9]{6}Z$'),
                           protected_retention_plan=lambda *args: None)
calls = []
def adapter(stamp, source_uuid, target, **kwargs):
    calls.append((stamp, source_uuid, target, kwargs))
    return {'kind':'transaction-completed','snapshot':target,'protected_parent':stamp,
            'protected_parent_uuid':source_uuid,'journal_transaction_completed':True}
args = dict(receiver_module=receiver, manager=object(), receiver_config=config,
    incoming=io.StringIO(), outgoing=io.StringIO(), stamp=parent, uuid=uuid,
    candidate=candidate, transaction_adapter=adapter,
    run_command=lambda *a, **k: (_ for _ in ()).throw(AssertionError('unexpected deletion')))
with mock.patch.object(gateway, 'verify_root_and_config', return_value={'mode':'receiver'}):
    result = gateway.run_unattended_receiver_transaction(**args)
    assert result['journal_transaction_completed'] and len(calls) == 1
    assert calls[0][3]['incoming'] is args['incoming']
    try:
        gateway.run_unattended_receiver_transaction(**{**args, 'candidate': parent})
    except RuntimeError: pass
    else: raise AssertionError('Protected parent accepted as target')
    try:
        gateway.run_unattended_receiver_transaction(**{**args, 'transaction_adapter': lambda *a, **k: {}})
    except RuntimeError: pass
    else: raise AssertionError('False completion accepted')
    def interrupted(*a, **k): raise OSError('interrupted transport')
    try:
        gateway.run_unattended_receiver_transaction(**{**args, 'transaction_adapter': interrupted})
    except OSError: pass
    else: raise AssertionError('Interruption swallowed')
    bad = SimpleNamespace(**vars(config)); bad.writer_lock_path = Path('/wrong')
    try:
        gateway.run_unattended_receiver_transaction(**{**args, 'receiver_config': bad})
    except RuntimeError: pass
    else: raise AssertionError('Unsafe lock accepted')
    callback = calls[0][3]['delete_subvolume']
    try: callback(Path('/wrong/path'))
    except RuntimeError: pass
    else: raise AssertionError('Unexpected deletion path accepted')
    assert 'approval_path' not in calls[0][3] and 'consumed_dir' not in calls[0][3]
print('PASS: unattended gateway delegates without approvals, rejects unsafe paths and false completion')
