#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest
from types import SimpleNamespace
p = Path(__file__).resolve().parents[1] / 'files' / 'btrfs-agreed-parent-scope-observer.py'
s = importlib.util.spec_from_file_location('observer', p)
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
UNIT = 'btrfs-agreed-receive-20261102-083000Z.scope'
def response(**replacements):
    d = {'Id': UNIT, 'LoadState':'loaded', 'ActiveState':'inactive', 'SubState':'dead',
         'ControlGroup':'/system.slice/' + UNIT, 'TasksCurrent':'0'}
    d.update(replacements)
    return '\n'.join(f'{k}={v}' for k,v in d.items()) + '\n'
def run(text=None, rc=0):
    return lambda *args, **kwargs: SimpleNamespace(returncode=rc, stdout=response() if text is None else text)
class Tests(unittest.TestCase):
    def test_report_not_cleanup(self):
        r=m.inspect_scope(UNIT, runner=run()); self.assertFalse(r['cleanup_authorized']); self.assertFalse(r['journal_bound'])
    def test_bad_name(self):
        with self.assertRaises(m.ScopeRefused): m.inspect_scope('../fake', runner=run())
    def test_active(self):
        with self.assertRaises(m.ScopeRefused): m.inspect_scope(UNIT, runner=run(response(ActiveState='active')))
    def test_unknown(self):
        with self.assertRaises(m.ScopeRefused): m.inspect_scope(UNIT, runner=run(response(LoadState='not-found')))
    def test_tasks(self):
        with self.assertRaises(m.ScopeRefused): m.inspect_scope(UNIT, runner=run(response(TasksCurrent='1')))
    def test_control_group(self):
        with self.assertRaises(m.ScopeRefused): m.inspect_scope(UNIT, runner=run(response(ControlGroup='')))
    def test_wrong_id(self):
        with self.assertRaises(m.ScopeRefused): m.inspect_scope(UNIT, runner=run(response(Id='other.scope')))
    def test_missing_property(self):
        with self.assertRaises(m.ScopeRefused): m.inspect_scope(UNIT, runner=run('Id='+UNIT+'\n'))
    def test_duplicate(self):
        with self.assertRaises(m.ScopeRefused): m.inspect_scope(UNIT, runner=run(response()+'Id='+UNIT+'\n'))
    def test_nonzero(self):
        with self.assertRaises(m.ScopeRefused): m.inspect_scope(UNIT, runner=run(rc=1))
if __name__ == '__main__': unittest.main(verbosity=2)
