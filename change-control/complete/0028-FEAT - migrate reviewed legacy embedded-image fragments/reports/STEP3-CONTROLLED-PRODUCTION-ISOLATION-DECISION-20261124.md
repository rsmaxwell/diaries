# 0028-FEAT — Exact controlled production maintenance decision and rollback plan

Prepared: 24 November 2026. **Not an authorisation for production mutation.** Scope is Steps 3/4 only. This report supplements, rather than replaces, `STEP3-CONTROLLED-MAINTENANCE-AND-ROLLBACK-HANDOFF-20261124.md`. Evidence remains under the 0028 feature directory.

## Established facts (production receipts through 16:34 UTC)

- Git: published responder `7aa6296`, parent `7e51b62`, change-control files consolidated. The **pinned Java 25 fat JAR** has a private SHA-256 receipt. No permanent responder redeployment is required.
- PostgreSQL 18: `diaries-postgres` container; Compose `diaries-db`; host publishes 5433 on `0.0.0.0` and `::`; HBA local and loopback `trust`, final `host all all all scram-sha-256`. The loopback rules are confined to the **PostgreSQL container network namespace**, not the host's loopback. One idle JDBC client was observed on the last survey; the current session inventory must be rechecked after stopping writers.
- Compose: `diaries-responder` has `unless-stopped` restart policy and `/data/files` writable; `diaries-db` and `diaries-mqtt` should remain running. Stopping `diaries-compose.service` would bring down more services and is not an acceptable responder-only control.
- Backup timer `diaries-complete-backup-publish.timer` enabled/active; next scheduled 25 Nov 00:30 GMT. One-shot service calls `fixed-capture-preflight` then `fixed-capture` from `/home/richard/projects/diaries/scripts/backup-dataset.sh`.
- Source fixed capture uses PostgreSQL `docker compose exec -T diaries-db pg_dump` (local PG socket), host NAS Files and checksummed `rsync --delete` into mutable `diaries-backup/`. It preserves an **already stopped** responder's state. Its verified marker is revoked before copy and emitted only after manifest/files verification.
- `mars` `diaries-pull` fixed receive performs guarded source transfer, invalidates and then creates a verified snapshot-eligibility marker; it does **not** itself create a durable snapshot. Snapshot manager supports `create` and `hold-add <timestamp> --reason <reason>` on sender. Native replication is separate, and remote snapshot must be independently verified and protected.
- The previous retained full PostgreSQL restore passed; **only three Files samples were hashed**, not a full Files restore. No accepted production maintenance window, new recovery point or live dry-run exists.

## Production control design — after explicit owner authorisation only

