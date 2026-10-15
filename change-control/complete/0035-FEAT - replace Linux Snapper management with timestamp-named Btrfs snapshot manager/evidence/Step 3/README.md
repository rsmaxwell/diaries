# Step 3 — Receiver snapshot identity/retention (`backup`)

Status: **CLOSED — 15 October 2026** (source and live receiver verification passed).

Receiver contract and non-destructive verification: see `playbooks/verification/0035-step3/README.md`.

Observed in Step 1: filesystem `/dev/sda2` Btrfs UUID `b915f967-7cb4-4c14-b11b-f52209637a22`; received snapshots under `/@data/mars-received/@data`; eight receipt records ending `20261015-030004Z`; creation/prune timers disabled. The legacy `/@data/backup` remains preserved. Native receiver's acceptance validates received UUID and read-only flag; receipt metadata is stored outside immutable snapshots. Step 1 also found the unrelated local backup snapshot-manager verification path stale (`/@data/diaries-mars-replica/pluto`); this is a carried-forward finding, not a reason to alter the accepted native receipt repository.

The Step 3 retention decision is *no automated pruning of received snapshots* until a separately authorised algorithm can preserve the last common source/receiver incremental parent, respect send/receive locks, verify acceptance receipts and handle unknown/unaccepted entries safely. Local GFS root/@data retention is a distinct namespace.

Run `verification/0035-step3/capture-backup.yaml` read-only from `mango`, attach its transcript, reconcile every received UUID and acceptance receipt. **Closure decision:** The source contract and completed read-only `backup` capture satisfy the Step 3 identity/retention baseline gate. No receiver deletion, pruning, local timer activation, legacy migration, or live configuration edits are authorised. The separate stale local verification path remains deferred.


## Verified live evidence — 2026-10-15

- Source regression: **PASS, 9/9** (`separate receive root`, receipts outside received roots, received UUID check, readonly validation, accepted-parent requirement, shared writer lock, unaccepted-failure preservation, no auto-delete, read-only capture).
- `ansible-playbook verification/0035-step3/capture-backup.yaml --ask-vault-pass`: **backup ok=2, changed=0, failed=0, unreachable=0**. Full console transcript: `backup-receiver-20261015-084236.txt`.
- Filesystem: `/dev/sda2`, Btrfs UUID `b915f967-7cb4-4c14-b11b-f52209637a22`; receive root `/@data/mars-received/@data`. State directory `/@data/mars-received/.replication-state` is `0700 richard:richard`; writer lock is `0600 richard:richard`.
- Exactly **8** received snapshots and **8** acceptance receipts. `UNRECEIPTED=[]` and `MISSING_RECEIVED=[]`. Each receipt reports `matched=True`, `readonly=ro=true`, and `received_uuid=source_uuid`.
- Latest accepted: `20261015-030004Z`, source/received UUID `6f44e0e0-1968-6e4d-a3bd-9f77d71e9a47`, accepted parent `20261014-100031Z` (present). This matches the `mars` protected source UUID from Step 2.
- Receiver local snapshot timers and legacy Snapper timers observed disabled/inactive; Btrfs quota rescan not running at capture time.
- `/@data/backup` is preserved. No automatic received-snapshot cleanup has been enabled or authorised. The pre-existing receiver-local verification-path mismatch is carried forward for later remediation, and is distinct from native receiver acceptance.

**Decision: Step 3 CLOSED.** This closure validates the existing accepted receipt and lineage baseline; it does not constitute a destructive pruning rehearsal or evidence that future automatic receiver retention is safe.
