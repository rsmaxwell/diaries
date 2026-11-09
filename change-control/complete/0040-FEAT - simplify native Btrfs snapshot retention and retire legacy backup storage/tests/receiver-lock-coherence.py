#!/usr/bin/env python3
"""0040-FEAT: receiver inventory/plan lock-coherence regression; no live access."""
import importlib.util
import io
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

manager_path = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location('snapshot_manager_0040', manager_path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

class FakeLock:
    def __init__(self, path, records):
        self.path = path
        self.records = records
    def close(self):
        self.records.append(('release', str(self.path)))

with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)
    state = root / 'state'
    state.mkdir()
    (state / 'writer.lock').touch()
    config = SimpleNamespace(mode='receiver', receiver_state_dir=state,
                             lock_path=root / 'manager.lock', writer_lock_path=state / 'writer.lock')
    for command in ('receiver-inventory', 'receiver-plan'):
        events = []
        def lock(path, **kwargs):
            events.append(('acquire', str(path), kwargs))
            return FakeLock(path, events)
        def check(_):
            assert [v[1] for v in events if v[0] == 'acquire'] == [str(config.lock_path), str(config.writer_lock_path)]
        with patch.object(module, 'require_root'), patch.object(module, 'load_config', return_value=config), \
             patch.object(module, 'with_lock', side_effect=lock), \
             patch.object(module, 'receiver_inventory', side_effect=check), \
             patch.object(module, 'receiver_plan', side_effect=check), redirect_stdout(io.StringIO()):
            code = module.main(['--config', str(root / 'config.json'), command])
        assert code == 0, (command, code)
        assert [v[1] for v in events if v[0] == 'release'] == [str(config.writer_lock_path), str(config.lock_path)]
        print('PASS:', command, 'acquires manager lock then exclusive receiver writer lock')

    pending = state / '.receiver-prune-pending.json'
    pending.write_text('{}')
    with patch.object(module, 'receiver_inventory', side_effect=AssertionError('should not enumerate')):
        try:
            module.receiver_plan(config)
        except module.SnapshotError as ex:
            assert 'pending receiver prune transaction' in str(ex)
        else:
            raise AssertionError('retention plan ignored pending journal')
    print('PASS: pending deletion journal blocks retention planning')
    assert 'receiver pruning blocked: live common-parent coordination not implemented' in manager_path.read_text()
    print('PASS: production receiver deletion still blocked')
print('PASS: 0040 receiver inventory/plan lock coherence; no live mutation')
