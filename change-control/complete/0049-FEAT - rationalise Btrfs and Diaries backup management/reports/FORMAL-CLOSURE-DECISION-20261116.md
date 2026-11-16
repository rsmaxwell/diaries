# 0049-FEAT — Formal feature closure decision (16 November 2026)

**Decision:** APPROVED — feature CLOSED.
**Feature:** Rationalise Btrfs and Diaries backup management (`0049-FEAT`).
**Approval provenance:** the feature owner explicitly stated in the Diaries project conversation on 16 November 2026: “I approve formal closure of 0049-FEAT.”
**Approval scope:** implementation, acceptance results, known limitations, published source revisions and documented rollback readiness.

## Accepted outcomes

1. The `diaries-backup-status` and `btrfs-backup-status` management interfaces are separated by application/infrastructure responsibility; human tables and operator JSON are consistently formatted. Current executable and timer naming has been rationalised without resetting the `.simple-*` persistent replication state files.
2. The sender (`mars`) and receiver (`backup`) were deployed and verified. The first post-0049 incremental replication ran through the dedicated 0041 `btrfs-send` service account and advanced the agreed parent to `20261116-150008Z` (received UUID `818b8956-76de-564f-8351-37cc89037d14`). Independent receiver inspection verified the snapshot is read-only and both parent records match.
3. The receiver retained two independent recovery holds and 27 historical receipts; the bounded prune preview selected zero deletions. A final Ansible reapply reported `changed=0` and `failed=0` on both hosts.
4. The feature source and evidence were published in three repositories. Playbooks and Ansible-controller publication occurred first; Diaries followed, with exact remote SHA verification.

## Published baseline accepted at closure

| Repository | Published `main` revision on approval |
| --- | --- |
| Playbooks (`rsmaxwell/playbooks`) | `a2508ad61f479c1b2bc20cb39896006c1f2906e1` |
| Ansible-controller (`rsmaxwell/ansible-controller`) | `a81eafdf1fccf6bcd7d9d1b3dfa77143872682e8` |
| Diaries (`rsmaxwell/diaries`) | `34be53fe219dbe773b516596e3d36fa5b29801bb` |

The Diaries SHA above is **the published pre-closure baseline**, not the yet-to-be-created closure relocation commit. The final commit and `git ls-remote` check must be recorded from the actual Windows Cygwin command output; do not insert an invented final SHA into this document. See `reports/REPOSITORY-REVISION-RECORD-20261116.md` for the full revision and rollback-reference details.

## Explicit accepted limitations / separate work

- `last verified transfer` remains `unknown` when no independent transfer receipt exists. The accepted live send/receive and identity checks are independent evidence and are not relabelled as a receipt.
- Two stale qgroups were observed on `mars` with qgroups_status `ok`; management of recurrence remains under **0039-DEF**.
- No production destructive prune, backup restore or live rollback was performed or required. Rollback readiness is documented, **not** a demonstrated rollback outcome.
- Internal `.simple-*` persistent state filenames remain deliberately unchanged to avoid unnecessary recovery risk.
- 0041 dedicated SSH and sudoers restrictions, retention limits and service schedules are preserved.

## Final closure administration

- **Implementation steps:** 1–4 **CLOSED** following the explicit owner acceptance above.
- **Historical evidence:** retain all reports, terminals, manifests and SHA-256 records unchanged (except the living feature status documents updated for closure).
- **Repository location:** move the **entire** feature directory from `change-control/in-progress/` to `change-control/complete/`, using Git on the authoritative Windows Diaries checkout. Stage only the old/new 0049 feature paths, commit, push `rsmaxwell/diaries` `main`, and verify that its remote SHA matches the new closure commit.
- **Commit/push status at document creation:** not yet executed. The terminal publication receipt is required to complete the Git audit trail; no success is assumed beforehand.
- **Other repositories and production:** no new Playbooks, Ansible-controller, inventory, application-submodule or live-host change is required for closure.

**Authorised result:** close 0049 after recording the feature relocation and published closure commit. This decision records the feature owner's approval, not an unobserved Git action.
