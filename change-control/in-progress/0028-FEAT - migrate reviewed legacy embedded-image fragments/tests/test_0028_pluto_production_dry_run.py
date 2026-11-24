#!/usr/bin/env python3
"""Offline test suite for the strictly read-only production dry-run wrapper."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
from unittest import TestCase, main, mock

SCRIPT=Path(__file__).resolve().parents[1] / 'tools/0028-pluto-production-dry-run.py'
spec=importlib.util.spec_from_file_location('run0028',SCRIPT)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class Tests(TestCase):
    def test_read_only_cli_modes(self):
        text=SCRIPT.read_text()
        self.assertIn("('preflight','probe','run')",text)
        self.assertNotIn('permit-production-apply',text)
        self.assertNotIn('--mode apply',text)
        self.assertNotIn('pg_restore',text)
        self.assertNotIn('mosquitto_pub',text)
        self.assertNotIn('CREATE TABLE',text)
    def test_docker_runner_uses_readonly_volumes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with mock.patch.object(m,'STAGE',root),mock.patch.object(m,'execute') as fake:
                fake.return_value=mock.Mock(returncode=0,stdout=b'PASS',stderr=b'')
                m.runner('rsmaxwell/diaries-responder:0.0.9-build-86',root/'output','dry-run',root/'cfg.json')
                command=fake.call_args[0][0]
            self.assertIn('container:diaries-postgres',command)
            self.assertIn('diaries-responder:ro',command)
            self.assertIn('--read-only',command)
            self.assertIn('--mode',command)
            self.assertIn('dry-run',command)
            self.assertNotIn('apply',command)
    def test_live_stage_hash_matches_expected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'reviewed').mkdir()
            j=root/'diaries-0028-reviewed-migration-fat.jar';j.write_bytes(b'test jar only')
            files={
                '0028-dispositions.csv':b'a', '0028-image-decisions.csv':b'b',
                '0028-v2-preservation-decisions.PRIVATE.csv':b'c',
                'PREPARATION-RESULT.json':json.dumps({'counts':{'CONVERT_TO_IMAGE':71,'DEFER':1,'links_preserved':30,'marquees_preserved':22},'productionApplyAllowed':False}).encode(),
            }
            for name,data in files.items(): (root/'reviewed'/name).write_bytes(data)
            (root/'reviewed'/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(val).hexdigest()+'  '+key+'\n' for key,val in files.items()))
            root.chmod(0o700)
            with mock.patch.object(m,'STAGE',root),mock.patch.object(m,'JAR',j),mock.patch.object(m,'MANIFEST',root/'reviewed'):
                m.validate_stage(hashlib.sha256(b'test jar only').hexdigest())
                with self.assertRaises(RuntimeError):m.validate_stage('0'*64)
    def test_no_jdbc_to_production_while_timer_active(self):
        with mock.patch.object(m,'text',return_value='active'):
            with self.assertRaises(RuntimeError):m.require_isolated()
    def test_files_config_contract_is_checked(self):
        text=SCRIPT.read_text()
        self.assertIn("original['diaries'].get('root') == '/data'",text)
        self.assertIn("original['diaries'].get('files')!='files'",text)
    def test_staging_path_is_transient(self):
        self.assertIn("/run/diaries-0028-production-migration-input",SCRIPT.read_text())
        self.assertNotIn("/run/user/",SCRIPT.read_text())
    def test_staging_script_uses_stable_private_run_dir_and_sudo(self):
        script=SCRIPT.with_name('0028-stage-private-dry-run.sh').read_text()
        self.assertIn("stage='/run/diaries-0028-production-migration-input'",script)
        self.assertIn('sudo -n install -d -m 700',script)
        self.assertIn('test ! -e',script)
        self.assertIn('sha256sum -c -',script)
        self.assertNotIn('mkdir -m 700 -p',script)
        self.assertNotIn('stage="/run/user/',script)
    def test_staging_script_does_not_remove_private_evidence(self):
        script=SCRIPT.with_name('0028-stage-private-dry-run.sh').read_text()
        self.assertNotIn('rm -rf',script)
        self.assertNotIn('docker compose',script)
        self.assertNotIn('systemctl start',script)
    def test_run_requires_pinned_jar_digest(self):
        with self.assertRaises(RuntimeError):m.validate_stage('not-a-hash')
    def test_output_is_private(self):
        self.assertIn('PRIVATE OUTPUT ON PLUTO (TRANSIENT)',SCRIPT.read_text())
    def test_no_jar_download_or_deploy(self):
        text=SCRIPT.read_text()
        self.assertNotIn('docker pull',text)
        self.assertNotIn('docker compose up',text)
        self.assertNotIn('systemctl stop',text)

if __name__=='__main__':main(verbosity=2)
