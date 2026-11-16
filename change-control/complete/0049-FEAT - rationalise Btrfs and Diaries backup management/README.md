# 0049-FEAT — Rationalise Btrfs and Diaries backup management

- **Type:** Feature
- **State:** CLOSED — FORMAL OPERATOR ACCEPTANCE GRANTED 2026-11-16; repository relocation and closure publication are the final administrative operation
- **Opened:** 2026-11-16
- **Ownership:** Diaries **parent** Git repository: feature planning, change control, test/evidence and closure. Permanent operational source, Ansible roles, templates and regression tests belong in the Playbooks repository on `mango`.
- **Hosts:** `mars` (collection, source snapshots, replication sender) and `backup` (replication receiver, received-snapshot retention).
- **Baseline:** Implementation uses updated 2026-11-16 source bundles, including 0041 service identity. Recapture host and Git revisions before deployment. Coordinate any overlap with 0048-FEAT; do not expand this feature into its permissions/source-mode work.

## Technical acceptance update — 16 November 2026

- The updated sender/receiver interface was deployed on `backup` first and then `mars`; the old push/prune units were removed and the replacement timers became active.
- A complete incremental transfer through `btrfs-push.service` advanced the agreed parent to `20261116-150008Z`. The receiver independently verified the matching received UUID, read-only snapshot, protected parent/prior, two independent holds and 27 preserved historical receipts.
- The final Ansible reapply returned `changed=0`, `unreachable=0`, `failed=0` on both hosts. No production pruning or restore was performed.
- Evidence: `reports/FINAL-TECHNICAL-ACCEPTANCE-20261116.md` and `evidence/Step 4/`.
- **Repository finalisation:** all three repositories were committed and published on 16 November 2026; exact revisions and remote checks are recorded in `reports/REPOSITORY-REVISION-RECORD-20261116.md`. **Formal closure approved on 16 November 2026.** The directory relocation and publication receipts are produced by the controlled closure operation.

## Publication and closure readiness — 16 November 2026

- **Playbooks:** `a2508ad61f479c1b2bc20cb39896006c1f2906e1` published to `rsmaxwell/playbooks` (`main`).
- **Ansible-controller:** `a81eafdf1fccf6bcd7d9d1b3dfa77143872682e8` published to `rsmaxwell/ansible-controller` (`main`), pinning that Playbooks commit. Private `inventory` pointer remains unchanged.
- **Diaries parent:** `34be53fe219dbe773b516596e3d36fa5b29801bb` published to `rsmaxwell/diaries` (`main`); application submodule pointers unchanged.
- **Formal closure:** explicitly approved by the feature owner on 16 November 2026; see `reports/FORMAL-CLOSURE-DECISION-20261116.md`. The final administrative operation relocates this complete history to `change-control/complete/` and publishes a Diaries-only closure commit.

## Objective

Provide a concise, consistent and discoverable backup-management interface on `mars` and `backup` without redesigning the accepted Btrfs replication, snapshot retention, Diaries publication/verification, or service-account security mechanisms.

Three agreed outcomes:

1. **Separate application data from infrastructure.** `diaries-backup-status` reports retained **Diaries dataset** backups and verification evidence only. Move qgroups, filesystem/snapshot-engine health, source pull/last accepted marker, off-site push/replication and agreed-parent information to the new, host-aware `btrfs-backup-status`.
2. **Retire historical scheme terminology.** Remove `simple`/`simplified` from current operator-facing command names, subcommands, systemd unit names, Ansible configuration identifiers, help, and active documentation. Replace historical `native-push` unit naming with `btrfs-push`, subject to preserving 0041 execution identities and access controls. Do not rewrite accepted historical evidence.
3. **Make all output legible and automation-safe.** Render lists as aligned tables with descriptive section titles and column headers, consistently aligned values and UTC timestamps. Pretty-print operator-facing JSON with stable documented structure; preserve internal protocol and stream framing.

## Target operator interface

| Command | `mars` | `backup` | Responsibility |
| --- | --- | --- | --- |
| `diaries-backup-status` | Yes | No | Brief Diaries dataset history, retained occurrences and correctly labelled verification evidence |
| `diaries-backup-history` | Yes | No | Detailed grouped/list/show/path/verify of Diaries backups |
| `btrfs-backup-status` | Yes | Yes | Concise backup infrastructure health; host-relevant sections; optional local-only inspection |
| `btrfs-snapshot-manager status/list` | Yes | Yes | Low-level Btrfs snapshot state and inventory |
| `btrfs-snapshot-manager create` | Yes | No | Local source snapshot creation |
| `btrfs-snapshot-manager prune --dry-run [--max-delete N]` | Yes | Yes | Read-only retention preview; host-specific safeguards |
| `btrfs-snapshot-manager prune --max-delete N` | Yes | Yes | Bounded retention deletion; strictly guarded and scheduled through configured units |
| `btrfs-snapshot-manager hold-*` | Existing sender functionality | No new receiver promise | Explicit source-side holds; no new privileges or receiver capability without a separately justified need |
| `btrfs-replication sender status` | Yes | — | Read-only sender/receiver relationship and candidate preflight |
| `btrfs-replication receiver status` | — | Yes | Read-only receiver state |
| `btrfs-clear-stale-qgroups` | Yes | Yes | Existing qgroup inspection/guarded maintenance, retained as a specialist command |
| `diaries-pull.service` | Yes | — | Execute the existing source collection and verification under its established service identity |
| `btrfs-push.service` | Yes | — | Proposed replacement of `btrfs-native-push.service`; execute under the **accepted 0041 identity/wrapper** |
| `btrfs-receiver-prune.service` | — | Yes | Proposed replacement of `btrfs-receiver-simple-prune.service`; run existing guarded retention |

