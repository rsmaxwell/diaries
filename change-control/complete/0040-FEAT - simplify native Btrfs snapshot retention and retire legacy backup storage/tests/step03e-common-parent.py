#!/usr/bin/env python3
"""0040 Step 3E: offline common-parent observation and fail-closed receiver prune."""
import importlib.util, tempfile, pathlib, sys
from unittest.mock import patch
manager=pathlib.Path(sys.argv[1]); sender=pathlib.Path(sys.argv[2])
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod
m=load('manager3e',manager); p=load('sender3e',sender)
S='20261023-030037Z'; UUID='fdcabd00-aa98-7647-bd3a-de5e23186d38'
info={'flags':'readonly','parent_uuid':p.SOURCE_PARENT,'received_uuid':'-','uuid':UUID}
with patch.object(p,'local',return_value=info):
    result=p.inspect_common_parent([{'snapshot':S,'source_uuid':UUID}]); assert result['source_uuid']==UUID and result['authorizes_prune'] is False
with patch.object(p,'local',return_value={**info,'uuid':'mismatch'}):
    try:p.inspect_common_parent([{'snapshot':S,'source_uuid':UUID}]);raise AssertionError('wrong UUID accepted')
    except RuntimeError as e:assert 'No verified' in str(e)
for bad in [[{'snapshot':'bad','source_uuid':UUID}], [{'snapshot':S,'source_uuid':UUID}]*2]:
    try:p.inspect_common_parent(bad);raise AssertionError('bad receiver list accepted')
    except RuntimeError:pass
with patch.object(p,'local',side_effect=FileNotFoundError):
    try:p.inspect_common_parent([{'snapshot':S,'source_uuid':UUID}]);raise AssertionError('missing source accepted')
    except RuntimeError as e:assert 'No verified' in str(e)
with tempfile.TemporaryDirectory() as t:
    root=pathlib.Path(t); approval=root/'approval.json'; approval.write_text('{}')
    config=m.Config.__new__(m.Config)
    object.__setattr__(config,'mode','receiver');object.__setattr__(config,'receiver_state_dir',root)
    object.__setattr__(config,'receiver_prune_enabled',True)
    try:m.receiver_guarded_prune(config,approval);raise AssertionError('receiver deletion reached')
    except m.SnapshotError as e:assert 'coordination not implemented' in str(e)
print('PASS: Step 3E common-parent diagnostic and deletion-disabled gate')
