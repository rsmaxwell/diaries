#!/usr/bin/env python3
"""Fixed CLI/command integration; no live Btrfs or SSH."""
import importlib.util
import io
import json
from pathlib import Path
from unittest.mock import patch
from contextlib import redirect_stdout
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]/'files'
def load(file):
    spec=importlib.util.spec_from_file_location(file.replace('-','_'),ROOT/file)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
cmd=load('btrfs-agreed-parent-fixed-commands.py')
entry=load('btrfs-agreed-parent-receiver-entry.py')
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
class Tests(unittest.TestCase):
    def test_commands_are_fixed_and_identity_bound(self):
        for fn,mode in ((cmd.promote_command,'--promote'),(cmd.promoted_readback_command,'--promoted-readback')):
            call=fn(A,B)
            self.assertEqual(call[:len(cmd.SSH)],list(cmd.SSH))
            self.assertEqual(call[len(cmd.SSH):len(cmd.SSH)+3],['sudo','-n',cmd.RECEIVER_ENTRY])
            self.assertEqual(call[-9:],[mode,'--parent',A['timestamp'],'--parent-uuid',A['uuid'],'--candidate',B['timestamp'],'--candidate-uuid',B['uuid']])
            with self.assertRaises(cmd.CommandRefused):fn(B,A)
    def invoke(self,mode):
        argv=['receiver',mode,'--parent',A['timestamp'],'--parent-uuid',A['uuid'],'--candidate',B['timestamp'],'--candidate-uuid',B['uuid']]
        calls=[]
        class Fake:
            def promote_verified_receiver(self,a,b):
                calls.append(('promote',a,b))
                return {'status':'receiver-promoted-previous-pinned','authorizes_prune':False,'authorizes_release':False}
            def read_promoted_state(self,a,b):
                calls.append(('readback',a,b))
                return {'schema':1,'established':b,'pending':None,'previous':a}
        output=io.StringIO()
        with patch.object(sys,'argv',argv),patch.object(entry.os,'geteuid',return_value=0),patch.object(entry,'module',return_value=Fake()),redirect_stdout(output):entry.main()
        return calls,json.loads(output.getvalue())
    def test_promote_and_readback_dispatch(self):
        for mode,expected in (('--promote','promote'),('--promoted-readback','readback')):
            calls,result=self.invoke(mode)
            self.assertEqual(calls,[(expected,A,B)])
            self.assertIsInstance(result,dict)
    def test_root_is_required(self):
        argv=['receiver','--promote','--parent',A['timestamp'],'--parent-uuid',A['uuid'],'--candidate',B['timestamp'],'--candidate-uuid',B['uuid']]
        with patch.object(sys,'argv',argv),patch.object(entry.os,'geteuid',return_value=1000),patch.object(entry,'module') as loader:
            with self.assertRaisesRegex(RuntimeError,'root required'):entry.main()
            loader.assert_not_called()
    def test_modes_mutually_exclusive(self):
        with patch.object(sys,'argv',['receiver','--promote','--promoted-readback']):
            with self.assertRaises(SystemExit) as caught:entry.main()
            self.assertEqual(caught.exception.code,2)
if __name__=='__main__':unittest.main(verbosity=2)
