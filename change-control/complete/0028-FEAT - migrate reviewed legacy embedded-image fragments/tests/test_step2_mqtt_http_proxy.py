#!/usr/bin/env python3
"""0028-FEAT offline regression checks for retained-only HTTP replay recovery."""
import re
import subprocess
import unittest
from pathlib import Path

F = Path(__file__).resolve().parents[1]
TOOLS = F / 'tools'


class HttpGatewayChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = (TOOLS / 'rehearse-0028-step2-mqtt-reader.sh').read_text()
        cls.resume = (TOOLS / 'verify-0028-step2-reader-http.sh').read_text()
        cls.cleanup = (TOOLS / 'remove-0028-mqtt-replay.sh').read_text()
        cls.nginx = (TOOLS / '0028-mqtt-http-proxy.conf').read_text()

    def test_bash_syntax(self):
        for name in ('rehearse-0028-step2-mqtt-reader.sh',
                     'verify-0028-step2-reader-http.sh',
                     'remove-0028-mqtt-replay.sh'):
            with self.subTest(name=name):
                subprocess.run(['bash', '-n', str(TOOLS/name)], check=True)

    def test_resume_before_initial_resource_collision_check(self):
        self.assertLess(self.runner.index("if [[ \"${1:-}\" == '--resume-http' ]]"),
                        self.runner.index("dedicated MQTT rehearsal containers/network already exist"))
        self.assertIn('exec bash "$tools/verify-0028-step2-reader-http.sh" "$2"', self.runner)
        self.assertNotIn('docker build', self.resume)
        self.assertNotIn('docker network disconnect', self.resume)
        self.assertIn('docker rm -f "$proxy"', self.resume)
        self.assertIn('refusing replacement',self.resume)
        self.assertNotIn('docker rm -f "$db"', self.resume)

    def test_proxy_is_only_dual_homed_service(self):
        self.assertIn('docker network connect "$backend" "$proxy"', self.resume)
        self.assertIn('docker create --name "$proxy" --network "$frontend"', self.resume)
        self.assertNotIn('docker network connect "$frontend" "$reader"', self.resume)
        self.assertNotIn('docker network connect "$frontend" "$responder"', self.resume)
        self.assertNotIn('docker network connect "$frontend" "$db"', self.resume)
        self.assertIn('nets!={backend}', self.resume)
        self.assertIn("set(p['NetworkSettings']['Networks'])!={backend,frontend}", self.resume)

    def test_loopback_only_effective_ports(self):
        for line in ('-p 127.0.0.1:58081:8081', '-p 127.0.0.1:58082:8082'):
            self.assertIn(line, self.resume)
        self.assertIn("bindings[0].get('HostIp')!='127.0.0.1'", self.resume)
        self.assertIn("bindings[0].get('HostPort')!=external", self.resume)
        self.assertIn("docker network inspect --format '{{.Internal}}' \"$backend\"", self.resume)

    def test_nginx_routes_exactly_two_internal_services(self):
        self.assertEqual(re.findall(r'listen (\d+);', self.nginx), ['8081','8082'])
        self.assertEqual(re.findall(r'proxy_pass (\S+);', self.nginx),
                         ['http://diaries-0028-replay-responder:8081',
                          'http://diaries-0028-replay-reader:8082'])
        self.assertNotIn('mosquitto', self.nginx)
        self.assertNotIn('pluto', self.nginx)

    def test_existing_mqtt_receipts_required_and_revalidated(self):
        self.assertIn('complete original MQTT replay receipts', self.resume)
        self.assertIn('validate-retained', self.resume)
        self.assertIn('validate-marquees', self.resume)
        self.assertIn('migration0028_source', self.resume)
        self.assertIn('migration0028_image_occurrence', self.resume)

    def test_post_proxy_readiness_and_samples(self):
        self.assertIn('http://127.0.0.1:58082/health/ready', self.resume)
        self.assertIn('http://127.0.0.1:58082/fragments/$fid', self.resume)
        self.assertIn('http://127.0.0.1:58081/files/$path', self.resume)
        self.assertIn('marquee_after', self.resume)

    def test_cleanup_is_label_guarded_and_db_preserved(self):
        self.assertIn('"$proxy" diaries-0028-replay-reader', self.cleanup)
        self.assertIn('refusing unlabelled HTTP frontend network', self.cleanup)
        self.assertIn('docker network rm "$frontend"', self.cleanup)
        self.assertNotIn('docker rm -f "$db"', self.cleanup)
        self.assertNotIn('docker volume rm ', self.cleanup)


if __name__ == '__main__':
    unittest.main(verbosity=2)
