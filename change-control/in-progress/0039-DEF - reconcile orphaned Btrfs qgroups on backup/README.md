# 0039-DEF - Reconcile orphaned Btrfs qgroups on backup

## Type
Defect

## Status
In progress — Steps 1–2 CLOSED; Step 3 production remediation and post-repair replication acceptance PASSED 2026-10-22. Steps 4–8 require remaining gate reconciliation; defect NOT CLOSED. No OS upgrade authorised.

## 2026-10-22 current operational disposition (supersedes earlier no-mutation planning statements)

The operator subsequently explicitly authorised controlled qgroup destruction; the production operations have now been completed and independently reconciled. Historical sections below describing "no deletion authorised" were accurate when written but are **not the current status**. See `evidence/Step 03/STEP03-PRODUCTION-REMEDIATION-ACCEPTANCE.md` for observed counts, interrupted-batch reconciliation, journals and successful post-cleanup mars→backup receipt/lineage verification. This does not authorise new destructive work, filesystem upgrades or changes to retention and schedules. Root-cause recurrence/prevention and broader Steps 4–8 acceptance remain open.

## Priority
High — operational storage-accounting risk; no demonstrated replication failure or filesystem corruption.

## Opened
2026-10-21

## Summary
Investigate and safely remedy a very large disparity between Btrfs qgroups and existing subvolumes on off-site receiver `backup`, and fix the `btrfs-snapshot-manager status` diagnostic (`qgroups_status=unavailable;reason=unexpected_output`) only after its actual cause is established.

## Workflow registration
Following `change-control/README.md`: registered as next available ID `0039-DEF` under `todo`, with observed behaviour, desired outcome, scope and acceptance criteria; moved the complete record to `in-progress` to begin investigation on 2026-10-21. This package contains the *in-progress* state only; no host operations have been performed by this package. Maintain state transitions by moving the whole directory. Never mark a gate CLOSED from planned commands alone.

## Background and observed behaviour
After 0038-FEAT closed, `sudo btrfs-snapshot-manager status` on `backup` reported `qgroups_status=unavailable;reason=unexpected_output`. `sudo btrfs qgroup show /@snapshots` produced very many qgroups with zero referenced and exclusive bytes. Read-only measurement on 2026-10-21 reported **29,571 total**, **29,437 zero-sized**, **134 nonzero**, versus **133 listed Btrfs subvolumes**. The host reports **btrfs-progs v5.16.2** and **Linux 5.15.0-164-generic**. The attempted `btrfs quota status` returned `unknown token 'status'`: this is not a supported subcommand in the installed utility, not evidence of failed quotas.

The ratio strongly suggests stale/orphaned qgroups but **does not prove that each zero-sized qgroup is orphaned**. Existing source/receiver replication evidence remains valid. A zero qgroup can require contextual interpretation; subvolume-deletion-in-progress and level-0 versus higher-level qgroups must be distinguished. The parser failure was confirmed as an incompatible case-sensitive header check on older btrfs-progs output, corrected and deployed on `backup`. The underlying Btrfs qgroup persistence mechanism remains unproven.

## Expected behaviour
Quota accounting should have an understood and supportable relationship to surviving subvolumes and intentionally maintained qgroups. A safe, repeatable maintenance policy should prevent uncontrolled stale-record accumulation. The snapshot-manager status command should report a correct, bounded, actionable qgroup diagnostic without dumping tens of thousands of lines or breaking on supported output formats. Native mars-initiated send/receive and receipt verification remain unaffected.

## Reproduction / operator workflow
`backup` SSH terminal; read-only initial commands and commands in `evidence/Step 01/STEP01-RUNBOOK.md`. No credentials, unredacted filesystem data or raw 30k-line output should be checked into source. Preserve summarized evidence and exact version information.

## Evidence and analysis
- `note(20261021-075633).txt`: long qgroup listing, including zero entries and valid accounting for qgroup `0/55805` (received snapshot).
- `note(20261021-080412).txt`: 133 subvolumes; 29,571 qgroups; 29,437 zero; 134 nonzero; progs/kernel versions; unsupported `btrfs quota status`.
- 0038-FEAT accepted: native offsite incremental receive/receipt succeeded and manager reconciliation was idempotent; 0038 remains CLOSED.
- Confirmed: native and legacy deletion on `mars` can leave exact-ID stale level-0 qgroups; older `backup` output triggered an overly strict header parser. Kernel-level persistence and future automatic reclamation remain open.

