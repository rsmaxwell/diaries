# Step 3 — actual manager disposable rehearsal driver

Prepared 23 October 2026. The new driver exercises the **internal** `receiver_delete_one_locked` manager function on mars under both manager and receiver writer locks. It streams authoritative source from mango without installing on mars. It exclusively targets `/media/usb/@data/0040-step03-manager-rehearsal`; any different config or paths fail closed. Its local, read-only source-parent UUID callback is **only a disposable stand-in**, not a production source-held pin; this does not certify trusted multi-host coordination.

Stages: `check` (non-mutating preflight) and `success` (destructive deletion of ONLY disposable `20261023-000001Z`, with durable journal and receipt cleanup). Protected parent `20261023-000003Z` remains untouched. A later separate stage will cover interrupted transactions and operator-gated recovery. The public receiver-prune interface stays disabled.

Acceptance pending actual Cygwin/mars terminal evidence; do not mark Step 3 CLOSED.

## Interruption extension (23 October 2026)

The updated regression driver retains the successful `success` test and adds these narrowly-scoped scenarios on disposable `20261023-000002Z`:

1. `interrupt-before` uses the actual locked manager transaction with an injected failure before Btrfs deletion; the production-format journal remains, and the manager must classify `BEFORE_DELETE`.
2. `inspect` is read-only, requires an expected interrupted state and asserts `authorizes_repair=false`.
3. `reset-before` is an **explicit state-changing** operator action permitted ONLY when recovery returns `BEFORE_DELETE`, snapshot and receipt both exist, and the journal exactly matches the pinned disposable identity. It cancels the injected test journal with directory `fsync`; it does not delete snapshot or receipt. This is not a production recovery facility.
4. `interrupt-after` makes a genuine Btrfs deletion of ONLY `20261023-000002Z`, injects a failure before receipt unlink, and asserts `AFTER_DELETE_RECEIPT_PRESENT`. It deliberately leaves the receipt and pending journal for inspection, with no automatic reconciliation.

**Execution sequence and gate:** `interrupt-before`, `inspect`, `reset-before`, `interrupt-after`, `inspect`. Run one stage at a time and review terminal evidence between stages. Do not rerun destructive stages after success. The driver streams manager source from mango and does not replace installed tools. Production receiver pruning remains disabled. Source protection in this driver remains a disposable-local stand-in, not an authenticated live source-held pin.

Previous `success` rehearsal **PASSED**, supported by user Cygwin log dated 2026-10-23 19:02; no claim is made that these new interruption scenarios have run yet.

## Controlled AFTER_DELETE reconciliation extension (23 October 2026)

Evidence from Cygwin `interrupt-after` and direct `mars` inspection at 19:09–19:10 confirms genuine Btrfs deletion of disposable `20261023-000002Z`, a preserved root-owned 0600 receipt and pending schema-1 journal, `AFTER_DELETE_RECEIPT_PRESENT` classification, and the protected parent `20261023-000003Z` intact with `ro=true`. The preceding `BEFORE_DELETE` test and operator-directed `reset-before` passed.

New `reconcile-after` **state-changing** operator command (NOT automatic repair) requires precisely `AFTER_DELETE_RECEIPT_PRESENT` for the pinned disposable candidate, exact journal and receipt identities, root-owned restricted files, absent deleted subvolume, verified received/source protected-parent UUID and receipt, and an independent checkpoint hold. The driver holds manager and receiver writer locks; only then unlinks/fsyncs the candidate receipt and calls the existing `receiver_journal_finish` implementation to durably clear the journal. It must finish in `CLEAN` while preserving the protected parent. This does not enable production pruning or a production recovery CLI.

Acceptance remains PENDING the actual `reconcile-after` terminal log and independent post-reconciliation inspection. Step 3 remains OPEN.

### Reconciliation preflight failure and corrective test-driver change (2026-10-23)

The first `reconcile-after` execution **failed safely before modifying the
receipt or journal**. The recovery classifier returned
`AFTER_DELETE_RECEIPT_PRESENT`, but the driver incorrectly called
`receiver_inventory(config)` before reconciliation. That routine correctly
rejects the deliberately orphaned candidate receipt and the pending journal
as unverified JSON files (`problems=2`). This is expected during recovery,
not evidence of corrupted Btrfs state.