| Operation | Exact target / contract | Safe reversal / failure action |
|---|---|---|
| Timer isolation | `pluto`: capture `systemctl show` original properties; confirm backup **service inactive**; then stop **timer only** | Restore initial active/enabled state precisely; do not disable/re-enable indiscriminately |
| Editor/RPC exclusion | `pluto`: prevent new Editor RPCs, safely drain; `docker compose --file /home/richard/projects/diaries/compose.yaml --env-file /home/richard/projects/diaries/.env stop diaries-responder` from that project directory | `docker compose ... up -d --no-deps diaries-responder` **only after** recovery/postflight. Do not stop the whole Compose systemd unit |
| DB TCP exclusion | `pluto`: **back up live `pg_hba.conf` byte-for-byte**, then carefully insert non-loopback IPv4/IPv6 `reject` rules before the general SCRAM rule; verify syntax, reload, verify actual blocked connection attempts from both family paths and all Docker peers | Restore **the exact original HBA bytes**, reload and prove ordinary SCRAM connections succeed. HBA reload does not disconnect pre-existing sessions: inspect and account for/terminate them separately with consent |
| Maintenance DB access | DB's **container-local Unix socket** continues supporting `pg_dump`. For Java 25 CLI, prepare an **isolated one-shot runner sharing the PostgreSQL network namespace** and an *ephemeral private config* that points DB host to `127.0.0.1:5432`, with the same production database/name/user and read-only `/data/files`. Test network, mounts and Files paths before use; do **not** reuse the responder service or publish the config | One-shot runner removed; private config removed after accepted results; retain only hashes and approved evidence. The loopback `trust` exception must be protected from unrelated Docker operators |
| Files exclusion | `pluto`/NAS: positively exclude all independent Files-root writers, not just responder; inspect `.image-staging` | Restore Files access only after DB+MQTT state accepted |
| Fresh backup | `pluto`: `scripts/backup-dataset.sh fixed-capture-preflight` then `... fixed-capture` **after writers isolated**; verify responder stays stopped, manifest/marker and matched Files | Failure leaves responder stopped; do not label mutable `diaries-backup/` a recovery snapshot |
| Immutable rollback | `mars`: run installed guarded `diaries-pull`, verify marker, `sudo btrfs-snapshot-manager create`, `hold-add <created-timestamp> --reason 0028-rollback`; replicate native snapshot with supported `btrfs-push` job. Verify same backup manifest/checksum and snapshot paths on **both** mars and backup; preserve hold/pin against prune | Do not delete or overwrite any older accepted backups. No destructive restore without separate owner authorisation |
| Dry-run | `pluto`: invoke one-shot JAR main via `java -cp` with `--mode validate-manifest`, then `--mode dry-run` against the **writer-stopped** production DB and read-only Files; output to new private folder. Compare exact 71 conversions, 1 deferred Fragment 1564, 30 URLs, 22 preserved Marquees, hashes and DB identity | Discard/review failed dry-run; keep isolation until safe restoration. **No journal SQL, apply or MQTT writes** at this stage |
| Reopen | Restore HBA, timer and service states *in inverse order* after dry-run and reviewed safety decision, or retain outage only with separate apply approval. Preserve fresh rollback snapshot | Confirm DB access, responder health, MQTT and Editor/Reader behaviour before considering the window closed |

**Caveat:** `pg_hba_file_rules` exposes *parsed effective rules*, not the original literal file bytes, include layout or current file permissions. The new read-only inspector records `SHOW hba_file` and deployed fixed-capture script SHA for the control review; it does **not** authorise or automate a configuration change. The `docker --network container:diaries-postgres` maintenance-runner method must be proved compatible with the pinned JAR/config before any live use. `pg_hba.conf` rules apply on **connection establishment**; a reload alone does not evict existing connections.

## Gate for *starting* writer isolation — separate scope-limited consent

Owner must accept a controlled temporary outage that may stop `diaries-responder`, suspend the backup timer, block DB TCP ingress and coordinate NAS writers, and authorise **creation (not deletion)** of a matching new recovery point and execution of a DB-read-only dry-run. This permission explicitly **excludes** creating journal tables, running `--mode apply`, replaying MQTT retained messages, deploying images, restoring data and deleting snapshots. Commands should be run in an existing SSH terminal to `pluto` or Cygwin `ssh pluto`, from `/home/richard/projects/diaries`, and on `mars`/`backup` only for their named backup/verification steps. On failure, keep writers excluded until the recovery/reopen decision is accepted.

After successful live dry-run: independent owner acceptance of the exact 71-conversion plan and 1 defer, actual recovery IDs and manifest hashes, Step 1/2 gates, and **separate approval for migration journal/apply**. A JSON `0028-apply-approval-v1` is not a substitute for a proven maintenance window.

## Read-only pre-maintenance command (Windows 11, Cygwin)

```bash
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
python3 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tests/test_step3_controlled_window_contract.py'
python3 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tools/inspect-0028-step3-controlled-window.py'
```

Expected: private `CONTRACT.json` and `READOUT.md`, no password printing, no service changes, `PRODUCTION APPLY NOT AUTHORISED`. If code differs from the uploaded source bundle, investigate before using its assumed restoration behaviour. Do not copy/paste the table's mutating commands until consent and exact environment checks are accepted.
