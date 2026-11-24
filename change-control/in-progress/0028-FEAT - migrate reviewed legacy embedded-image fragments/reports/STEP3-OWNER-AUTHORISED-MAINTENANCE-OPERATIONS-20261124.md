# 0028-FEAT — Owner-authorised maintenance operations (bounded scope)

Prepared: 24 November 2026 after owner explicitly approved **temporary writer isolation, fresh protected PostgreSQL-and-Files backup, and a production DRY-RUN ONLY**. The owner has not authorised schema journal installation, the 71-conversion apply, MQTT replay, destructive restores, snapshot deletion, or permanent deployment changes. Step 1/Step 2 formal acceptance is still separate and open.

Source review: `diaries-sources-20261124-090430.zip`, `playbook-sources-20261124-084655.zip`, deployed fixed-capture checksum matching source, read-only pluto contract receipt `20261124T164217605036Z-controlled-window-contract`. Pinned responder `7aa6296`, parent `7e51b62`; these and the release JAR have previously passed acceptance checks. All previous datasets and test restores must remain untouched.

## Operator constraints

- Use **Windows PC / Cygwin** for `ssh` commands, working from the Windows Diaries parent. The scripts are executed via STDIN on the named remote host and do **not** require copying into permanent Playbooks roles or `/home/richard` on the remote. The private local evidence and logs remain under `change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/evidence/Step 3/private/`.
- The `pluto` control script does not run backups or the migration. It has four explicit actions: `preflight`, `isolate`, `status`, `reopen`. Its HBA rollback copy is retained in the PostgreSQL data volume until the window is accepted. It never mutates Git, MQTT or the database schema/data.
- **Do not begin isolation until** the recovery script has been inspected and the operator can remain at the terminals to complete or reopen the window. Stopping the responder interrupts production Editor and Reader functionality. If `sudo -n` is unavailable, `preflight` safely fails without mutations; do not work around this with unreviewed snippets.
- The script presumes timer **active/enabled**, backup publisher **inactive**, Compose and responder **active**, PostgreSQL host port 5433 dual-stack, and seven original HBA rules. It aborts on contract drift. It does not terminate an unknown active JDBC session, change PostgreSQL credentials or rewrite Docker Compose.
- PostgreSQL's container-local Unix socket is preserved for the installed `pg_dump`; non-loopback TCP is temporarily denied. A negative **IPv4** connection test and parsed IPv6 rejection rule are checked, but the 0028 script does *not* claim a live external IPv6 denial test. Separate NAS/Files-root writers must be excluded and verified independently. A successful tool output is not proof that nobody else can write directly to NAS.

## Phase A — Stage private dry-run inputs and run preflight WITHOUT production changes

Windows PC, Cygwin:

```bash
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
feature='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
python3 "$feature/tests/test_0028_pluto_maintenance_window.py"
python3 "$feature/tests/test_0028_receiver_rollback_hold.py"
python3 "$feature/tests/test_0028_pluto_production_dry_run.py"
bash "$feature/tools/0028-stage-private-dry-run.sh"
jar_identity="$feature/evidence/Step 3/private/20261124T151206Z-release-artifact/ARTIFACT-IDENTITY.txt"
hash=$(sed -n 's/^artifact_sha256=//p' "$jar_identity")
ssh pluto "python3 - preflight '$hash'" < "$feature/tools/0028-pluto-production-dry-run.py"
ssh pluto 'python3 - preflight' < "$feature/tools/0028-pluto-maintenance-window.py"
```

Record output and the printed `PINNED_0028_JAR_SHA256`. Offline preflight runs the Java CLI in a network-disabled disposable container, validates all 72 reviewed inputs, and checks the exact production Java 25 image and read-only Files mounts before an outage. It creates only temporary private input/result files on `pluto` under `/run/diaries-0028-production-migration-input` (mode 0700, owned by the SSH user; created with `sudo -n install -d` because `/run` is root-owned; persists between SSH sessions but not reboot); no database/service mutation. **No production outage is initiated by staging or preflight.** Confirm every source file was copied successfully before Phase B. The expected current JDBC count is one; it should disappear after stopping the responder. If any check fails, do not isolate.

## Phase B — Writer isolation (already scope-authorised, changes production)

First confirm operators have ceased production editing, no external NAS Files writer is active, and the backup publisher remains inactive. Windows PC / Cygwin:

