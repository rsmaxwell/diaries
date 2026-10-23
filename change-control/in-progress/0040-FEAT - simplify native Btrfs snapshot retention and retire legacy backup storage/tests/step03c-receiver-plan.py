"""0040-FEAT Step 3C: no mutation, verified inventory, shared retention buckets."""
import importlib.util
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

p = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location('snapshot_step3c', p)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory() as td:
    base = Path(td)
    received = base / 'received'
    received.mkdir()
    state = base / 'state'
    state.mkdir()
    stamps = ['20261019-030000Z', '20261020-030000Z', '20261022-100000Z',
              '20261022-110000Z', '20261022-120000Z']
    cfg = base / 'config.json'
    cfg.write_text(json.dumps({
        'mode': 'receiver', 'snapshot_root': str(base),
        'receiver_state_dir': str(state),
        'sources': [{'name': '@data', 'snapshot_directory': str(received)}],
        'retention': {'hourly': 2, 'daily': 1, 'weekly': 0, 'monthly': 0,
                      'yearly': 0, 'minimum_age_minutes': 30},
    }))
    config = mod.load_config(cfg)
    for i, stamp in enumerate(stamps):
        path = received / stamp
        path.mkdir()
        uuid = f'{i+1:036x}'
        (state / (stamp + '.json')).write_text(json.dumps({
            'schema': 1, 'snapshot': stamp, 'destination': str(path),
            'source_uuid': uuid, 'received_uuid': uuid,
            'read_only_verified': True,
            # Historical parent need not remain present.
            'parent_snapshot': '20261001-000000Z',
        }))

    def fake_run(command, *, check=True):
        if command[1:3] == ['subvolume', 'show']:
            stamp = Path(command[-1]).name
            value = f'{stamps.index(stamp)+1:036x}'
            out = 'Received UUID: ' + value + '\n'
        elif command[1:4] == ['property', 'get', '-ts']:
            out = 'ro=true\n'
        else:
            raise AssertionError('unexpected or mutating command: ' + repr(command))
        return subprocess.CompletedProcess(command, 0, out, '')

    with patch.object(mod, 'preflight'), patch.object(mod, 'run', side_effect=fake_run):
        fixed = datetime(2026, 10, 22, 12, 45, tzinfo=timezone.utc)
        result = mod.receiver_plan(config, now=fixed)
        expected = mod.retention_keep_set(mod.list_managed(config, config.sources[0]), config.retention, fixed)
        assert set(result['keep']) == expected
        assert result['candidates'] == ['20261022-100000Z', '20261020-030000Z', '20261019-030000Z']
        assert result['executable'] is False
        assert (received / stamps[0]).exists() and (state / (stamps[0] + '.json')).exists()

        # A matching receipt with wrong received UUID must fail the entire plan.
        target = state / (stamps[0] + '.json')
        data = json.loads(target.read_text())
        data['source_uuid'] = 'f' * 36
        target.write_text(json.dumps(data))
        try:
            mod.receiver_plan(config, now=fixed)
        except mod.SnapshotError:
            pass
        else:
            raise AssertionError('invalid received identity accepted')
        data['source_uuid'] = data['received_uuid']
        target.write_text(json.dumps(data))

        # An orphan receipt also fails closed.
        orphan = state / '20261018-030000Z.json'
        orphan.write_text('{}')
        try:
            mod.receiver_plan(config, now=fixed)
        except mod.SnapshotError:
            pass
        else:
            raise AssertionError('orphan receipt accepted')
        orphan.unlink()


    # A receiver plan is never an execution approval.
    assert all(path.exists() for path in received.iterdir())

print('PASS: Step 3C read-only receiver retention selection, receipt failure and no mutation')
