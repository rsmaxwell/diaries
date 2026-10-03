# 0031-FEAT — Step 15 evidence

## Status

**COMPLETE — 2026-10-03.**

Step 15 — **Update architecture and operating documentation** — is complete. The effective database/Files pairing rule is now documented as normal architecture and operating practice rather than only inside the 0031 change-control material.

## Updated operator-facing documentation

### Diaries repository

- `README.md` — durable dataset invariant, isolated defaults, common-local override, stable `/files/...` contract, complete backup/restore and re-sharing warning.
- `ARCHITECTURE.md` — durable two-sided storage model, effective override selection, physical selector resolution, environment-neutral Image identity, backup/rollback consequence.
- `diaries-responder/README.md` — `diaries.files` leaf semantics, direct-Windows effective configuration, stable public route and matched database/Files requirement.
- `config/environments/local.env.example` — paired override rule, restoring isolated defaults, leaf semantics and destructive-operation warning.
- `scripts/windows/README.md` — normal local operating guide covering precedence, pair validation/reporting, direct responder configuration, backups, restores and rollback/re-sharing.

### Playbooks repository

- `roles/diaries/README.md` — production `diaries_files_dir` contract, explicit selector/mount semantics, production backup/restore and storage migration rules.
- `roles/diaries/files/sync/scripts/README.md` — production operating notes now begin with the normal durable-pair rule and matched recovery procedure before the historical 0031-specific helpers.

## Verification

A static review checked all Step 15 documentation requirements against the current configuration sources, including the three committed local defaults, `local.env.example`, production `.env.j2`, production Compose mount and read-only diary scan mount.

Result:

```text
Checks: 31, failed: 0
PASS: 0031-FEAT Step 15 architecture and operating documentation is complete and consistent with the current configuration sources.
```

See `verification-output.txt` and `DOCUMENTATION-MATRIX.md`.

## Runtime/data impact

None. Step 15 changes documentation only. It does not change database rows, mutable Files bytes, NAS layout, retained MQTT state, Compose runtime behaviour, Ansible rendering, responder code or production services.

See `CLOSE-OUT.md` for the completion decision.