```bash
ssh pluto 'python3 - isolate' < "$feature/tools/0028-pluto-maintenance-window.py"
ssh pluto 'python3 - status' < "$feature/tools/0028-pluto-maintenance-window.py"
```

This stores a byte-identical HBA rollback file, stops only the backup **timer**, stops the `diaries-responder` **Compose service**, inserts two temporary `reject` rules ahead of the general SCRAM rule, reloads PG, checks that new non-loopback IPv4 connections are rejected, and demands **zero other client sessions**. It leaves PostgreSQL and MQTT running. HBA loopback and Unix socket trust remain unchanged. **It is not safe to proceed to backup** until host/network ingress and all independent NAS writers have been accounted for and IPv6 rejection established to the operator's satisfaction. A failed check means **HALT**; do not proceed.

To reopen from a partial or completed isolation (Windows PC / Cygwin):

```bash
ssh pluto 'python3 - reopen' < "$feature/tools/0028-pluto-maintenance-window.py"
ssh pluto 'python3 - status' < "$feature/tools/0028-pluto-maintenance-window.py"
```

`reopen` restores original HBA bytes, reloads rules, starts only responder if stopped, and restores the timer's initial active state. The rollback HBA copy remains until reviewed cleanup. Verify responder health, MQTT connectivity and Reader/Editor after reopening. This is a recovery command, not proof that a previously attempted backup or dry-run passed.

## Phase C — Fresh matched DB-and-Files fixed capture (only after Phase B verified)

**pluto** via Windows Cygwin:

```bash
ssh pluto 'cd /home/richard/projects/diaries && \
  scripts/backup-dataset.sh fixed-capture-preflight && \
  scripts/backup-dataset.sh fixed-capture && \
  test "$(docker inspect -f {{.State.Running}} diaries-responder)" = false'
```

This is the *installed* script that matched the reviewed uploaded source. Capture uses the PostgreSQL local socket and a read-only Files source; the fixed published `diaries-backup/` is **mutable**. Inspect schema-2 manifest, verification marker, matching DB custom/plain dumps and Files inventory. The source script cannot prove independent NAS writers were absent just because the responder was stopped. If anything fails, **do not** treat the fixed published directory as a rollback point.

**mars** from Cygwin (after pluto capture accepted):

```bash
ssh mars 'sudo -n systemctl start diaries-pull.service && \
  sudo -n diaries-backup-status --limit 5'
```

The guarded pull receives/verifies the fixed dataset and marks it snapshot-eligible; it is **not** the immutable point by itself. Once latest backup ID and marker match `pluto`, choose an unused UTC timestamp and immediately hold the new snapshot. `btrfs-snapshot-manager create` prints the timestamp, and supports `create --timestamp`:

```bash
ssh mars '( stamp=$(date -u +%Y%m%d-%H%M%SZ); \
  sudo -n btrfs-snapshot-manager create --timestamp "$stamp" || exit 1; \
  sudo -n btrfs-snapshot-manager hold-add "$stamp" --reason "0028-FEAT production migration rollback" || exit 1; \
  sudo -n btrfs-snapshot-manager hold-list || exit 1; \
  echo "0028_ROLLBACK_STAMP=$stamp" )'
```

Record the **actual** `0028_ROLLBACK_STAMP`; never guess the timestamp. The snapshot/hold operation is approved creation/protection, not deletion. Retain the previous source snapshot and source data. If pull/hold fails, do not proceed to dry-run.

**mars** (after the local hold):

```bash
ssh mars 'sudo -n systemctl start btrfs-push.service && \
  sudo -n /usr/local/bin/btrfs-replication sender status'
```

Verify sender and receiver `state.parent.timestamp` equal `0028_ROLLBACK_STAMP` and the source/receiver snapshots' Btrfs IDs and manifest/dump/File data identities agree. The simplified sender selects the newest eligible snapshot per cycle; it is not enough that the command merely exited with status zero. The **backup** receiver hold is a separate operation.

**backup** receiver hold (exact timestamp from `mars`, Windows PC / Cygwin):

```bash
# Replace only the following value with the exact printed timestamp
stamp='YYYYMMDD-HHMMSSZ'
ssh backup "sudo -n python3 - hold '$stamp'" < "$feature/tools/0028-receiver-rollback-hold.py"
ssh backup "sudo -n python3 - verify '$stamp'" < "$feature/tools/0028-receiver-rollback-hold.py"
ssh backup 'sudo -n diaries-backup-status --limit 5'
```

