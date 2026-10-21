#!/usr/bin/env python3
"""0037-FEAT Step 5: isolated read-only adversarial manager tests.
Usage: python3 step05_adversarial.py /home/richard/playbooks/roles/snapshots/files/btrfs-snapshot-manager.py
"""
import contextlib
import importlib.util
import io
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

if len(sys.argv) != 2:
    raise SystemExit('Usage: python3 step05_adversarial.py ABSOLUTE_PATH_TO_MANAGER')
manager_path = pathlib.Path(sys.argv.pop(1)).resolve()
spec = importlib.util.spec_from_file_location('snapshot_manager_0037_step05', manager_path)
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)
NOW = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)

def dt(day, hour=0):
    return datetime(2026, 10, day, hour, tzinfo=timezone.utc)

def record(number, date, kind='single', cleanup='timeline', source='@data'):
    return dict(number=number, timestamp=date, kind=kind, cleanup=cleanup,
                config=source, source=source, path=f'/fake/{source}/{number}')

def config():
    return m.Config(pathlib.Path('/fake/native'), pathlib.Path('/fake/lock'), None,
        (m.SnapshotSource('root', pathlib.Path('/fake/root')),
         m.SnapshotSource('@data', pathlib.Path('/fake/data'))),
        m.RetentionPolicy(1, 2, 1, 1, 1, 30),
        m.VerificationPolicy(False, '@data', '', '', None))

def plan(legacy, native=None, pins=None, holds=None, incomplete=None, now=NOW):
    native = native or []
    def capture():
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            m.legacy_plan(config(), ['root=root', '@data=@data'], True)
        return json.loads(buf.getvalue())
    with patch.object(m, 'preflight'), \
         patch.object(m, 'managed_snapshot_sets', return_value=(native, incomplete or {})), \
         patch.object(m, 'replication_pins', return_value=set(pins or [])), \
         patch.object(m, 'read_checkpoint_holds', return_value=holds or {}), \
         patch.object(m, 'legacy_snapper_inventory', return_value=legacy), \
         patch.object(m, 'datetime') as clock:
        clock.now.return_value = now
        return capture()

def decisions(document):
    return {int(x['number']): x for x in document['decisions']}

class PlanningSafety(unittest.TestCase):
    def test_no_legacy(self):
        doc = plan({'root': [], '@data': []})
        self.assertEqual(doc['decisions'], [])
        self.assertFalse(doc['authorizes_deletion'])

    def test_legacy_only_and_anchor(self):
        d = decisions(plan({'@data': [record(1,dt(1)), record(2,dt(2)), record(3,dt(3))], 'root': []}))
        self.assertEqual(d[3]['decision'], 'KEEP')
        self.assertIn('LATEST_LEGACY_ANCHOR', d[3]['reasons'])

    def test_native_precedence_and_floor(self):
        native = [('20261018-120000Z',dt(18,12))]
        d = decisions(plan({'@data':[record(1,dt(18,15)),record(2,dt(10))], 'root': []},native))
        self.assertEqual(d[1]['decision'], 'KEEP' if 'LATEST_LEGACY_ANCHOR' in d[1]['reasons'] else 'WOULD-DELETE')
        self.assertIn('20261018-120000Z', plan({'@data': [], 'root': []},native)['native_keepers'])

    def test_mixed_types_excluded(self):
        d = decisions(plan({'@data':[record(1,dt(10),'pre','number'),record(2,dt(11),'post','number'),record(3,dt(12),'single','manual')], 'root': []}))
        self.assertTrue(all(x['decision']=='EXCLUDED' for x in d.values()))

    def test_recent_snapshot(self):
        d = decisions(plan({'@data':[record(1,NOW - timedelta(minutes=5))], 'root': []}))
        self.assertIn('MINIMUM_AGE', d[1]['reasons'])

    def test_duplicate_times_deterministic(self):
        a = [record(10,dt(10)), record(11,dt(10)), record(12,dt(11))]
        d = decisions(plan({'@data':a,'root': []}))
        self.assertEqual(d[10]['decision'],'WOULD-DELETE')
        self.assertEqual(d[11]['decision'],'KEEP')
        self.assertEqual(d[12]['decision'],'KEEP')

    def test_distinct_source_scope(self):
        d=plan({'root':[record(1,dt(10),source='root')], '@data':[record(2,dt(11))]})
        self.assertEqual({x['source'] for x in d['decisions']},{'root','@data'})

    def test_incomplete_native_aborts(self):
        with self.assertRaises(m.SnapshotError):
            plan({'@data':[]}, incomplete={'20261019-000000Z': {'root'}})

    def test_missing_pins_aborts(self):
        with patch.object(m,'preflight'),patch.object(m,'managed_snapshot_sets',return_value=([],{})),\
             patch.object(m,'replication_pins', side_effect=m.SnapshotError('missing pins')):
            with self.assertRaises(m.SnapshotError):
                m.legacy_plan(config(), ['root=root'], True)

    def test_missing_holds_aborts(self):
        with patch.object(m,'preflight'),patch.object(m,'managed_snapshot_sets',return_value=([],{})),\
             patch.object(m,'replication_pins', return_value=set()),\
             patch.object(m,'read_checkpoint_holds', side_effect=m.SnapshotError('missing holds')):
            with self.assertRaises(m.SnapshotError):
                m.legacy_plan(config(), ['root=root'], True)

    def test_pin_and_hold_are_keepers(self):
        names=[('20261001-000000Z',dt(1)),('20261002-000000Z',dt(2))]
        d=plan({'root':[], '@data':[]}, names, pins={'20261001-000000Z'}, holds={'20261002-000000Z': {'reason':'test'}})
        self.assertEqual(set(d['native_keepers']), {x[0] for x in names})

    def test_plan_has_no_delete_call(self):
        with patch.object(m,'run',side_effect=AssertionError('unexpected external command')):
            d=plan({'@data':[record(1,dt(1))]})
            self.assertFalse(d['authorizes_deletion'])

