# 0035-FEAT Step 8 — Gate B reconciliation (15 October 2026)

**Status:** Gate A PASSED; Gate B evidence reconciliation PARTIAL; **Step 8 OPEN**.

## Current live evidence

On `mango`, the 0035 Step 8 Gate A source contract passed. Read-only playbook results: `mars=ok2 changed0 failed0`, `backup=ok2 changed0 failed0`, `pluto=ok2 changed0 failed0`. `mars` reported 52 complete paired timestamp sets, 0 incomplete, dry-run keep=52/delete=0; held checkpoint `20261013-171228Z`; pinned replication source `20261015-030004Z`. Verified history includes 45 occurrences of `20261009-154847Z` and 7 of `20261015-003023Z` (52 total). `backup` has 8 accepted received snapshots with matching receipts, UUIDs and parents; passive timers disabled. `pluto` reported verified publication `20261015-003023Z`, ext4 cleanup unsupported/no-op.

## Existing 0034-FEAT evidence (inherited, not re-executed)

The completed 0034 feature README states Step 11.3 disposable off-site recovery Gates A–D were **CLOSED** and accepted the schema-2 publication `20261015-003023Z` and native Btrfs incremental received snapshot `20261015-030004Z`; it also describes existing 0034 recovery and incremental push acceptance. This source bundle contains the README and implementation steps, but not the underlying Step 11.3 recovery transcripts. Treat this as **cross-referenced closure evidence**, not direct independent re-verification of the original recovery test.

The source implementation tests of 0035 Step 6 covered full/incremental transport and fail-closed protection; the Step 6 live-state capture checked accepted UUID identity, not an interrupted transfer.

## Gate B disposition

| Acceptance item | Evidence and decision |
|---|---|
| Timestamp GFS/current protection | Gate A live dry-run PASS, but boundary-driven actual prune still not exercised |
| History IDs map to restore source paths | Gate B1 PASS (2026-10-15): `show`/`path` verified on `mars` and `pluto`; matching manifest SHA-256; no host changes |
| Schema-2 disposable restore | Inherited from 0034 Gates A–D closure statement; underlying transcripts need correlation or controlled rerun |
| Replica safety and last parent | Current receipt UUID/parent state PASS; abnormal transfer loss scenario not live-tested |
| Storage pressure | No direct disposable test yet |
| Lost SSH or transfer interruption | No new controlled evidence; remains OPEN |
| Duplicate receive and stale parent | Source-regression coverage; disposable failure injection remains OPEN |
| Full-dataset hash `verify` | Not run in Gate A; defer until planned expensive verification |
| Transfer sizes and disk allocation | Not measured as part of these 0035 captures |

## Safety / next action

Deploy the *read-only* `verification/0035-step8/verify-history-lightweight.yaml` from the accompanying Playbooks patch and capture `/tmp/0035-step8-gate-b1.txt`. Design Gate B2 to run against disposable Btrfs loopback volumes; never interrupt scheduled `mars` -> `backup` replication or invoke production `prune --apply`. Do not mark Step 8 CLOSED yet.

## Gate B1 — ACCEPTED (15 October 2026)

Live transcript: `gate-b1-20261015-100244.txt`. Both `mars` and `pluto` passed all `show`/`path` assertions: `mars ok=5 changed=0 failed=0`; `pluto ok=4 changed=0 failed=0`. The production backup `20261015-003023Z` resolves on `mars` to `/media/usb/@snapshots/@data/20261015-030004Z/backup/pluto/.diaries-backup-generations/20261015-003023Z` and on `pluto` to `/home/richard/projects/diaries/data/.diaries-backup-generations/20261015-003023Z`. Both report manifest SHA-256 `c64f94a5211a16506838e74686ecd95acd56f56f8e98caff6e14c4a4a9ce4b65`. Earlier production backup `20261009-154847Z` also resolved. These are path and identity checks **not** a full schema-2 hash verification or a restore.

## Gate B2 — Disposable failure-injection acceptance (OPEN)

The companion Playbooks test uses temporary directories and fault injection against the receiver's production Python functions and the snapshot manager's retention policy. It exercises missing/mismatched receipts, duplicate destinations, stale parent, baseline/reseed checks, atomic receipt publication failure and retention boundary selection. Such tests prove the code-level safety decisions; they **do not** prove a real kernel Btrfs send/receive failure, capacity exhaustion, SSH interruption, or disk-level behaviour. Those integration cases need separate isolated Btrfs-volume evidence before acceptance. Never run these against `mars`, `pluto`, or `backup`.

**Gate A PASS; Gate B1 PASS; Gate B2 OPEN; Step 8 OPEN.**

## Gate B2 — loopback kernel integration tooling prepared (15 October 2026)

A new opt-in Playbooks script `verification/0035-step8/verify-gate-b2-btrfs-loopback.sh` tests **actual** Btrfs full/incremental send/receive, read-only/UUID identity, truncated stream rejection, missing-parent rejection and survival of previously accepted data, using two newly created temporary loopback volumes. It requires an isolated Linux VM with root/loopback support. **NOT RUN** at documentation time. Source-level `bash -n` validated only.

The production receiver uses fixed repository paths, source/receiver filesystem UUIDs and privileged endpoint configuration, so this disposable harness deliberately does not invoke it against test volumes. Receiver receipt-authorization tests remain evidenced only by the existing offline Python harness (12 PASS on `mango`, 2026-10-15). Real SSH loss, kernel ENOSPC, receipt publication under pressure, full schema-2 restore and measured stream/disk metrics remain OPEN. Prior 0034 Gates A–D recovery closure is inherited from the 0034 completion record, not independently rerun here. **Step 8 remains OPEN** pending real disposable execution and disposition of remaining scenarios.