The one-off helper acquires the manager/replication locks, validates receiver configuration, read-only snapshot and `Received UUID`, adds an atomic root-owned 0600 hold, and verifies retention's keep set. It never deletes snapshots or invokes a restore. Receiver mode deliberately does not expose `btrfs-snapshot-manager hold-add`; using its source-side command on backup will fail. **If the receiver hold or shared manifest hashes fail, no acceptable protected rollback point exists.**

## Phase D — One-shot Java 25 production dry-run (after both protected holds accepted)

The reviewed CLI's `validate-manifest` and `dry-run` modes make no DB writes. The one-shot runner uses the pinned Java 25 responder **image without replacing the production responder container**. It starts with a read-only filesystem, inherits the *stopped* responder's NAS volumes as read-only, joins `diaries-postgres`' network namespace for a container-local TCP connection and overrides only `db.host=127.0.0.1` and `db.port=5432` in a temporary 0600 config. The temporary config is removed on completion or failure. The client output directory is transient until copied to PRIVATE feature evidence on Windows.

Do **not** run Phase D until (a) PostgreSQL/Files writers remain isolated, (b) matching database+Files source snapshot on `mars` is held, and (c) the receiver snapshot's Received UUID is independently held on `backup` and hashes are reconciled. The runner cannot, by itself, attest to the holds on other hosts: the operator must bind these receipts first. No schema journal, MQTT replay, deploy or apply is authorised.

**Windows PC — Cygwin** (same `feature` variable as Phase A):

```bash
jar_identity="$feature/evidence/Step 3/private/20261124T151206Z-release-artifact/ARTIFACT-IDENTITY.txt"
hash=$(sed -n 's/^artifact_sha256=//p' "$jar_identity")
[[ "$hash" =~ ^[0-9a-f]{64}$ ]] || { echo 'FAIL: missing pinned JAR digest'; false; }

ssh pluto "python3 - probe '$hash'" < "$feature/tools/0028-pluto-production-dry-run.py"
# Run this ONLY after probe PASS and both independently protected rollback holds:
ssh pluto "python3 - run '$hash'" < "$feature/tools/0028-pluto-production-dry-run.py"
```

Expected: manifest validation PASS, dry-run `DRY_RUN_PASS`, reviewed conversions exactly 71 and deferred Fragment 1564. A failure is a STOP, not a reason to switch to a different JAR/config/backup or to run apply. The runner refuses existing output and checks all five prepared private input files and hashes. **DO NOT re-run it in the same transient directory** without reviewing earlier output.

Copy the private output off `pluto` **before any remote cleanup**:

```bash
stage="/run/diaries-0028-production-migration-input"
receipt="$feature/evidence/Step 3/private/$(date -u +%Y%m%dT%H%M%SZ)-production-live-dryrun"
mkdir -m 700 "$receipt" || exit 1
scp -qr "pluto:$stage/result" "$receipt/" || { echo 'FAIL: result copy incomplete'; false; }
find "$receipt/result" -type f -print0 | xargs -0 sha256sum > "$receipt/RESULT-SHA256SUMS.txt"
cat "$receipt/result/dry-run/result/summary.json"
```

Review the full dry-run plan, summary and hashes in the private 0028 evidence directory. Compare manifest/JAR identity, live DB identity, Files path, 71 conversions, the 1 defer, 30 URLs and 22 Marquees against the accepted review. The exact 71-conversion apply plan will require separate formal acceptance; **this dry-run does not authorise it**. Once evidence is safely copied and verified, clear *only the exact temporary staged directory on pluto*, with an independently reviewed command. No fixed dataset or Btrfs snapshot is part of that temporary directory.

## Completion and limits

After an accepted *dry-run only*, use `reopen` and verify production health; record all service states, retained snapshots, manifest hashes and private receipts. Formal Step 1/2 acceptance and separate production `apply` approval remain OPEN. Do not install SQL journals, apply conversions, alter MQTT retained objects, delete Files or destroy backups without additional explicit authorisation. If any stage fails or evidence is incomplete, keep the old rollback data intact and explicitly use `reopen` after confirming no partial schema/data writes have occurred.
