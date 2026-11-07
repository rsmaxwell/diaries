#!/usr/bin/env python3
"""Offline install-contract regression; no Ansible execution or secret creation."""
import pathlib
import unittest

ROLE = pathlib.Path(__file__).resolve().parents[1]
TASKS = (ROLE / 'tasks/native.yaml').read_text()
DEFAULTS = (ROLE / 'defaults/main.yaml').read_text()

class Tests(unittest.TestCase):
    def test_disabled_by_default(self):
        self.assertIn('btrfs_agreed_parent_sender_proof_key_install_enabled: false', DEFAULTS)
    def test_vault_missing_fails_closed(self):
        self.assertIn('btrfs_agreed_parent_sender_proof_key is defined', TASKS)
    def test_exact_key_length(self):
        self.assertIn("match('^[A-Za-z0-9_-]{32}$')", TASKS)
    def test_both_roles_only(self):
        self.assertIn("inventory_hostname in ['mars', 'backup']", TASKS)
        self.assertIn("('source' if inventory_hostname == 'mars' else 'receiver')", TASKS)
    def test_permissions(self):
        self.assertIn('path: /etc/diaries', TASKS)
        self.assertIn("mode: '0700'", TASKS)
        self.assertIn("mode: '0600'", TASKS)
        self.assertIn('dest: /etc/diaries/btrfs-agreed-parent-sender-proof.key', TASKS)
    def test_never_logs_secret_or_diff(self):
        block=TASKS.split('- name: Agreed parent | Install shared sender-proof key without logging contents')[1]
        self.assertIn('no_log: true', block)
        self.assertIn('diff: false', block)
    def test_no_automatic_enable(self):
        self.assertNotIn('btrfs_native_push_schedule_enabled: true', DEFAULTS)
        self.assertIn('when: btrfs_agreed_parent_sender_proof_key_install_enabled | bool', TASKS)

if __name__=='__main__': unittest.main(verbosity=2)
