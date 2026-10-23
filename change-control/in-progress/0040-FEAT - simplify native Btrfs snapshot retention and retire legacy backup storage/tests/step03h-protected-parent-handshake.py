#!/usr/bin/env python3
"""Offline Step 3H protected-parent handshake regression. Does not call real SSH/Btrfs."""
import importlib.util
import json
import pathlib
import sys
from unittest.mock import patch

sender_path = pathlib.Path(sys.argv[1])
receiver_path = pathlib.Path(sys.argv[2])
def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
sender = load(sender_path, 'step03h_sender')
receiver = load(receiver_path, 'step03h_receiver')
stamp = '20261023-030037Z'
uuid = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
receipt = {'source_uuid': uuid}
with patch.object(receiver, 'receipt', return_value=receipt), patch.object(receiver, 'STATE', pathlib.Path('/nonexistent-step03h-state')):
    result = receiver.check_protected_parent(stamp, uuid)
    assert result['receiver_verified_under_lock'] and not result['authorizes_prune']
    try:
        receiver.check_protected_parent(stamp, 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb')
    except RuntimeError: pass
    else: raise AssertionError('Receiver accepted wrong UUID')
with patch.object(receiver, 'receipt', return_value=None), patch.object(receiver, 'STATE', pathlib.Path('/nonexistent-step03h-state')):
    try: receiver.check_protected_parent(stamp, uuid)
    except RuntimeError: pass
    else: raise AssertionError('Receiver accepted missing receipt')
with patch.object(sender, 'protect_common_parent', return_value={'snapshot':stamp,'source_uuid':uuid}), \
     patch.object(sender, 'remote', return_value=json.dumps(result)) as remote:
    outcome = sender.prepare_prune_parent()
    assert outcome['source_pinned'] and outcome['receiver_verified_under_lock']
    assert outcome['authorizes_prune'] is False
    assert remote.call_args.args == ('--check-protected-parent','--snapshot',stamp,'--source-uuid',uuid)
with patch.object(sender, 'protect_common_parent', return_value={'snapshot':stamp,'source_uuid':uuid}), \
     patch.object(sender, 'remote', return_value=json.dumps({**result, 'authorizes_prune':True})):
    try: sender.prepare_prune_parent()
    except RuntimeError: pass
    else: raise AssertionError('Sender accepted an unintended prune authorisation')
with patch.object(sender, 'protect_common_parent', return_value={'snapshot':stamp,'source_uuid':uuid}), \
     patch.object(sender, 'remote', side_effect=OSError('unreachable')):
    try: sender.prepare_prune_parent()
    except OSError: pass
    else: raise AssertionError('Sender accepted failed remote check')
print('PASS: Step 3H durable source pin and lock-held receiver proof; deletion not authorised')
