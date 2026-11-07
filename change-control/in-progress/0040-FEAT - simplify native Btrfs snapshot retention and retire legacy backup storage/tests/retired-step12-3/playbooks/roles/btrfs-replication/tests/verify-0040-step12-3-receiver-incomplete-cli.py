#!/usr/bin/env python3
"""Source regression for fixed receiver incomplete-inspection CLI integration."""
import importlib.util
from pathlib import Path
from unittest import TestCase, main, mock

BASE = Path(__file__).resolve().parents[1]

def load(name):
    p = BASE / 'files' / ('btrfs-agreed-parent-' + name + '.py')
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

entry = load('receiver-entry')
inspection = load('incomplete-inspection')

class Tests(TestCase):
    def setUp(self):
        self.a = {'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
        self.b = {'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
        self.state={'schema':1,'established':self.a,'pending':self.b,'previous':None}
        self.journal={'schema':1,'status':'receiving','parent':self.a,'candidate':self.b,'nonce':'a'*64}
    def test_no_mutation_and_no_fencing_claim(self):
        storage=mock.Mock()
        storage.read_state.return_value=self.state
        storage.read_journal.return_value=self.journal
        storage.receipt_absent.return_value=True
        with mock.patch.object(inspection.Path, 'exists', return_value=False), mock.patch.object(inspection.Path,'is_symlink', return_value=False):
            result=inspection.inspect_locked_under_existing_locks(self.a,self.b,storage=storage,state_dir=entry.STATE,destination_root='/@data/mars-received/@data')
        self.assertFalse(result['cleanup_authorized'])
        self.assertFalse(result['stream_terminated_independently_proven'])
        self.assertFalse(result['retransmit_authorized'])
        self.assertFalse(result['destination_present'])
    def test_refuse_receipt(self):
        storage=mock.Mock()
        storage.read_state.return_value=self.state
        storage.read_journal.return_value=self.journal
        storage.receipt_absent.return_value=False
        with mock.patch.object(inspection.Path,'exists',return_value=False),mock.patch.object(inspection.Path,'is_symlink',return_value=False):
            with self.assertRaises(inspection.InspectionRefused):
                inspection.inspect_locked_under_existing_locks(self.a,self.b,storage=storage,state_dir=entry.STATE,destination_root='/@data/mars-received/@data')
    def test_refuse_wrong_root(self):
        with self.assertRaises(inspection.InspectionRefused):
            inspection.inspect_locked_under_existing_locks(self.a,self.b,storage=mock.Mock(),state_dir=entry.STATE,destination_root='/tmp')
    def test_entry_requires_root(self):
        with mock.patch.object(entry.os,'geteuid',return_value=1000):
            with self.assertRaises(RuntimeError): entry.inspect_incomplete_fixed(self.a,self.b)
    def test_entry_uses_both_locks(self):
        locks=[]
        class Lock:
            def __init__(self,name): self.name=name
            def __enter__(self): locks.append(('enter',self.name)); return self
            def __exit__(self,*a): locks.append(('exit',self.name))
        class Receiver:
            def _lock(self,stack,p): return stack.enter_context(Lock(p))
        receiver=Receiver()
        state=mock.Mock()
        storage=mock.Mock()
        diagnostic=mock.Mock()
        diagnostic.inspect_locked_under_existing_locks.return_value={'cleanup_authorized':False}
        deps={'receiver':receiver,'state':state,'finalisation-storage':storage,'incomplete-inspection':diagnostic}
        with mock.patch.object(entry.os,'geteuid',return_value=0):
            result=entry.inspect_incomplete_fixed(self.a,self.b,loader=lambda n:deps[n])
        self.assertFalse(result['cleanup_authorized'])
        self.assertEqual(locks,[('enter',entry.MANAGER),('enter',entry.WRITER),('exit',entry.WRITER),('exit',entry.MANAGER)])
        diagnostic.inspect_locked_under_existing_locks.assert_called_once()
    def test_cli_and_installer_source(self):
        text=(BASE/'files/btrfs-agreed-parent-receiver-entry.py').read_text()
        self.assertIn("mode.add_argument('--inspect-incomplete'",text)
        self.assertIn('result = inspect_incomplete_fixed(parent, candidate)',text)
        install=(BASE/'tasks/agreed-parent-runtime.yaml').read_text()
        self.assertIn('    - incomplete-inspection',install)

if __name__=='__main__': main(verbosity=2)
