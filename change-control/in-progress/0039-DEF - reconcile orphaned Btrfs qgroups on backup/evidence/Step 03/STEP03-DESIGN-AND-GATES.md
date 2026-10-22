# Step 03 — Remediation safety design and acceptance gates

**Status:** IN PROGRESS (design only; no production mutation).

## Decision and boundaries

Construct a bounded, reproducible **read-only** qgroup-to-subvolume inventory on each Btrfs filesystem, independent of whether installed btrfs-progs prints `<stale>`. Preserve source/receiver read-only flags, received UUIDs, replication parentage and `.replication-state` receipts, operator holds, timers and retention. A zero-use qgroup is *never by itself* sufficient approval for destruction.

## Required inventory design

1. Freeze filesystem identity, mountpoint, Btrfs version, kernel, quota rescan state, root subvol ID 5 and all live subvolume IDs; detect enumeration errors and concurrent changes.
2. Enumerate level-0 and higher qgroups with limits, usage, parent/child relationships and command-version header; compare **IDs**, not zero usage or string markers. Classify `active`, `unmatched candidate`, `related/protected`, and `ambiguous`.
3. Verify candidate exclusion of active/received subvolumes, pending deletes, parent-child links, valid limits and changing inventory; emit machine-readable bounded summary plus deterministic fingerprint and human review sample.
4. Create regression fixtures for btrfs-progs 5.16.2 and 6.6.3, 30k+ qgroups, ambiguous columns, failing commands, interrupted reads and concurrent-change detection. Tests must not mutate real filesystem state.

## Remediation options to evaluate (none authorised)

- **Observe only** with trend and operational monitoring if risk remains tolerable.
- **Individually verified qgroup cleanup** only if a supported installed command safely applies to proven candidates, with explicit single/bounded approval and revalidation immediately before mutation; no bulk inferred deletion.
- **Distribution-managed OS/Btrfs upgrades** as separately approved maintenance: backup 22.04 → 24.04 first, mars already 24.04; consider newer supported versions only on their merits, not as a proven cure. Ensure remote console, boot fallback and recovery tests.
- Never use quota disable/re-enable, rescan, unapproved qgroup destroy, filesystem repair or forced pruning as an exploratory test.

## Acceptance gate to proceed beyond design

Require precise proposed commands and installed-version semantics; receiver dataset/receipt and UUID invariants; qgroup relationship/limit safety; pre/post fingerprint, bounded batch size and stop conditions; backup-space and runtime risk; credible rollback/recovery **limitations** (quota metadata operations are not necessarily reversible); independent operator approval.

**Immediate next execution stage:** inspect qgroup and subvolume commands and source options on `mango` against accepted code; then implement the read-only inventory and isolated regression tests. Do not run a destructive command on `mars` or `backup`.

## Evidence status update (2026-10-21)

Initial read-only source/regression, live reconciliation on both hosts, full-manifest capture, saved-manifest internal validation and UUID/mount/idle-rescan identity capture are **accepted observational evidence**. See `STEP03-EVIDENCE-INDEX.md` for counts, fingerprints, source logs and file checksums. This supersedes the earlier "immediate next execution stage" instructions for merely implementing the initial inventory.

**Next gate:** implement and test a reusable offline validator of the captured manifests and fingerprint, then independently reconcile off-site replication receipts, read-only/received UUID ancestry and protected holds. Design review remains open and forbids all Btrfs mutations.

## Protection verification acceptance — 2026-10-21

The permanent offline validator passed against both complete manifests. `mars` requires and retains root-owned mode-0600 replication protection and checkpoint holds. Active replication pin `20261021-030006Z` and holds `20261013-171228Z`, `20261018-165453Z` resolve to existing protected source snapshots; their `@data` UUIDs match receiver `received_uuid` values on `backup`. Native off-site scope is `@data` only. Both sources at all three timestamps (`mars`, six snapshots) and received `@data` at the three timestamps (`backup`, three snapshots) returned `ro=true` in the original logs bundled in `protection/mars/` and `protection/backup/`. This accepts the *observed protection identity/property gate*, **not** a future incremental-send or qgroup-destruction safety guarantee. Receipt-state and parent-chain review, qgroup-specific exclusions and mutation/recovery approval remain open. No qgroup operation is authorised.

## Receiver-parent reconciliation result — 2026-10-21

Protected checkpoint receipts and three historical parent `received_uuid` references matched independent snapshot listings on `backup`. Two historical source parents are absent on `mars`; the newest source parent remains. The current pinned/accepted checkpoint exists on both hosts. This verifies *captured identity lineage*, not future transfer success or safe qgroup destruction. See `STEP03-RECEIVER-PARENT-RECONCILIATION.md`. Proceed with an offline, non-authorising qgroup safety assessment. **No mutation authorised.**

## 2026-10-21 — offline assessment and historical patterns (Step 03 open)

Both actual saved manifests passed the fail-closed offline safety assessor: `mars` 191 total (140 active-excluded, 6 protected, 24 limited, 21 unmatched investigation-only) and `backup` 29,571 total (131 active-excluded, 3 protected, 13,962 limited, 15,475 unmatched investigation-only). Source-fingerprint and SHA256 verification passed. No deletion commands were generated or authorised.

