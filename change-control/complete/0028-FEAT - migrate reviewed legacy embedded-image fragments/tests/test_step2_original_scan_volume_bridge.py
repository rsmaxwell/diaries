"""Offline contract/regression tests for 0028 Docker volume-backed source scans.

These do NOT touch Docker or the user's existing rehearsal. The real Docker
checks are performed by verify-0028-step2-source-scans.sh on Windows.
"""
from io import BytesIO
import hashlib
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
VERIFY=ROOT/'tools'/'verify-0028-step2-source-scans.sh'
CLEAN=ROOT/'tools'/'remove-0028-mqtt-replay.sh'


class SourceScanVolumeBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script=VERIFY.read_text(encoding='utf-8')
        cls.cleanup=CLEAN.read_text(encoding='utf-8')

    def test_shell_syntax(self):
        for path in (VERIFY,CLEAN):
            result=subprocess.run(['bash','-n',str(path)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)

    def test_labels_and_isolated_local_volume_only(self):
        self.assertIn("scan_volume='diaries-0028-replay-source-scans-volume'",self.script)
        self.assertIn('docker volume create --label "${label}=true" "$scan_volume"',self.script)
        self.assertIn("(v.get('Labels') or {}).get(label)!='true'",self.script)
        self.assertIn("v.get('Driver')!='local'",self.script)
        self.assertIn('attached to an unrelated container',self.script)

    def test_tar_stream_bypasses_windows_host_bind(self):
        self.assertIn('tar -C "$out/staged/diaries" -cf - . | docker cp - "$scan_loader:/data/diaries"',self.script)
        self.assertNotIn('staging_win=',self.script)
        self.assertNotIn('source=$staging_win',self.script)
        self.assertIn('--network none --label "${label}=true"',self.script)

    def test_docker_verifies_each_staged_file_hash_and_count(self):
        self.assertIn("docker exec -i \"$scan_loader\" sh -c 'cd /data && sha256sum -c'",self.script)
        self.assertIn('"$out/staged/SHA256SUMS.txt"',self.script)
        self.assertIn('actual_scans=$(docker exec "$scan_loader" find /data/diaries -type f',self.script)
        self.assertIn('volume contains unexpected symbolic links',self.script)
        self.assertIn('source-scans-container-probe-sha256.txt',self.script)
        self.assertIn('"$actual_probe" == "$expected_probe"',self.script)

    def test_sidecar_mounts_volume_readonly_no_host_ports(self):
        self.assertIn('type=volume,source=$scan_volume,target=/usr/share/nginx/html/diaries,readonly',self.script)
        self.assertIn('type=bind,source=$scans_conf_win,target=/etc/nginx/conf.d/default.conf,readonly',self.script)
        self.assertIn("if any(v for v in (d['NetworkSettings']['Ports'] or {}).values()):",self.script)
        self.assertIn("media['RW'] is not False",self.script)
        self.assertIn("media['Name']!=volume",self.script)

    def test_labels_verified_before_old_sidecar_replacement(self):
        old_check=self.script.index('scan_mode=$(python3')
        old_rm=self.script.index('docker rm -f "$scans"')
        self.assertLess(old_check,old_rm)
        self.assertIn('legacy-bind',self.script)
        self.assertIn('source scan server identity mismatch',self.script)
        self.assertIn('source-scans-volume-container-id',self.script)
        self.assertIn('source-scans-before-volume.PRIVATE.json',self.script)

    def test_no_automatic_overwrite_of_partial_existing_volume(self):
        self.assertIn('if [[ "$new_volume" == 1 || "$preexisting_scan_files" == 0 ]]; then',self.script)
        self.assertIn('[[ -z "$(docker ps -a -q -f "name=^/${scan_loader}$")" ]]',self.script)
        self.assertIn('existing scan loader',self.script)
        self.assertIn('sha256sum -c',self.script)

    def test_existing_database_mqtt_and_reader_are_not_replaced(self):
        for target in ('"$db"','"$broker"','"$responder"','"$reader"'):
            self.assertNotIn('docker rm -f '+target,self.script)
        self.assertIn('"$(psql_isolated \'select count(*) from public.migration0028_source\')" == 71',self.script)
        self.assertIn('Marquee records changed',self.script)

    def test_cleanup_requires_explicit_confirmation_and_label(self):
        self.assertIn('--confirm-remove-isolated-replay',self.cleanup)
        self.assertIn('refusing unlabelled original-scan volume',self.cleanup)
        self.assertIn('docker volume rm "$scan_volume"',self.cleanup)
        self.assertNotIn('docker volume rm "diaries-0028-rehearsal-pgdata"',self.cleanup)
        self.assertNotIn('docker rm -f "$db"',self.cleanup)

    def test_relative_tar_members_and_checksum_integrity(self):
        # Check that the tar stream has short relative member paths and that
        # its contents can be checked independently, unlike the host bind.
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)/'long'/'private'/'evidence'/'staged'/'diaries'
            diary=base/'diary-1828-and-1829-and-jan-1830'
            diary.mkdir(parents=True)
            fixtures={'img2839.jpg':b'original-test-page-2839', 'img2840.jpg':b'original-test-page-2840'}
            for fn,data in fixtures.items():
                (diary/fn).write_bytes(data)
            proc=subprocess.run(['tar','-C',str(base),'-cf','-','.'],capture_output=True)
            self.assertEqual(proc.returncode,0,proc.stderr)
            with tarfile.open(fileobj=BytesIO(proc.stdout),mode='r:') as tf:
                members=[m for m in tf.getmembers() if m.isfile()]
                self.assertEqual(2,len(members))
                for member in members:
                    self.assertFalse(member.name.startswith('/'))
                    self.assertNotIn('..',member.name.split('/'))
                    self.assertLess(len(member.name),130)
                    fn=Path(member.name).name
                    self.assertEqual(hashlib.sha256(fixtures[fn]).hexdigest(),
                                     hashlib.sha256(tf.extractfile(member).read()).hexdigest())

if __name__=='__main__':
    unittest.main(verbosity=2)
