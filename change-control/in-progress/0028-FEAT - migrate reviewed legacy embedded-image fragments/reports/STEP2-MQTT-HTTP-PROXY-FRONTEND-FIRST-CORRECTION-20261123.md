# 0028-FEAT — Step 2 HTTP proxy frontend-first correction (2026-11-23)

## Trigger

The first `--resume-http` attempt for evidence `20261123T195519Z-mqtt-reader-replay` reported:

- `PASS: 71/71 retained MQTT Fragment topics match reviewed ...`
- `PASS: all 22 retained Marquee topics ...`
- `PASS: database/broker/responder/Reader remain on the isolated backend`
- `FAIL: proxy is not the only intended dual-homed HTTP gateway`

`docker ps` showed the labelled `diaries-0028-replay-http-proxy` running, but with `8081-8082/tcp` and **no localhost host-port bindings**. The previous script created it attached to the `--internal` backend and tried to attach the normal frontend afterward. That initial network choice did not establish the required published ports.

## Correction

The HTTP resume helper now creates a new gateway with the **normal frontend bridge first**, binds only `127.0.0.1:58081/58082`, connects the isolated backend **before** starting Nginx, and verifies the effective Docker port mappings and network membership afterward. The original broker, responder, Reader and migrated PostgreSQL database are never rebuilt or removed.

A stale proxy may be replaced automatically **only** if it has the expected 0028 label, `nginx:alpine` image, exactly the expected read-only Nginx configuration mount, no unexpected network membership, and no unexpected requested host-port bindings. It saves `docker inspect`/logs first and removes **only** `diaries-0028-replay-http-proxy`. A mismatched proxy fails closed.

If the proxy is already healthy, it is reused. The original successful MQTT receipts and migration journal are checked again; no new MQTT publications are performed.

## Offline verification

- Bash syntax: passed.
- Python regression tests: 18 passed (10 new proxy-state/startup tests and 8 updated existing HTTP gateway checks).
- Prohibited network and port configurations: rejected by synthetic tests.
- Existing dual-homed proxy with localhost mappings: reused by synthetic tests.
- Frontend-first create -> backend connect -> nginx start: verified in script tests.
- Real Docker HTTP test: **pending** owner application and execution. The previous MQTT and database test evidence remains valid.

## Next run — Windows PC, Cygwin

From the Diaries parent repository root:

```bash
bash 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tools/rehearse-0028-step2-mqtt-reader.sh' \
  --resume-http 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/evidence/Step 2/private/20261123T195519Z-mqtt-reader-replay'
```

This is an isolated, disposable **HTTP gateway-only** repair, not a production deployment or migration authorisation. Do **not** stop the separate `diaries-development-*` services or delete the isolated rehearsal database.