Read-only historical analysis found `backup` has 29,437 unmatched qgroups over IDs 276–55746, concentrated nearly continuously from ~27000 onward, with limited and unlimited records interleaved; near the end, odd limited/even unlimited IDs alternate. This *suggests* a repeated historical pair workflow but proves neither source nor eligibility. Current snapshot-manager pruning logs exact subvolume IDs before deletion and does not explicitly reconcile qgroups; its second deletion call is creation rollback. Native receiver failed-transfer destinations are left for inspection. Causality is unresolved.

See `evidence/Step 03/STEP03-OFFLINE-ASSESSMENT-AND-HISTORICAL-PATTERN.md` for exact sources, original logs and checksums. Both locally saved assessment JSON files remain in `evidence/Step 03/assessment/` and are not overwritten. **Step 03 IN PROGRESS; 0039-DEF OPEN; no production mutation authorised.**

## 2026-10-21 — Snapper-pair linkage and disposable stale-qgroup reproduction (Step 03 OPEN)

Seven surviving `backup` Snapper `@data`/`root` snapshot pairs have adjacent subvolume IDs, and the validated manifest shows `@data` at 1.00TiB max referenced versus unlimited `root` for all seven. Historical cleanup ran for both configurations. The 2026-10-21 `backup` baseline confirms no pending deletions and idle quota rescan. This strongly supports, but does not exhaustively prove, historical Snapper association of the 29,437 unmatched qgroups.

On an isolated 512 MiB loopback Btrfs filesystem on `mango` (UUID `8346c9fd-6dbb-45b6-94dc-e8b4728e2757`), successful synchronised deletion left **both** unlimited qgroup `0/257` and 1 TiB-limited qgroup `0/259` `<stale>`. A later read-only check showed 0 B usage for both while the 1 TiB limit remained. These results do not establish backup's exact Btrfs mechanism or safety of destroying any qgroup. Original logs and hashes, limitations and next acceptance gates are in `evidence/Step 03/STEP03-STALE-QGROUP-REPRODUCTION.md`. The disposable filesystem remains intact. **Step 03 / 0039-DEF IN PROGRESS; no production mutation authorised.**

## 2026-10-21 — disposable qgroup reconciliation Gates A–D (Step 03 OPEN)

On the identity-verified 512 MiB `mango` loopback Btrfs filesystem (UUID `8346c9fd-6dbb-45b6-94dc-e8b4728e2757`), the four guarded rehearsal gates **passed**. Gate A recorded live IDs and limits; Gate B destroyed only stale unlimited `0/257`; Gate C destroyed only stale 1 TiB-limited `0/259`; Gate D verified the exact three original active qgroup rows and the two active subvolumes remained, no deleted snapshot reappeared, no pending deletions/rescan, and read-only stale selection returned zero. See `evidence/Step 03/STEP03-RECONCILIATION-GATES-A-D.md` and original logs in `evidence/Step 03/reconciliation/mango/`. The separate SHA256 manifest uses defect-root-relative paths. This supports **disposable removal feasibility only**, not any production candidate eligibility or production remediation authorisation. Gates A–D accepted on observed outputs; preservation checksum verification in local checkout remains pending. **Step 03 and 0039-DEF stay IN PROGRESS**; do not dismantle test image yet.

## 2026-10-21 — offline investigation planner adversarial regression accepted (Step 03 OPEN)

The offline planner passed complete saved `backup` (29,571 qgroups) and `mars` (191 qgroups) baselines, five command-line negative tests, and **12 adversarial evidence-tampering regressions**. The first regression attempt exposed an unhandled manifest-validator exception; the subsequent targeted fix was verified by controlled `PLAN UNAVAILABLE:` errors for all 12 cases. Python compilation, source-evidence SHA256 unchanged, and `git diff --check` passed. Original successful terminal log, defect-root-relative SHA256 manifest, individual rejection cases and acceptance limits: `evidence/Step 03/STEP03-PLANNER-REGRESSION-ACCEPTANCE.md` and `evidence/Step 03/planner-regression/note(20261021-151658).txt`.

**Offline planner adversarial gate ACCEPTED; Step 03 remains IN PROGRESS.** Live protection, receipt/hold and fingerprint revalidation and any production deletion authorisation remain outstanding. This assessment does not approve production mutation. Evidence installation and checksum verification in the user's local repository are pending.


## Final Step 03 disposition — 2026-10-22

The earlier design-stage `IN PROGRESS` and `no production mutation authorised` statements on this page are **historical states**, superseded by the separately approved and executed production cleanup documented in `STEP03-PRODUCTION-REMEDIATION-ACCEPTANCE.md`. The original design and test evidence is retained unchanged.

**Step 03 CLOSED:** all 29,437 verified unmatched qgroups were removed, independent post-cleanup qgroup/subvolume checks passed and a new incremental `mars` → `backup` receive passed with zero unmatched afterwards. Residual recurrence risk is temporarily accepted. Ubuntu 24.04 upgrade and sustained qgroup recurrence assessment are deferred to a separately controlled follow-on change; the upgrade is not a proven preventative fix. No further Btrfs quota mutation or OS change is authorised by this documentation update. The full 0039-DEF stays OPEN until Steps 4–8 have been reconciled and accepted.