## Scope
- **Primary:** `backup` Btrfs quota metadata and off-site receiver safety; compare `mars` only where useful and read-only.
- **Playbooks:** snapshot-manager diagnostic/parser, Btrfs snapshot/retention helpers, relevant Ansible role defaults and targeted regression tests **if evidence warrants changes**.
- **Diaries:** change-control docs and evidence; no planned client, responder, MQTT, PostgreSQL, images, web, or application code changes.
- **Out of scope without separately approved change:** filesystem upgrade, quota disable/re-enable, rescan, qgroup destroy/clear-stale, snapshot deletion/pruning, receiver reseed, restore, replication scheduler changes, retention changes, modification of receipts or historical 0038 records.

## Implementation plan
See `IMPLEMENTATION-STEPS.md`, `DESIGN-AND-SAFETY.md`, and step-specific runbook. Work **one acceptance gate at a time** with host/terminal, preconditions, command classification, observed output and rollback.

## Acceptance criteria
- [ ] Inventory level-0 and other qgroups; account for existing subvolumes, top-level ID 5 and pending deletions; distinguish orphans from intentional records; validate quota state using commands supported by installed tools.
- [ ] Identify mechanism/cause and whether new orphan records continue to accumulate, rather than assuming zeros are all stale.
- [ ] Confirm expected mars→backup receipt/received UUID/read-only and incremental parent preservation as pre/post invariants; do not require full restore or reseed when existing evidence suffices.
- [ ] Approve and document exact remediation with dependency/parent-safety analysis, rollback/recovery limitations, space/performance consideration, and independent operator gate prior to any mutation.
- [ ] Implement permanent Playbooks configuration/diagnostic/test changes where justified, with source regression and reviewed Ansible `--check --diff` before any deploy.
- [ ] Demonstrate bounded, understandable diagnostic and successful targeted regressions, then real deployment verification and idempotency if deployed.
- [ ] Record observations, Git revisions, remaining limits and evidence before moving directory to `complete`.

## Git references
Diaries accepted pre-defect baseline `06e9305728dd6b05225f9945f2eef971b6008cbe` (`0038-FEAT complete`). Playbooks accepted baseline `fc8233da3464aa114d69a2e34bd8990f96daf281` (`0038-FEAT - Step 8`). These are *last confirmed operator commits*, not independently verified current working trees. Recheck `git status` and HEAD before editing. Document future commits as observed.

## Deployment and rollback
No production changes in Step 1. Existing `/root/remote-backup-pre-reconcile/` contains 0038 predeployment program/config copies; it is **not** a rollback for Btrfs qgroup metadata operations. Never represent quota cleanup as automatically reversible. Preserve snapshots, receipts, replication parents and recovery options; require explicit approval and a specific stop/rollback plan before quota mutation.

## Completion summary / date
Not completed.

## 2026-10-21 investigation update (Step 1 accepted; Step 2 open)
- `backup`: 29,571 level-0 qgroups versus 133 listed subvolumes plus root ID 5; 29,437 unmatched IDs, zero usage and no parent/child relationships. Of these, 13,962 still have quota limits. No pending deleted subvolumes or active quota rescan. Source: `note(20261021-081546).txt`, `note(20261021-081652).txt`, `note(20261021-081914).txt`. These are orphan candidates supported by cross-checks, not an approved deletion set.
- `mars`: 39 unmatched qgroups explicitly show `<stale>` in `btrfs qgroup show -pcre`; 21 have 3.64TiB quota limits; relationship columns are `-`, not parent links. Source: `note(20261021-083102).txt`, `note(20261021-083733).txt`. Operator reports prior cleanup achieved zero stale qgroups but count is now growing again: **recurrence is a defect requirement**.
- Source review: Btrfs role applies qgroup limits; older unreferenced deletion helper disables filesystem-wide quota before deletion; native prune uses `btrfs subvolume delete`, and legacy prune invokes Snapper; no causal attribution established. Sources `note(20261021-082208).txt`, `note(20261021-082626).txt`, `note(20261021-082841).txt`.
- Platform baseline: `mars` Ubuntu 24.04.4 LTS / btrfs-progs 6.6.3 / running 6.8.0-138; `backup` Ubuntu 22.04.5 LTS / btrfs-progs 5.16.2 / running 5.15.0-164. Both report reboot required, no held packages. Detailed boot preflight in `evidence/Step 02/STEP02-FINDINGS.md`.
- Upgrading both hosts to current **supported** distribution-provided Btrfs utilities/kernel is an explicit **planning goal**, not a proven solution for recurring stale records. Distinct change/maintenance gates and rollback/access requirements apply, particularly to upgrading `backup` from 22.04 to 24.04.