These are the implemented interface names; their installation on `mars` and `backup` was confirmed by 16 November 2026 live read-back evidence. There must be exactly one active push timer and one active receiver-prune timer after cutover. Direct privileged replication protocol entry points are not a substitute for the 0041 service boundary.

## Scope

- Implement separate, read-only status summaries and appropriately documented `--json`, `--verbose`, `--local-only` (infrastructure) and `--limit` (Diaries) options.
- Standardise human-readable tabular output for lists in applicable existing backup tools (including grouped/ungrouped Diaries history, snapshot listings and receiver pruning previews). Do not wrap, truncate or silently alter critical identities; handle empty lists explicitly.
- Pretty-print JSON directly at **operator-facing** CLI boundaries (`indent=2`, deterministic ordering where applicable). Keep JSON on stdout and warnings/errors on stderr. Do **not** pipe internal RPC responses through `jq` or change line-based protocol/stream framing.
- Review and normalise exit-state reporting: success, degraded health and required-check failure for top-level status commands; preserve documented specialist exit behaviour (e.g. replication deferred status) unless explicitly covered by tests and callers.
- Remove Diaries-specific *presentation* from generic `btrfs-snapshot-manager status` while preserving all snapshot-creation eligibility and verified-marker safety checks.
- Rename active program, systemd/Ansible and operator subcommand identifiers; retire obsolete receiver commands only after checking all consumers. Unify the **operator-facing** prune preview/execution syntax while retaining existing receiver identity, journal, lock, hold, approved-state and deletion safeguards.
- Inventory `.simple-*` persistent agreed-parent/prune state paths. Prefer a controlled, atomic, reversible migration to neutral names where safe; if risk or consumers make a rename unnecessary/unsafe, retain internal filenames as a **documented exception** with no operator-facing exposure. Never reset or recreate agreed-parent state to achieve a rename.
- Update Playbooks installation/removal tasks, role docs, source regressions and service/timer descriptions to represent the final single scheme.

## Explicit exclusions

- No changes to the Btrfs send/receive algorithm, snapshot selection, agreed-parent meaning, receiver-ahead recovery, retry or lock semantics.
- No changes to retention buckets, schedules, maximum deletions, hold/receipt protection, snapshot contents, backups, verified dataset publication format or recovery policy.
- No changes to dedicated sender/receiver accounts, SSH restrictions, keys, sudoers, privileged wrappers or administrative recovery rights except strictly name-dependent updates required to preserve **exactly** the accepted 0041 security contract.
- No backup restoration, production snapshot deletion/reseed, destructive qgroup operation, or source-mode/permission redesign as part of a naming/reporting feature.
- No modifications to historic feature records, reports, tests or archived evidence to make old names disappear.

## Deliverables and control

- [`MANAGEMENT-INTERFACE-CONTRACT.md`](MANAGEMENT-INTERFACE-CONTRACT.md): command ownership, naming/semantic contract, output examples and migration decisions.
- [`IMPLEMENTATION-STEPS.md`](IMPLEMENTATION-STEPS.md): one coherent implementation and consolidated validation/deployment flow.
- [`tests/ACCEPTANCE-MATRIX.md`](tests/ACCEPTANCE-MATRIX.md): acceptance evidence and regression expectations.
- [`reports/BASELINE-SOURCE-REVIEW-20261116.md`](reports/BASELINE-SOURCE-REVIEW-20261116.md): original proposal baseline.
- [`reports/IMPLEMENTATION-SOURCE-20261116.md`](reports/IMPLEMENTATION-SOURCE-20261116.md): implementation, source regression and pending host gates.
- `evidence/`: source regression, deployment, live transfer, receiver read-back and idempotence logs supplied during 16 November 2026 acceptance. Preserve raw files under this feature. No evidence or script output is to be stored permanently in `/home/richard`, `/tmp`, or the Playbooks repo.

## Closure condition

All closure criteria were met and formal operator acceptance was granted on 16 November 2026. The approved closure operation moves the complete feature history to `change-control/complete/` without altering operational code or historical evidence. The actual relocation and publication are confirmed by the Git command receipt.
