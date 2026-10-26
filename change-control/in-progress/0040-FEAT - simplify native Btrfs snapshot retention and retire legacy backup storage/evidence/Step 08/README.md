# 0040-FEAT — Step 08 evidence register

**Status: CLOSED — 25 October 2026 (accelerated acceptance; documentation prepared for application).**

## Gate and scope

Original Step 8: controlled non-destructive deployment and verification of shared manager in passive/dry-run mode; binary/hash parity, host configuration, source snapshot creation, receiving logic and receipts, real Ansible repeat-run `changed=0`, rollback availability and no received-snapshot changes caused by deployment.

The deployment and rollback evidence accepted under Step 7 is reused; no second production deployment or expensive full replication rehearsal was undertaken.

## Accepted evidence

- Playbooks revision `a8f857c` on `mango`, working tree clean. Under Step 7, `native-btrfs.yaml --limit mars,backup` completed: `mars ok=15 changed=2 failed=0`; `backup ok=20 changed=2 failed=0`. A later `--check --diff` returned `changed=0`, `failed=0` for both hosts. This establishes check-mode idempotency; a second actual apply was **not** recorded for this Step 7/8 installation.
- Host-local rollback copies created before deployment: `mars` `/home/richard/rollback/0040-step07-20261025-073634Z/` (4 files) and `backup` `/home/richard/rollback/0040-step07-20261025-073636Z/` (3 files). Original directory hierarchy preserved; restoration not tested.
- SHA-256 parity between Playbooks and installed executable on both hosts: shared manager `b3cfa6e6eab75e430e12238236f932944fdc50f045087e14da544f0d7e741ada`; `mars` native-push `98cbaddd5804febd198004080fd29c943b6450b37a8f55814953ac567a006480`.
- `mars` remains configured to require/create paired `root` and `@data`; runtime reports 63 complete timestamp sets, 0 incomplete, valid Diaries logical dataset `production`, backup ID `20261025-003218Z`.
- `mars` `btrfs-native-push.timer` remains enabled and active at 03:30 UTC, with last schedule on 25 October and next on 26 October. No schedule change recorded.
- `backup` receiver config remains in receiver mode with `receiver_prune_enabled=false`; `receiver-recovery-plan` reports `state=CLEAN`, `authorizes_repair=false`; `receiver-inventory` verifies 21 received snapshots with `problems=0`, most recent `20261025-030026Z`; `receiver-plan` reports `total=21 retention_keep=21 candidate_count=0 executable=false`.
- Recent receipt files present through `20261025-030026Z.json`. Receiver inventory validates snapshot/receipt identity under manager checks; previous Step 6 verified the received UUID correspondence for `20261024-030038Z`. A fresh exhaustive receipt-to-live-source audit was not performed.
- `richard`'s constrained `delete-receiver --snapshot *` sudo permission was explicitly retained and `visudo` passed. Existing source and receiver protections continue to apply.

## Limitations and decision

This is a non-destructive acceptance. No live pruning or `@data`-only source cutover occurred. The 21-snapshot post-deployment receiver inventory compared with the preceding 20-snapshot baseline is consistent with a new scheduled receive, **not proof by itself** that every preexisting snapshot identity remained unchanged; there is no observed deployment-related deletion or inventory problem. The accelerated plan waives another full cross-host deletion rehearsal. The qgroup stale count on `mars` (234 at last runtime check) remains a separate maintenance issue.

**Step 08 CLOSED — 25 October 2026**, subject to application of this record in the Diaries repository. Step 9 remains OPEN. No deletion or automatic receiver prune is authorised by this decision.

Evidence provenance: user-provided terminal outputs 20261025-073907, 20261025-074146, 20261025-082157 and earlier Step 6 evidence; Step 07 register and report.