## Step 02 — accepted deletion-correlation evidence (2026-10-21)
- Exact legacy Snapper deletion journal identities on `mars` match persistent stale qgroups: `20189` (Snapper 19629), `20237` (19677), and `20261` (19701), all retaining `3.64TiB` reference limits. Sources: `note(20261021-092113).txt` and `note(20261021-092525).txt`.
- `mars` stale count grew from 39 to **41**; the bounded inventory adds IDs `20917` and `20918`. Manager reported `qgroups_total=187`, `qgroups_stale=41`, `qgroups_under_deletion=0`, `qgroups_status=ok` (warning threshold currently 100).
- Since 2026-10-18 journal counts were 156 native `DELETE` lines and 3 legacy delete lines. These are journal event counts, **not** proof that native deletion caused any particular stale record.
- **Step 02 CLOSED on 2026-10-21:** native deletion correlation and parser compatibility are accepted. The deeper Btrfs lifetime mechanism is explicitly deferred to Step 3 risk analysis; no quota changes authorised. Preserve snapshot holds, replication pins, received UUIDs, and rollback options.
- `backup` OS update path: evaluate 22.04→24.04 first; 26.04 LTS is an additional separately gated option if justified and supported. OS upgrades and qgroup cleanup must not be combined.

## Step 2 formal closure — 2026-10-21

**CLOSED (diagnosis and diagnostic deployment acceptance).** Evidence: `evidence/Step 02/STEP02-CLOSURE.md` and original operator logs. At 10:15:09 UTC, naturally scheduled native prune on `mars` deleted subvolumes `20919` and `20920`, both subsequently listed as `<stale>` qgroups; stale count rose **41→43**. Legacy Snapper IDs `20189`, `20237`, `20261` had already been correlated. On `backup`, the repaired parser recognises the 5.16.2 lowercase heading, reports **29,571** qgroups without false `unexpected_output`, and the three local snapshot timers remain disabled. Both controlled Playbooks deployments (one installed executable changed on each host) and subsequent `changed=0` Ansible checks passed. **No OS upgrade or quota cleanup was performed.**

This closes the *diagnostic* gate, not the whole defect. The 29,437 unmatched level-0 qgroups are not an approved deletion set; `qgroups_stale=0` on old `backup` utilities reflects missing explicit markers, not health. Step 3 develops a version-independent inventory and safe remediation/recovery design before any destructive approval.

## Step 03 interim acceptance update — 2026-10-21

Read-only inventories and full operator-captured JSON manifests for `mars` and `backup` have passed isolated source tests, live output compatibility, count/ID uniqueness, classification and filesystem-identity verification. The evidence, exact summary figures, capture fingerprints and SHA256 values are indexed at `evidence/Step 03/STEP03-EVIDENCE-INDEX.md`. All evidence is held beneath the defect directory, not in a separate `mango` evidence tree.

**Step 03 remains IN PROGRESS:** no remediation has been authorised; permanent validator/fingerprint verification, replication/hold reconciliation, recurrence assessment and independent operator mutation gate remain open. The documentation ZIP does not contain the four large/small local inventory/identity captures already present in the operator's Windows checkout.

## Step 03 protection verification — 2026-10-21

Permanent offline validation passed for both full manifests; installed protection state was inspected, source/received `@data` UUIDs for three protected checkpoints matched, and all six protected `mars` snapshots plus three received `backup` snapshots were verified `ro=true`. The two original read-only property logs are archived at `evidence/Step 03/protection/{mars,backup}/`, with findings and checksums in `STEP03-EVIDENCE-INDEX.md`. Off-site replication intentionally sends only `@data`. **Step 03 remains IN PROGRESS** pending receipt/parent-chain review, recurrence analysis, and separately approved qgroup-specific remediation design. No mutation authorised.

## Step 03 receiver receipt and parent reconciliation (2026-10-21)

**Accepted observationally:** three protected `@data` checkpoints have receiver receipts with matching source and received UUIDs, filesystem identities and successful transfers; all three historic incremental parents are still present on `backup` with matching `received_uuid`. Two older parents have been pruned on `mars`, consistent with historical receipt lineage. The active `20261021-030006Z` parent remains pinned and accepted. Details and original logs: `evidence/Step 03/STEP03-RECEIVER-PARENT-RECONCILIATION.md`. **Step 03 remains IN PROGRESS; no qgroup removal authorised.**

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


## Accelerated Step 03 acceptance — 2026-10-22

**Step 03 CLOSED by documented operator risk acceptance.** The source-backed production remediation and manual post-remediation incremental send/receive passed, removing 29,437 orphaned `backup` qgroups and leaving zero unmatched after the new receive. See `evidence/Step 03/STEP03-PRODUCTION-REMEDIATION-ACCEPTANCE.md` and the closure disposition in `IMPLEMENTATION-STEPS.md`.

Recurrence prevention remains **unproven**. The operator intends to upgrade `backup` to Ubuntu 24.04 immediately after completion of 0039-DEF; that will be a separately gated change, with post-upgrade recurrence monitoring. No permanent automatic qgroup deletion is approved. Steps 4–8 and overall defect closure remain **OPEN** pending evidence/NA reconciliation and final change-control review.
