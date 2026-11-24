# 0028-FEAT — Isolated Editor MQTT v5 CONNACK verifier correction

Date: 23 November 2026  
Scope: read-only isolated Angular Editor verification tool and focused tests.

## Observed failure

Windows Cygwin log `note(20261123-212628).txt` recorded successful isolated Editor and WebSocket bridge builds, isolated same-origin runtime configuration, localhost-only port `58083`, and original manuscript `img2840` HTTP access. The final WebSocket MQTT CONNECT probe aborted with:

```text
FAIL: MQTT broker did not return v5 CONNACK: b'\x20\x0e\x00\x00\x0b"\x00\n\'\x00\x1e\x84\x80!\x00\x14'
```

These bytes, in hexadecimal, are:

```text
20 0e 00 00 0b 22 00 0a 27 00 1e 84 80 21 00 14
```

MQTT v5 CONNACK fixed header `20`, remaining length 14, acknowledge flags `00`, and reason code `00` indicate successful connection. The next byte `0b` denotes eleven property bytes, comprising Topic Alias Maximum, Maximum Packet Size and Receive Maximum. The original probe incorrectly required an exact five-byte encoding beginning `20 03 00 00`; that is only one valid success-response shape.

## Correction

Replace hard-coded MQTT CONNACK prefix and fixed offset checks in `tools/0028-editor-websocket-probe.py` with strict MQTT v5 packet framing checks: variable-byte Remaining Length, valid acknowledge/session flags for Clean Start, zero success reason code, variable-byte property length, exact packet boundaries and binary WebSocket opcode. This explicitly **does not** accept a rejected CONNECT, malformed or truncated packet. No changes to broker, WebSocket bridge, Editor, responder, Reader or database are required.

Add eleven parser regression cases to `tests/test_step2_isolated_editor_gui.py`, covering the exact observed broker response, properties-free success, rejection reason, invalid flags/packet types, truncated/inconsistent lengths, oversized variable-byte integer and multi-byte Remaining Length.

## Verification and next action

26 Python offline test cases passed, including the original 15 isolation tests and the 11 new MQTT parser cases. Python module compilation passed. ZIP scope includes only the probe, its tests, and this report. **Live Docker re-verification has not yet run.**

The labelled Editor containers are already running and must remain untouched. On Windows Cygwin, after applying the patch, run the existing read-only verifier from the Diaries parent checkout root:

```bash
bash 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tools/verify-0028-step2-isolated-editor.sh'
```

Do not rerun `start-0028-step2-isolated-editor.sh`, rebuild images, recreate the migrated PostgreSQL restore or rerun MQTT retained-topic replay. Manual Angular Editor GUI acceptance and formal feature gates remain open; production apply is not authorised.