class InventorySafety(unittest.TestCase):
    def run_inventory(self, csv_text, cfg_text=None, tz='Etc/UTC', missing=False):
        with tempfile.TemporaryDirectory() as temp:
            root=pathlib.Path(temp)
            source=root/'data'; source.mkdir()
            snaps=source/'.snapshots'
            if not missing:
                snaps.mkdir()
            text_cfg=f'SUBVOLUME | {source}\n' if cfg_text is None else cfg_text
            cfg=m.Config(root/'native',root/'lock',None,(m.SnapshotSource('@data',source),),
                         config().retention,config().verification)
            def fake_run(argv,**kwargs):
                if 'get-config' in argv: return subprocess.CompletedProcess(argv,0,text_cfg,'')
                if 'list' in argv: return subprocess.CompletedProcess(argv,0,csv_text,'')
                if 'timedatectl' in argv[0]: return subprocess.CompletedProcess(argv,0,tz+'\n','')
                raise AssertionError(f'unexpected command: {argv}')
            with patch.object(m,'run',side_effect=fake_run),\
                 patch.object(m,'require_btrfs'),patch.object(m,'require_subvolume'):
                return m.legacy_snapper_inventory(cfg,['@data=@data'])

    def test_empty_without_directory(self):
        csv='number,type,date,cleanup\n0,single,,\n'
        self.assertEqual(self.run_inventory(csv,missing=True)['@data'],[])

    def test_numbered_missing_directory_aborts(self):
        csv='number,type,date,cleanup\n0,single,,\n1,single,2026-10-01 00:00:00,timeline\n'
        with self.assertRaises(m.SnapshotError): self.run_inventory(csv,missing=True)

    def test_duplicate_numbers_aborts(self):
        csv='number,type,date,cleanup\n1,single,2026-10-01 00:00:00,timeline\n1,single,2026-10-01 00:00:00,timeline\n'
        with self.assertRaises(m.SnapshotError): self.run_inventory(csv)

    def test_missing_columns_aborts(self):
        with self.assertRaises(m.SnapshotError): self.run_inventory('number,date\n0,\n')

    def test_unknown_source_aborts(self):
        with self.assertRaises((m.SnapshotError, OSError)): self.run_inventory('number,type,date,cleanup\n0,single,,\n',cfg_text='SUBVOLUME | /wrong\n')

    def test_failed_snapper_command_aborts(self):
        with patch.object(m,'run',side_effect=m.SnapshotError('snapper failed')):
            with self.assertRaises(m.SnapshotError):
                m.legacy_snapper_inventory(config(),['@data=@data'])

    def test_duplicate_mappings_aborts(self):
        with patch.object(m,'run',side_effect=m.SnapshotError('stub')):
            with self.assertRaises(m.SnapshotError):
                m.legacy_snapper_inventory(config(),['@data=@data','root=@data'])

class Compatibility(unittest.TestCase):
    def test_native_only_retention_unchanged_by_plan(self):
        snaps=[('20261019-110000Z',dt(19,11),pathlib.Path('/fake/a')),
               ('20261018-110000Z',dt(18,11),pathlib.Path('/fake/b'))]
        before=m.retention_keep_set(snaps,config().retention,NOW)
        plan({'@data':[], 'root':[]},[(n,t) for n,t,_ in snaps])
        after=m.retention_keep_set(snaps,config().retention,NOW)
        self.assertEqual(before,after)

if __name__=='__main__':
    unittest.main(verbosity=2)
