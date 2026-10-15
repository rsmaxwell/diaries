# 0035-FEAT Step 6 — Integrate native send/receive safety

**Status:** CLOSED — 2026-10-15 (qualified integration-safety gate; deferred measurements and fault-injection tracked below).

## Scope and existing accepted architecture

- 0034 owns the operational `mars`-initiated push and the `backup` receipt-producing acceptor; 0035 validates that its native snapshot protections are compatible with source retention.
- Native accepted receipts are under `/@data/mars-received/.replication-state`, outside immutable received subvolumes; `/@data/backup` remains historical and untouched.
- The rsync `.diaries-snapshot-verified.json` is an application-level source snapshot validation marker, **not** the authority for a native receiver acknowledgement.
- Remote privileges remain restricted to `richard` invoking fixed root Btrfs endpoint roles; no additional sudoers rules or SSH direction changes are introduced.

## Source verification (completed locally on supplied 2026-10-15 source bundle)

- `verification/0035-step6/verify-source-contract.py`: 15 checks PASS, covering read-only source UUIDs, recipient acceptance, parent and candidate pins before send, no release after failed transfer, independently validated receipt, atomic receipt durability, locks, constrained privilege and pruning isolation.
- `roles/remote-backup/tests/verify-native-btrfs-push.py`: PASS — full/incremental source-side verification, parent and receipt guards.
- `roles/remote-backup/tests/verify-replication-protection.py`: PASS — missing/invalid protection fails closed.
- Joint read-only Ansible playbook syntax parsed successfully.

These are contract/regression checks, **not** a proof that a new native transfer was executed in Step 6.

## Live validation required before closure

Run the exact commands in `playbooks/verification/0035-step6/README.md` on `mango`. Save `/tmp/0035-step6-joint.txt` into this evidence directory after review. Verify source and receiver UUID alignment, existing accepted incremental parent, read-only state, independent receipts, checkpoint protection and no unexpected schedule change. A failed/missing receipt must never be interpreted as a usable incremental parent.

Cross-reference existing 0034 evidence for an accepted full baseline and accepted incremental receive, interrupted-transfer handling, independent application schema-2 validation and a disposable restore. Add observed Btrfs used/allocated space, and measured full and incremental stream sizes, or mark those measures explicitly unavailable. Do **not** infer physical extent equivalence across hosts from shared UUIDs or backup IDs.

## Deferred / prohibited operations

No new full/reseed, injected failed production transfer, `prune --apply`, receipt deletion, snapshot deletion or scheduler toggling is authorised by Step 6 verification. If any required interruption/race criterion has no preexisting evidence, leave that acceptance criterion OPEN and design a separate disposable controlled exercise. No Docker build is required.

## Closure reconciliation — 2026-10-15

**Formal disposition: CLOSED**, limited to integration of the native source protection/receipt mechanism with the currently deployed 0034 transfer. This does not imply that all independent destructive/fault-injection tests or measurement work have been repeated in 0035.

Captured on `mango` in `joint-capture-20261015-092933.txt`:

- All **15** joint source contract assertions PASS; native push full/incremental regression PASS; replication-protection regression PASS. These are source-level checks, not proof of a new live transfer.
- Read-only Ansible capture: `mars ok=2 changed=0 failed=0`; `backup ok=2 changed=0 failed=0`.
- `mars`: 52 complete paired timestamp sets, zero incomplete. Valid `production` schema-2 backup `20261015-003023Z`; checkpoint hold `20261013-171228Z` intact.
- Source replication protection: `20261015-030004Z` UUID `6f44e0e0-1968-6e4d-a3bd-9f77d71e9a47`, equal to observed read-only source UUID. Source native push timer remains enabled, 03:30 UTC, with 15 October last execution and 16 October next due.
- `backup`: eight accepted received snapshots and eight independent receipts; **zero unreceipted or missing**; every observed received UUID matches receipt source UUID and `ro=true`. Latest accepted `20261015-030004Z` matches `mars` protection. Its accepted predecessor is `20261014-100031Z`. Local receiver snapshot timers inactive/disabled.
- No sends, deletes, prunes, configuration changes or timer changes were made in this verification.

### Evidence inherited from 0034 (not repeated in Step 6)

The 0034 feature README records native full-baseline migration and an accepted **15 October** automated incremental push, with the verified production generation `20261015-003023Z`, received read-only snapshot `20261015-030004Z`, and matching independent receipt. Its Step 11.3 Gates A–D document disposable off-site recovery; Step 11.4 documents the unattended cycle and fail-closed writer-lock collision/recovery. These support normal transfer, acceptance and application restore but **do not amount to a newly injected interrupted full/incremental Btrfs stream test**. Original detailed source/evidence bundles should be retained as cross-references, not substituted by this short transcript.

### Deferred / evidence limitations (carry into Step 8, not treated as PASS)

- **Interrupted full and incremental streams, loss of acknowledgement, disk pressure and race injection:** specific destructive/failure scenarios were not executed as part of Step 6. Source regressions show fail-closed logic, but on-host fault-injection remains pending in an isolated/disposable test.
- **Transfer-size and Btrfs disk-allocation measurements:** no defensible full/incremental byte counts or before/after allocation measurements were present in the reviewed 0034 README and Step 6 capture. Do not assert transfer-efficiency or cross-host physical extent identity. Capture separate measurements when safe.
- **Send scope:** nested `@data/.snapshots` is inventoried on `mars`; its inclusion in the replicated stream was not tested here.

**Closure rationale:** the Step 6 *integration-safety* contract is demonstrably in force and its current live lineage is coherent. Outstanding fault exercises and quantitative acceptance checks are explicitly deferred to Step 8 / subsequent feature-wide acceptance; this closure must not be cited as proof of those checks. No host action or Docker image build required.
