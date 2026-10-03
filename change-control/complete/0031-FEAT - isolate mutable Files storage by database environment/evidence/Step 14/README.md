# 0031-FEAT — Step 14 evidence

## Status

**COMPLETE — 2026-10-03.**

Step 14 — **Deploy the explicit production configuration non-destructively** — has been executed and verified successfully in production. The source implementation, deployment transcript, preflight, systemd activation and postflight evidence together prove that the explicit production storage configuration is active and non-destructive. See [`CLOSE-OUT.md`](CLOSE-OUT.md) for the completion decision.

## Implemented production change

The Diaries production Mosquitto configuration now uses:

```text
max_inflight_messages 20
max_queued_messages 0
```

This aligns production with the retained-snapshot correctness policy validated during Step 13 before the production responder is restarted. The Ansible copy phase validates both installed values before its restart handler can run. `max_queued_messages 0` remains an interim correctness safeguard; the later bounded retained-snapshot design follow-up is still required.

No database schema, Image row, catalogue object, persisted `Image.relativePath`, NAS Files bytes, browser `/files/...` route, or production Files selector is changed by this source implementation.

## Guarded production procedure

Playbooks now installs:

```text
roles/diaries/files/sync/scripts/step14-production-deployment.sh
```

The helper has two phases.

### `preflight`

Run while the Step 13 production responder write freeze is still active. It:

- requires `DIARIES_FILES_DIR=files`;
- verifies the deployed Compose path still selects `/data/files` from `${DIARIES_NAS_CONTENT_PATH}/${DIARIES_FILES_DIR}`;
- rejects `local.env` participation in the production start path;
- verifies the Step 8 production PostgreSQL dump and dataset sidecar still exist and match their recorded SHA-256 values;
- verifies the Step 8 Files rollback snapshot and its recorded inventory remain available on the NAS;
- records a secret-redacted production configuration review;
- captures deterministic production Image rows and a complete SHA-256 production `/data/files` inventory;
- captures a complete SHA-256 inventory of every `files-development-*` NAS root; and
- requires the production Image/File controls still to match the latest Step 13 AFTER control byte-for-byte.

### `postflight`

Run immediately after the normal Ansible Diaries deployment. It:

- requires every Compose service to be running and healthy where a healthcheck exists;
- requires the deployed and running broker to contain `max_inflight_messages 20` and `max_queued_messages 0`;
- waits for the current responder container start to log `synchronise: ok`;
- serves one existing catalogue object through `http://localhost:8081/files/...` and proves its bytes match `/data/files`;
- then briefly stops **only** `diaries-responder` for deterministic read-only durable-state verification;
- requires production Image rows and production Files inventory to be byte-for-byte unchanged from preflight;
- requires every `files-development-*` inventory to be byte-for-byte unchanged from preflight;
- reruns the existing Step 12 production reconciliation in dry-run mode and requires it still to match the Step 9 semantic baseline; and
- restarts the responder only after every check passes, then requires final service health, successful retained-tree synchronisation, and `/files/...` serving again.

If a durable comparison or reconciliation fails after the responder has been stopped, the helper deliberately leaves it stopped so writes do not resume on an unexplained production state.

## Authoritative runtime evidence

The successful production evidence identities are:

```text
preflight
  /home/richard/projects/diaries/data/0031-step14/preflight-20261003-090612

postflight
  /home/richard/projects/diaries/data/0031-step14/postflight-20261003-091828

post-deployment Step 12 reconciliation
  /home/richard/projects/diaries/data/0031-step12/production-20261003-091922
```

The exact supplied console transcripts are preserved under `runtime/console/`,
with an index and deployment-order note in [`runtime/README.md`](runtime/README.md).

The final postflight reported:

```text
PASS: Step 12 production reconciliation matches the Step 9 semantic baseline.
PASS: responder startup retained-tree synchronisation completed successfully.
PASS: Step 14 production deployment is healthy and non-destructive.
```

The timestamped helper-generated directories remain on `pluto`; because their
raw bytes were not supplied in the source bundle, this overlay records their
exact identities rather than inventing copies.

See [`CLOSE-OUT.md`](CLOSE-OUT.md) for the closure rationale and [`RUNBOOK.md`](RUNBOOK.md) for the deployment procedure.

