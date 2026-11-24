"""Offline, Python 3.8-compatible safety tests for the isolated 0028 Editor setup."""
import base64
import hashlib
import importlib.util
import os
from pathlib import Path
import socket
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'tools'


def load_probe():
    spec=importlib.util.spec_from_file_location('editor_probe',str(TOOLS/'0028-editor-websocket-probe.py'))
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class IsolatedEditorSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.start=(TOOLS/'start-0028-step2-isolated-editor.sh').read_text(encoding='utf-8')
        cls.verify=(TOOLS/'verify-0028-step2-isolated-editor.sh').read_text(encoding='utf-8')
        cls.conf=(TOOLS/'0028-editor-isolated-gateway.conf').read_text(encoding='utf-8')
        cls.bridge=(TOOLS/'0028-editor-ws-bridge'/'bridge.js').read_text(encoding='utf-8')
        cls.dockerfile=(TOOLS/'0028-editor-ws-bridge'/'Dockerfile').read_text(encoding='utf-8')
        cls.cleanup=(TOOLS/'remove-0028-mqtt-replay.sh').read_text(encoding='utf-8')

    def test_editor_port_is_loopback_only(self):
        self.assertIn('-p 127.0.0.1:58083:8083',self.start)
        self.assertIn("'HostIp':'127.0.0.1'",self.verify)
        self.assertNotIn('-p 0.0.0.0:',self.start)

    def test_existing_reader_proxy_not_replaced(self):
        self.assertIn("main_proxy='diaries-0028-replay-http-proxy'",self.start)
        self.assertNotIn('docker rm -f',self.start)
        self.assertNotIn('docker network disconnect',self.start)
        self.assertNotIn('docker network rm',self.start)

    def test_only_rehearsal_broker_is_bridge_target(self):
        self.assertIn("const HOST = 'diaries-0028-replay-broker'",self.bridge)
        self.assertIn('const PORT = 1883',self.bridge)
        for banned in ('pluto.rsmaxwell.co.uk','localhost:9001','diaries-development-mqtt'):
            self.assertNotIn(banned,self.bridge)

    def test_mqtt_ws_path_and_binary_requirement(self):
        self.assertIn("path !== '/mosquitto/'",self.bridge)
        self.assertIn("offered.includes('mqtt')",self.bridge)
        self.assertIn('!isBinary',self.bridge)
        self.assertIn('maxPayload',self.bridge)

    def test_client_config_does_not_use_original_dev_endpoint(self):
        self.assertIn("'brokerMode':'proxy'",self.start)
        self.assertIn("'brokerProxyPath':'/mosquitto/'",self.start)
        self.assertIn("'responderBaseUrlMode':'same-origin'",self.start)
        self.assertNotIn("'brokerMode':'direct'",self.start)
        self.assertNotIn('ws://localhost:9001',self.start)

    def test_migrated_db_is_verified_not_recreated(self):
        self.assertIn('public.migration0028_source',self.start)
        self.assertIn('public.migration0028_image_occurrence',self.start)
        self.assertNotIn('pg_restore',self.start)
        self.assertNotIn('pg_dump',self.start)
        self.assertNotIn('docker create --name "$db"',self.start)

    def test_browser_proxy_has_expected_routes(self):
        for text in ('listen 8083','/mosquitto/','proxy_set_header Upgrade',
                     '/diaries-responder/diaries/','diaries-0028-replay-source-scans',
                     'diaries-0028-replay-responder','diaries-0028-replay-editor:8080'):
            self.assertIn(text,self.conf)
        self.assertNotIn('pluto.rsmaxwell.co.uk',self.conf)

    def test_nginx_editor_gateway_created_on_frontend_first(self):
        create=self.start.index('docker create --name "$proxy"')
        attach=self.start.index('docker network connect "$backend" "$proxy"')
        start=self.start.index('docker start "$proxy"')
        self.assertLess(create,attach)
        self.assertLess(attach,start)
        self.assertIn('--network "$frontend"',self.start)

    def test_no_docker_desktop_long_bind_mount(self):
        self.assertNotIn('type=bind',self.start)
        self.assertIn('docker exec -i "$editor"',self.start)
        self.assertIn('docker cp "$tools/0028-editor-isolated-gateway.conf"',self.start)

    def test_new_replay_resources_cleaned_only_with_explicit_confirmation(self):
        self.assertIn('--confirm-remove-isolated-replay',self.cleanup)
        for name in ('diaries-0028-replay-editor-proxy','diaries-0028-replay-editor-ws-bridge',
                     'diaries-0028-replay-editor'):
            self.assertIn(name,self.cleanup)
        self.assertNotIn('docker rm -f "$db"',self.cleanup)
        self.assertNotIn('diaries-0028-rehearsal-pgdata',self.cleanup)

    def test_verify_is_only_readonly(self):
        for forbidden in ('docker run ','docker create ','docker rm ', 'docker build ',
                          'drop table','update fragment','delete from','docker network create'):
            self.assertNotIn(forbidden,self.verify.lower())

    def test_bridge_has_no_exposed_docker_port(self):
        self.assertIn('EXPOSE 9001',self.dockerfile)
        self.assertIn('USER node',self.dockerfile)
        self.assertIn('ws@8.18.3',self.dockerfile)
        self.assertNotIn('-p 127.0.0.1:9001',self.start)

    def test_websocket_client_packets_are_masked(self):
        probe=load_probe()
        frame=probe.ws_frame(b'\x10\x00')
        self.assertEqual(frame[0],0x82)
        self.assertEqual(frame[1],0x82)
        self.assertEqual(len(frame),8)
        self.assertEqual(bytes(frame[i+6]^frame[2+i%4] for i in range(2)),b'\x10\x00')

    def test_websocket_framing_handshake_over_real_loopback_socket(self):
        probe=load_probe()
        srv=socket.socket()
        srv.bind(('127.0.0.1',0));srv.listen(1)
        host,port=srv.getsockname()
        errors=[]
        def server_thread():
            try:
                conn,_=srv.accept()
                with conn:
                    req=b''
                    while b'\r\n\r\n' not in req: req+=conn.recv(1024)
                    self.assertIn(b'Sec-WebSocket-Protocol: mqtt',req)
                    key=next(line.split(b':',1)[1].strip() for line in req.split(b'\r\n') if line.lower().startswith(b'sec-websocket-key:'))
                    accept=base64.b64encode(hashlib.sha1(key+b'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').digest())
                    conn.sendall(b'HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Protocol: mqtt\r\nSec-WebSocket-Accept: '+accept+b'\r\n\r\n')
            except Exception as e: errors.append(e)
            finally:srv.close()
        t=threading.Thread(target=server_thread);t.start()
        with probe.handshake(host,port) as conn:
            self.assertIsNotNone(conn)
        t.join(timeout=5)
        self.assertFalse(errors)

    def test_python_probe_rejects_server_masking(self):
        probe=load_probe()
        left,right=socket.socketpair()
        try:
            right.sendall(b'\x82\x80')
            with self.assertRaises(RuntimeError):probe.recv_ws_frame(left)
        finally:left.close();right.close()



