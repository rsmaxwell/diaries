#!/usr/bin/env python3
"""Read-only MQTT v5 CONNECT/CONNACK smoke through isolated Editor WebSocket.

Python 3.8-compatible. Does not subscribe, publish, authenticate a user,
or mutate database records. Checks the browser-facing HTTP-to-MQTT bridge.
"""
import base64
import hashlib
import os
import socket
import struct
import sys


def recv_exact(s, n):
    b = b''
    while len(b) < n:
        x = s.recv(n-len(b))
        if not x:
            raise RuntimeError('WebSocket closed unexpectedly')
        b += x
    return b


def handshake(host='127.0.0.1', port=58083):
    s = socket.create_connection((host, port), timeout=10)
    s.settimeout(12)
    key = base64.b64encode(os.urandom(16)).decode('ascii')
    request = ('GET /mosquitto/ HTTP/1.1\r\nHost: %s:%d\r\n'
               'Upgrade: websocket\r\nConnection: Upgrade\r\n'
               'Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n'
               'Sec-WebSocket-Protocol: mqtt\r\n\r\n') % (host, port, key)
    s.sendall(request.encode('ascii'))
    header = b''
    while b'\r\n\r\n' not in header and len(header) < 16384:
        chunk = s.recv(1)
        if not chunk:
            raise RuntimeError('HTTP closed before WebSocket handshake')
        header += chunk
    h = header.decode('latin1').lower()
    if not h.startswith('http/1.1 101 '):
        raise RuntimeError('WebSocket upgrade did not succeed: %r' % h[:250])
    accept = base64.b64encode(hashlib.sha1((key+'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode('ascii')).digest()).decode('ascii').lower()
    if 'sec-websocket-accept: '+accept not in h or 'sec-websocket-protocol: mqtt' not in h:
        raise RuntimeError('WebSocket handshake response identity mismatch')
    return s


def ws_frame(payload):
    # Client-to-server WebSocket frames MUST be masked (RFC 6455).
    mask = os.urandom(4)
    n = len(payload)
    length = bytes([0x80+n]) if n < 126 else (b'\xfe'+struct.pack('!H', n))
    masked = bytes(x ^ mask[i % 4] for i, x in enumerate(payload))
    return b'\x82'+length+mask+masked


def recv_ws_frame(sock):
    a, b = recv_exact(sock, 2)
    opcode = a & 0x0f
    length = b & 0x7f
    if b & 0x80:
        raise RuntimeError('Server masked its WebSocket frame')
    if length == 126:
        length = struct.unpack('!H', recv_exact(sock, 2))[0]
    elif length == 127:
        length = struct.unpack('!Q', recv_exact(sock, 8))[0]
    if length > 65536:
        raise RuntimeError('Unexpectedly large MQTT response frame')
    data = recv_exact(sock, length)
    return opcode, data


def mqtt_varint(packet, offset):
    """Decode an MQTT 5 Variable Byte Integer at offset (1-4 bytes)."""
    value = 0
    multiplier = 1
    for _ in range(4):
        if offset >= len(packet):
            raise RuntimeError('Truncated MQTT variable-byte integer')
        byte = packet[offset]
        offset += 1
        value += (byte & 0x7f) * multiplier
        if not byte & 0x80:
            return value, offset
        multiplier *= 128
    raise RuntimeError('MQTT variable-byte integer exceeds four bytes')


def require_successful_connack(packet):
    """Validate a full MQTT 5 CONNACK, including broker-provided properties.

    MQTT 5 permits a variable-length CONNACK properties section. It is not
    safe to assume that the Remaining Length equals three bytes, nor that
    a successful CONNACK has a five-byte wire encoding.
    """
    if not packet or packet[0] != 0x20:
        raise RuntimeError('MQTT broker did not send a CONNACK packet')
    remaining, pos = mqtt_varint(packet, 1)
    if remaining != len(packet) - pos or remaining < 3:
        raise RuntimeError('Invalid MQTT CONNACK Remaining Length')
    ack_flags = packet[pos]
    reason = packet[pos + 1]
    if ack_flags != 0:
        # This probe always uses Clean Start=1, so Session Present must be 0.
        raise RuntimeError('MQTT CONNACK has invalid Session Present / reserved flags')
    if reason != 0:
        raise RuntimeError('MQTT broker rejected v5 CONNECT (reason code 0x%02x)' % reason)
    props_length, props_start = mqtt_varint(packet, pos + 2)
    if props_length != len(packet) - props_start:
        raise RuntimeError('MQTT CONNACK properties length does not match packet')
    return props_length


def main():
    sock = handshake()
    try:
        client_id = b'0028-editor-probe'
        variable = b'\x00\x04MQTT\x05\x02\x00\x3c\x00'
        payload = struct.pack('!H', len(client_id)) + client_id
        rem = len(variable) + len(payload)
        if rem >= 128:
            raise RuntimeError('Probe packet unexpectedly long')
        connect = b'\x10' + bytes([rem]) + variable + payload
        sock.sendall(ws_frame(connect))
        opcode, data = recv_ws_frame(sock)
        if opcode != 2:
            raise RuntimeError('MQTT broker response was not a binary WebSocket frame (opcode %d)' % opcode)
        props_length = require_successful_connack(data)
        print('PASS: isolated Editor /mosquitto/ WebSocket accepts MQTT v5 CONNECT '
              'and returns successful CONNACK (%d property bytes)' % props_length)
    finally:
        sock.close()


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, ValueError) as error:
        print('FAIL: %s' % error, file=sys.stderr)
        sys.exit(1)
