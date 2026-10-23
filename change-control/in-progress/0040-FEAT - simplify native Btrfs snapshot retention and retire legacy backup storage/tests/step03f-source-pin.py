import importlib.util
import sys
from unittest.mock import patch

path = sys.argv[1]
spec = importlib.util.spec_from_file_location('native_push_0040_3f', path)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
STAMP = '20261023-030037Z'
UUID = 'a' * 36
candidate = {'snapshot': STAMP, 'source_uuid': UUID, 'verified': True, 'authorizes_prune': False}

with patch.object(mod, 'inspect_common_parent', side_effect=[candidate, candidate]) as inspect, patch.object(mod, 'local', return_value={'source_uuid': UUID}) as local:
    result = mod.protect_common_parent()
    assert result['source_pinned'] is True and result['authorizes_prune'] is False
    local.assert_called_once_with('protect-source', STAMP)
    assert inspect.call_count == 2

with patch.object(mod, 'inspect_common_parent', return_value=candidate), patch.object(mod, 'local', return_value={'source_uuid': 'b'*36}):
    try: mod.protect_common_parent()
    except RuntimeError as e: assert 'pin UUID mismatch' in str(e)
    else: raise AssertionError('Wrong UUID accepted')

changed = dict(candidate, snapshot='20261022-120034Z')
with patch.object(mod, 'inspect_common_parent', side_effect=[candidate, changed]), patch.object(mod, 'local', return_value={'source_uuid': UUID}) as local:
    try: mod.protect_common_parent()
    except RuntimeError as e: assert 'source pin retained' in str(e)
    else: raise AssertionError('Changed common parent accepted')
    assert local.call_count == 1

with patch.object(mod, 'inspect_common_parent', side_effect=RuntimeError('No verified common replication parent')), patch.object(mod, 'local') as local:
    try: mod.protect_common_parent()
    except RuntimeError: pass
    else: raise AssertionError('Missing parent accepted')
    local.assert_not_called()

print('PASS: Step 3F persistent source pin contract, fail-closed revalidation (no mutation)')
