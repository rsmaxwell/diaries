# 0039-DEF - Reconcile orphaned Btrfs qgroups on backup

## Type
Defect

## Status
In progress — Step 1 CLOSED on 2026-10-21; Step 2 root-cause diagnosis IN PROGRESS. **No remediation or upgrade authorised.**

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

The ratio strongly suggests stale/orphaned qgroups but **does not prove that each zero-sized qgroup is orphaned**. Existing source/receiver replication evidence remains valid. A zero qgroup can require contextual interpretation; subvolume-deletion-in-progress and level-0 versus higher-level qgroups must be distinguished. The precise parser failure remains unconfirmed without the header/diagnostic command output and source-specific review.

## Expected behaviour
Quota accounting should have an understood and supportable relationship to surviving subvolumes and intentionally maintained qgroups. A safe, repeatable maintenance policy should prevent uncontrolled stale-record accumulation. The snapshot-manager status command should report a correct, bounded, actionable qgroup diagnostic without dumping tens of thousands of lines or breaking on supported output formats. Native mars-initiated send/receive and receipt verification remain unaffected.

## Reproduction / operator workflow
`backup` SSH terminal; read-only initial commands and commands in `evidence/Step 01/STEP01-RUNBOOK.md`. No credentials, unredacted filesystem data or raw 30k-line output should be checked into source. Preserve summarized evidence and exact version information.

## Evidence and analysis
- `note(20261021-075633).txt`: long qgroup listing, including zero entries and valid accounting for qgroup `0/55805` (received snapshot).
- `note(20261021-080412).txt`: 133 subvolumes; 29,571 qgroups; 29,437 zero; 134 nonzero; progs/kernel versions; unsupported `btrfs quota status`.
- 0038-FEAT accepted: native offsite incremental receive/receipt succeeded and manager reconciliation was idempotent; 0038 remains CLOSED.
- Working hypotheses (not yet proven): orphaned level-0 qgroups; old deletion/retention workflows; parser sensitivity or output/time cap; quota-rescan or rescan-state effects; qgroup relationship records. No root cause decided.

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
- **Step 02 remains IN PROGRESS:** account for native deletion correlation and the persistence mechanism before approving remediation. Preserve snapshot holds, replication pins, received UUIDs, and rollback options.
- `backup` OS update path: evaluate 22.04→24.04 first; 26.04 LTS is an additional separately gated option if justified and supported. OS upgrades and qgroup cleanup must not be combined.