The disposable driver now checks the surviving protected parent's received
UUID, read-only status and receipt, then invokes the unchanged manager's
`receiver_verified_checkpoint_holds()` on a *single verified protected-parent
entry*. This preserves the independent hold gate without requiring a clean
full inventory during an interrupted transaction. After journal and receipt
reconciliation, it runs the **full** receiver inventory and requires exactly
one verified snapshot (the protected parent), as well as a CLEAN recovery
state. No production manager or receiver-prune CLI is changed.

The repaired driver still requires live execution evidence before marking
reconciliation accepted or closing Step 3.

## Completed recovery evidence and bounded final verification (23 October 2026)

The corrected `reconcile-after` invocation was reported apparently stalled (Cygwin
log 20261023-191700). Independent mars inspection at 19:20 confirmed that
there were no remaining driver processes or lock holders; the interrupted
candidate subvolume, candidate receipt and pending journal were all absent,
and the protected parent remained read-only. Separate Cygwin streamed-manager
checks at 19:20–19:21 reported `RECEIVER-INVENTORY snapshots=1`, the
protected parent `20261023-000003Z` VERIFIED, `problems=0`, and
`RECEIVER-RECOVERY {"authorizes_repair": false, "state": "CLEAN"`.
This accepts filesystem reconciliation and recovery state, **not** successful
normal return of the driver. The precise cause of the apparent hang has not
been established. Do not repeat destructive rehearsal operations.

A non-mutating `verify-final` command was added. It requires the exact
isolated root-owned rehearsal configuration, both manager/writer locks, and
checks no pending journal, no candidate subvolumes or receipts, clean recovery,
exactly one verified received parent, the independent checkpoint hold, and
matching source/receiver parent UUIDs. The Cygwin SSH launcher now emits
flushed phase messages, sets 45-second source retrieval and 90-second
read-only verification deadlines (180 seconds for other scenarios), and kills
its **local SSH process group** if a deadline expires. On timeout the remote
state is explicitly UNKNOWN; SSH termination is not a guarantee of remote
process termination or rollback. Any mutating timeout requires independent
inspection, never an automatic retry. Production manager/sudoers are unchanged.

Acceptance for `verify-final` remains pending the user-executed command. Keep
Step 3 OPEN until that output is reviewed and the execution-reliability issue
is dispositioned in change control.

## Final acceptance and source retrieval output correction (23 October 2026)

The user-executed `python3 -u .../receiver-manager-disposable-rehearsal.py verify-final`
completed and returned to the Cygwin prompt (log `note(20261023-192603).txt`).
The final verification reported:

- Manager and receiver writer locks acquired in the expected order.
- `RECEIVER-RECOVERY {"authorizes_repair": false, "state": "CLEAN"}`.
- `RECEIVER-INVENTORY snapshots=1`, `VERIFIED 20261023-000003Z`, `problems=0`.
- `PASS: verify-final clean; one held protected parent; no pending journal or candidate receipts`.

**Disposition:** Accept disposable real-manager transaction and recovery testing:
genuine Btrfs send/receive, clean journalled deletion, interruption before
deletion and operator cancellation, interruption after deletion with retained
journal/receipt, independent physical verification, operator-directed
reconciliation, and final read-only verification. No repeat destructive test
or full restore is justified. The apparent stall of the earlier
`reconcile-after` invocation remains of *undetermined cause*. Its final
filesystem state was independently confirmed clean, and the final verification
terminated normally; do not describe that earlier invocation as a normal
command-level pass.

**Output correction:** The initial bounded SSH helper printed the entire
manager source returned by the successful `mango` retrieval (about 1,600
lines), obscuring useful verification output. The helper now accepts
`display_stdout=False` for that source-retrieval call only. It still returns
the retrieved bytes, surfaces stderr, preserves timeout and process-group
cleanup handling, and does not alter remote scripts, locks, files, or Btrfs
state. The normal `mars` verification output remains visible.

**Scope boundary:** These results accept the *disposable manager rehearsal*,
not production receiver pruning. The rehearsal source-pin callback was a
local stand-in, not a trusted source-held cross-host lease. The receiver
prune CLI remains fail-closed and production deletion must stay disabled
until live `mars`–`backup` coordination/lease guarantees, security review,
negative regressions and deployment gates are satisfied. Preserve Step 3
as OPEN for that remaining production coordination work; do not close the
overall 0040 feature.
