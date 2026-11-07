#!/usr/bin/env python3
"""Regression for bounded unattended Step 12.3 driver."""
import importlib.util
from pathlib import Path
import unittest

FILE = Path(__file__).resolve().parents[1] / 'files' / 'btrfs-agreed-parent-unattended-driver.py'
spec = importlib.util.spec_from_file_location('driver', FILE)
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)

class FakeCoordinator:
    def __init__(self, transitions):
        self.transitions = iter(transitions)
    def choose_once(self, **kwargs):
        assert kwargs['canonical_locks_held'] is True
        action, following = next(self.transitions)
        if action == 'RAISE':
            raise RuntimeError('peer unavailable')
        return {'status':'one-step-verified','action':action,'next_action':following}

class Tests(unittest.TestCase):
    def run_driver(self, transitions, **kw):
        return d.drive(coordinator=FakeCoordinator(transitions), policy=object(),
                       observe=lambda: {}, operate=lambda *args: {}, locks_held=True, **kw)
    def test_successful_prepared_cycle(self):
        result = self.run_driver([('execute-prepared','acknowledge-previous'),
                                  ('acknowledge-previous','select-next-candidate')])
        self.assertEqual(result['status'], 'cycle-ready')
        self.assertEqual(result['actions'], ['execute-prepared','acknowledge-previous'])
    def test_recovery_resumes_without_send(self):
        self.assertEqual(self.run_driver([('resume-committed','acknowledge-previous'),
                                          ('acknowledge-previous','select-next-candidate')])['status'], 'cycle-ready')
    def test_idle_exits(self):
        self.assertEqual(self.run_driver([('select-next-candidate','select-next-candidate')])['status'],
                         'awaiting-candidate-selection')
    def test_no_progress_refused(self):
        with self.assertRaisesRegex(d.DriverRefused, 'no verified durable progress'):
            self.run_driver([('resume-committed','resume-committed')])
    def test_outage_propagated(self):
        with self.assertRaisesRegex(RuntimeError, 'peer unavailable'):
            self.run_driver([('RAISE','')])
    def test_bounded_failure(self):
        with self.assertRaisesRegex(d.DriverRefused, 'bounded workflow exhausted'):
            self.run_driver([('prepare-next-candidate','execute-prepared')], max_actions=1)
    def test_lock_required(self):
        with self.assertRaisesRegex(d.DriverRefused, 'canonical sender locks'):
            d.drive(coordinator=None,policy=None,observe=lambda:None,operate=lambda:None)
    def test_wrong_budget(self):
        with self.assertRaisesRegex(d.DriverRefused, 'invalid action budget'):
            self.run_driver([], max_actions=0)
    def test_prune_forbidden(self):
        result = self.run_driver([('select-next-candidate','select-next-candidate')])
        self.assertFalse(result['authorizes_prune'])
        self.assertFalse(result['authorizes_release'])

if __name__ == '__main__':
    unittest.main(verbosity=2)
