#!/usr/bin/env python3
"""Source-only adversarial guard test; uses a disposable journal, never Btrfs."""
import importlib.util
import json
from pathlib import Path
import tempfile
from unittest import mock

endpoint = Path(__file__).resolve().parents[1] / 'files/btrfs-native-endpoint.py'
spec = importlib.util.spec_from_file_location('step12_endpoint', endpoint)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
parent = '20261021-010000Z'
parent_uuid = '11111111-1111-1111-1111-111111111111'
source_uuid = '22222222-2222-2222-2222-222222222222'

with tempfile.TemporaryDirectory(prefix='0040-endpoint-guard-') as tmp:
    root = Path(tmp)
    received = root / 'received'
    state = root / 'state'
    received.mkdir()
    state.mkdir()
    pending = state / '.receiver-prune-pending.json'
    with mock.patch.object(module, 'RECEIVE_DIR', received), \
         mock.patch.object(module, 'RECEIVER_STATE', state), \
         mock.patch.object(module, 'RECEIVER_PENDING', pending), \
         mock.patch.object(module, 'safe_path', side_effect=lambda *a: None), \
         mock.patch.object(module, 'fs_check', side_effect=AssertionError('filesystem reached')), \
         mock.patch.object(module, 'show', side_effect=AssertionError('subvolume reached')), \
         mock.patch.object(module, 'run', side_effect=AssertionError('Btrfs command reached')):
        for candidate in (parent, '20261022-010000Z'):
            pending.write_text(json.dumps({
                'schema': 1, 'snapshot': candidate,
                'destination': str(received / candidate),
                'receipt': str(state / (candidate + '.json')),
                'source_uuid': source_uuid,
                'protected_parent': parent, 'protected_parent_uuid': parent_uuid,
            }))
            try:
                module.delete_receiver(candidate)
            except RuntimeError as exc:
                assert 'older than protected parent' in str(exc), str(exc)
            else:
                raise AssertionError(f'Unsafe candidate permitted: {candidate}')
        print('PASS: parent and newer rejected before filesystem inspection or Btrfs commands')
        (received / parent).mkdir()
        pending.write_text(json.dumps({
            'schema': 1, 'snapshot': '20261020-010000Z',
            'destination': str(received / '20261020-010000Z'),
            'receipt': str(state / '20261020-010000Z.json'),
            'source_uuid': source_uuid, 'protected_parent': parent,
            'protected_parent_uuid': parent_uuid,
        }))
        try:
            module.delete_receiver('20261020-010000Z')
        except AssertionError as exc:
            assert str(exc) == 'filesystem reached', str(exc)
        else:
            raise AssertionError('Older candidate failed to enter subsequent safety gates')
        print('PASS: older candidate reaches subsequent filesystem safety gate')
print('LIMIT: disposable journal and mocked Btrfs; no production deletion authority')