class MqttV5ConnackParsing(unittest.TestCase):
    """Guard against assuming a five-byte properties-free CONNACK."""
    @classmethod
    def setUpClass(cls):
        cls.probe = load_probe()

    def test_actual_mosquitto_connack_with_properties(self):
        # Exact response from Windows Cygwin rehearsal on 23 November 2026.
        actual = bytes.fromhex('20 0e 00 00 0b 22 00 0a 27 00 1e 84 80 21 00 14')
        self.assertEqual(self.probe.require_successful_connack(actual), 11)

    def test_mqtt_v5_connack_without_properties(self):
        self.assertEqual(self.probe.require_successful_connack(bytes.fromhex('20 03 00 00 00')), 0)

    def test_nonzero_connack_reason_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'rejected'):
            self.probe.require_successful_connack(bytes.fromhex('20 03 00 87 00'))

    def test_connack_with_bad_packet_type_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'CONNACK'):
            self.probe.require_successful_connack(bytes.fromhex('30 03 00 00 00'))

    def test_connack_with_invalid_flags_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'Session Present'):
            self.probe.require_successful_connack(bytes.fromhex('20 03 01 00 00'))

    def test_connack_with_trailing_garbage_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'Remaining Length'):
            self.probe.require_successful_connack(bytes.fromhex('20 03 00 00 00 ff'))

    def test_connack_with_truncated_properties_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'properties length'):
            self.probe.require_successful_connack(bytes.fromhex('20 04 00 00 02 22'))

    def test_connack_with_incorrect_remaining_length_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'Remaining Length'):
            self.probe.require_successful_connack(bytes.fromhex('20 0e 00 00 00'))

    def test_connack_variable_byte_integer_over_127(self):
        # A large property section is encoded using a two-byte Remaining Length.
        props = bytes([0x26]) + b'\x00\x3d' + b'a'*61 + b'\x00\x3d' + b'b'*61
        # This test verifies length framing independently of broker-defined
        # semantics of the deliberately synthetic property bytes.
        self.assertEqual(len(props), 127)
        packet = bytes([0x20, 0x82, 0x01, 0x00, 0x00, 0x7f]) + props
        self.assertEqual(self.probe.require_successful_connack(packet), 127)

    def test_incomplete_variable_byte_integer_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'Truncated MQTT variable'):
            self.probe.require_successful_connack(b'\x20\x80')

    def test_overlong_variable_byte_integer_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'exceeds four bytes'):
            self.probe.require_successful_connack(b'\x20\x80\x80\x80\x80\x00')


if __name__=='__main__': unittest.main()
