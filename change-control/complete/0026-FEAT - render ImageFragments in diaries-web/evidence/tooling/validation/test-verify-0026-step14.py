"""stdlib-only negative controls for the Step 14 verification harness."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import subprocess

p = Path(__file__).with_name('verify-0026-step14.py')
spec = importlib.util.spec_from_file_location('step14', p)
step14 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(step14)


class Step14HarnessTest(unittest.TestCase):
    def test_inventory_includes_application_source_but_not_secret_or_generated_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name, content in [('diaries-web/src/main/java/A.java', 'x'),
                                  ('scripts/windows/validation/verify.ps1', 'x'),
                                  ('diaries-web/build/cache.secret', 'password'),
                                  ('config/mosquitto/pwfile.txt', 'password'),
                                  ('diaries-client/node_modules/module.js', 'x'),
                                  ('diaries-client/public/assets/build-info.json', '{"buildDate":"generated"}'),
                                  ('scripts/windows/validation/__pycache__/verify.pyc', 'bytecode'),
                                  ('diaries-web/src/test/resources/fixture.json', '{}')]:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            found = step14.manifest(root)
            self.assertIn('diaries-web/src/main/java/A.java', found)
            self.assertIn('diaries-web/src/test/resources/fixture.json', found)
            self.assertIn('scripts/windows/validation/verify.ps1', found)
            self.assertNotIn('diaries-web/build/cache.secret', found)
            self.assertNotIn('config/mosquitto/pwfile.txt', found)
            self.assertNotIn('diaries-client/node_modules/module.js', found)
            self.assertNotIn('diaries-client/public/assets/build-info.json', found)
            self.assertNotIn('scripts/windows/validation/__pycache__/verify.pyc', found)

    def _xml(self, text):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        f = Path(temp.name) / 'TEST-suite.xml'
        f.write_text(text)
        return step14.xml_results(Path(temp.name))

    def test_xml_counts_and_skip_fail_closed(self):
        summary = self._xml('<testsuite name="com.example.ExampleTest" tests="3">'
                  '<testcase classname="com.example.ExampleTest" name="pass"/>'
                  '<testcase classname="com.example.ExampleTest" name="skipped"><skipped message="no Docker"/></testcase>'
                  '<testcase classname="com.example.ExampleTest" name="fail"><failure message="bad"/></testcase>'
                  '</testsuite>')
        self.assertEqual([summary[k] for k in ('tests', 'passed', 'skipped', 'failures')], [3, 1, 1, 1])
        with self.assertRaises(RuntimeError):
            step14.require_tests(summary)

    def test_missing_or_skipped_mqtt_is_never_a_pass(self):
        empty = self._xml('<testsuite name="com.example.Irrelevant"/>')
        with self.assertRaises(RuntimeError):
            step14.require_tests(empty, no_skips=True, classes=step14.SELECTED)
        skipped = self._xml('<testsuite name="com.rsmaxwell.diaries.web.mqtt.MqttProjectionIntegrationTest">'
                  '<testcase name="skip"><skipped message="Docker missing"/></testcase></testsuite>')
        with self.assertRaises(RuntimeError):
            step14.require_tests(skipped, no_skips=True)

    def test_required_integration_class_must_appear(self):
        summary = self._xml('<testsuite name="com.example.OtherTest">'
                  '<testcase classname="com.example.OtherTest" name="ok"/></testsuite>')
        with self.assertRaises(RuntimeError):
            step14.require_tests(summary, classes=step14.SELECTED)

    def test_compose_output_discards_rendered_secrets(self):
        # A realistic Compose response may contain credentials in environment
        # and CIFS driver options. Only allow-listed identity fields may persist.
        rendered = ('{"services":{"diaries-web":{"image":"diaries-web:local",'
                    '"environment":{"PASSWORD":"top-secret"},'
                    '"healthcheck":{"test":["CMD","true"]},'
                    '"depends_on":{"diaries-mqtt":{"condition":"service_healthy"}}}},'
                    '"volumes":{"nas-photo":{"driver_opts":{"o":"password=top-secret"}}}}')
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'compose.json'
            with patch.object(step14, 'command_output', return_value=subprocess.CompletedProcess([], 0, rendered, '')):
                value = step14.compose_check('docker', Path(temp) / 'compose.yaml', None, output)
            self.assertEqual(value['services']['diaries-web']['image'], 'diaries-web:local')
            self.assertNotIn('top-secret', output.read_text())
            self.assertNotIn('\"PASSWORD\"', output.read_text())
            self.assertNotIn('driver_opts', output.read_text())

    def test_missing_published_image_is_recorded_not_blocking(self):
        rendered = '{"services":{"diaries-web":{"image":"rsmaxwell/diaries-web:integration"}}}'
        calls = [
            subprocess.CompletedProcess([], 0, rendered, ''),
            subprocess.CompletedProcess([], 1, '', 'No such image'),
        ]
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'compose.json'
            with patch.object(step14, 'command_output', side_effect=calls):
                value = step14.compose_check('docker', Path(temp) / 'compose.yaml', None, output,
                                             inspect_images=True)
            inspection = value['services']['diaries-web']['imageInspection']
            self.assertEqual({'availableLocally': False}, inspection)


    def test_evidence_must_not_live_under_a_cleaned_build_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            web_build = base / 'diaries-web' / 'build'
            safe = base / 'build' / 'step14-run'
            with self.assertRaisesRegex(ValueError, 'must not be inside generated output'):
                step14.validate_evidence_location(web_build / 'step14-run', [web_build])
            self.assertEqual(safe.resolve(), step14.validate_evidence_location(safe, [web_build]))

    def test_binary_sha_and_manifest_are_stable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / 'diaries-web/src/main/java/Example.java'
            path.parent.mkdir(parents=True)
            path.write_bytes(b'one')
            first = step14.manifest(root)
            self.assertEqual(first, step14.manifest(root))
            path.write_bytes(b'two')
            self.assertNotEqual(first, step14.manifest(root))


if __name__ == '__main__':
    unittest.main(verbosity=2)
