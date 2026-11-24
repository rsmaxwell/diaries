#!/usr/bin/env python3
"""Regression for isolated JWT secret's Java Base64 compatibility."""
import base64
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('0028-isolated-auth-secret.py')
spec = importlib.util.spec_from_file_location('auth_secret_0028', str(SCRIPT))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class IsolatedAuthSecretTests(unittest.TestCase):
    def test_standard_base64_secret_valid_for_java(self):
        for _ in range(50):
            secret = mod.new_standard_secret()
            self.assertTrue(mod.valid_standard_secret(secret))
            self.assertEqual(len(base64.b64decode(secret, validate=True)), 48)

    def test_unsafe_or_short_secrets_rejected(self):
        for candidate in ('', None, 'a-b_c', 'bad=', 'abc', 'c2hvcnQ=', 123):
            self.assertFalse(mod.valid_standard_secret(candidate))

    def test_future_fixture_generator_uses_java_compatible_secret(self):
        source = Path(__file__).with_name('0028-replay-verify.py').read_text(encoding='utf-8')
        self.assertIn("'secret':base64.b64encode(secrets.token_bytes(48)).decode('ascii')", source)
        self.assertNotIn("'secret':secrets.token_urlsafe", source)

    def test_repair_preserves_all_other_config_keys_and_original_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root/'responder.json'
            backup = root/'original.PRIVATE.json'
            original={'secret': 'a-b_c', 'db':{'database':'diaries_0028_rehearsal'},
                      'mqtt': {'host':'diaries-0028-replay-broker'},
                      'normaliseOnStartup': False}
            raw=json.dumps(original,indent=1).encode('utf-8')
            config.write_bytes(raw)
            after=mod.repair(config,backup)
            self.assertEqual(backup.read_bytes(),raw)
            self.assertTrue(mod.valid_standard_secret(after['secret']))
            self.assertEqual(after['db'],original['db'])
            self.assertEqual(after['mqtt'],original['mqtt'])
            self.assertEqual(after['normaliseOnStartup'],False)
            self.assertEqual(mod.load_config(config),after)

    def test_reject_valid_secret_without_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            config=root/'responder.json';backup=root/'old.json'
            config.write_text(json.dumps({'secret':mod.new_standard_secret()}),encoding='utf-8')
            content=config.read_bytes()
            with self.assertRaisesRegex(ValueError, 'already valid'):
                mod.repair(config,backup)
            self.assertEqual(config.read_bytes(),content)
            self.assertFalse(backup.exists())

    def test_refuse_backup_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);config=root/'responder.json';backup=root/'old.json'
            config.write_text(json.dumps({'secret':'a-b_c'}),encoding='utf-8')
            backup.write_text('precious',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'already exists'):
                mod.repair(config,backup)
            self.assertEqual(backup.read_text(), 'precious')
            self.assertFalse(mod.valid_standard_secret(mod.load_config(config)['secret']))

    def test_refuse_missing_and_symlink_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with self.assertRaisesRegex(ValueError,'missing'):
                mod.load_config(root/'missing')
            real=root/'real.json';real.write_text('{}',encoding='utf-8')
            link=root/'link.json';link.symlink_to(real)
            with self.assertRaisesRegex(ValueError,'symlink'):
                mod.load_config(link)


if __name__=='__main__': unittest.main(verbosity=2)
