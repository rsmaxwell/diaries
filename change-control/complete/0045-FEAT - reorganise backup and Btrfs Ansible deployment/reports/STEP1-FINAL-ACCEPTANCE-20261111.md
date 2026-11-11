# 0045-FEAT — Step 1 final acceptance: original installation freeze

**Date:** 11 November 2026. **Disposition: Step 1 CLOSED.** No Playbooks, inventory or managed-host installation was modified to obtain this evidence. Steps 2–4 remain OPEN.

## Accepted definitive baseline

The original, prior-to-refactor installation evidence is **`evidence/Step 1/baseline-20261111-111819Z/`**. Both manifests are schema `0045-static-installed-v2`. Earlier partial/v1 captures remain evidence of collector corrections, but must **never** substitute for the definitive v2 reference in the before/after comparison.

| Field | `mars` | `backup` |
|---|---:|---:|
| Managed-path entries (present and expected-absent) | 85 (61 present) | 56 (22 present) |
| Systemd service/timer unit entries | 12 | 12 |
| Package status/version entries | 11 | 11 |
| Cron principals | root and richard | root and richard |
| ACL root checks | 1 | 1 |
| Live snapshots complete/incomplete | 76 / 0 | 34 / 0 |
| Stale qgroups | 0 | 0 |
| Latest sampled relevant service result | success, exit 0 | success, exit 0 |

The source freeze records **Playbooks `main` `7dfa93fef6d975aa82f5f4cfdf54497b106e7645`**, clean against `origin/main` at capture. The Windows Diaries baseline and submodule readback are retained separately; the Step 1 evidence and corrected tooling were committed and pushed as **Diaries `bb91e33`** (11 November). Inventory authority remains **`/etc/ansible` on `mango`**, with `btrfs_native_endpoint_role` values `source` on mars and `receiver` on backup. 0046 inventory migration is a separate deferred feature.

The v2 manifest comparer was run with the definitive baseline on both sides and returned **PASS for both hosts**. This proves compatibility/readability of the capture and comparison schema, **not** post-refactor equivalence (which has not yet been attempted).

## Actual source-to-installed mapping: mandatory invariants

Source inspected: latest user-uploaded `playbook-sources-20261111-111917.zip`, with current 0044 names. The source bundle is a review reference; verify live `mango` HEAD and uncommitted changes again before modifying Playbooks.

| Source deployment mechanism | Installed asset family | Preservation requirement |
|---|---|---|
| `roles/local-backup/tasks/install_machine_scripts.yaml`: scoped `synchronize`, rendered templates, cron | `/root/scripts/backup/**`, `/root/log/backup`, root backup cron | Preserve installed scripts, existing include/exclude files, template output and cron exactly; exclude `diaries-pull.py` from generic root sync |
| `roles/local-backup/tasks/install_user_scripts.yaml`: scoped `synchronize`, templates, user cron | `/home/richard/scripts/backup/**`, `/home/richard/log/backup`, richard cron | Preserve file hashes/modes and existing extra legacy/rollback files; never use a blanket `--delete` in this refactor |
| `roles/local-backup/tasks/diaries_pull.yaml` and `source_snapshot_access.yaml` | Diaries pull executable, timer/service, writer lock, backup directories and source ACL | Preserve user ownership, opt-in rules, writer-barrier semantics, ACLs and scheduled time |
| `roles/snapshots/tasks/main.yaml`: `copy`, template, hold initialisation, preflight and timer activation | `/usr/local/sbin/{btrfs-snapshot-manager,diaries-backup-history,btrfs-extent-sharing}`, `/usr/local/lib/diaries-backup`, `/etc/btrfs-snapshot-manager.json`, snapshot service/timer units and holds | Source-only role guard and Btrfs subvolume validation must remain; hold file is `force: false`; installation before preflight/activation |
| `roles/btrfs-replication/tasks/native.yaml`: endpoint-conditioned copy, template and guarded activation | `/usr/local/bin/btrfs-simplified-replication`, source push units, receiver retention/config/prune units and protected `.replication-state` | Preserve source/receiver split, configuration contents, exact timer states, read-only identity checks, checkpoint receipts, locks and mode/owner |
| `roles/btrfs-replication/tasks/qgroup-maintenance.yaml`: endpoint-neutral shared helper | `/usr/local/sbin/btrfs-clear-stale-qgroups`, `/etc/btrfs-stale-qgroups.json`, qgroup service/timer | Same source, endpoint-specific rendered content, schedule and enabled state |
| Previous installed files/units and explicit `state: absent` guards | Retired sudoers and executables **absent**, receiver snapshot units **still present**, `/root/scripts/backup/remote/**` **still present** on mars | **Do not infer that removing obsolete operator playbooks permits deleting installed assets.** Current installation equality means preserving these observed states unless separately authorised |

## Caller/entry-point review and mandatory Step 2 check

Current tracked source includes `local-backup.yaml`, `remote-backup.yaml`, `btrfs-replication.yaml`, `snapshots.yaml`, `scripts/local-backup.sh`, `scripts/remote-backup.sh` and `scripts/snapshots.sh`. In the supplied source, `remote-backup.yaml` still runs default `btrfs-replication/tasks/main.yaml` (which includes the source `snapshots` role), whereas `btrfs-replication.yaml` explicitly invokes `native.yaml`. These are **not equivalent entry points**. The receiver/source safety guard must not be weakened.

Tracked references include current `AGENTS.md`, role documentation and historical `verification/0034-*` documents. Historical records must not be rewritten for renamed entry points; active operator docs must be updated. Step 1 source review cannot establish that no external Jenkins job, cron task, administrator automation, or script invokes the old entry points. **Before removal in Step 2**, perform and record the live caller audit; redirect all required callers to the correct new interface. This is a hard pre-deletion gate, not an invitation to delay the completed installation freeze.

## Comparison rules and exceptions

- Compare static installed program/config/unit SHA-256; owner/group/mode; expected-absent assets; units' loaded command fingerprints and calendar/timer state; relevant packages, cron, mounts, and ACL fingerprints.
- Exclude generated Python bytecode, `__pycache__` and other disposable artifacts only within the scoped backup script trees. Do not ignore differences in managed system paths, credentials, sudoers, or permanent user files.
- Persistent dataset contents, changing snapshots, mutable protection receipts and operational counters are **not** frozen. Their state and protection must remain valid, checked separately without moving/restoring/deleting backup data.
- Any post-implementation difference requires explicit cause and correction; an Ansible `ok`/`changed=0` summary alone is insufficient.
- Receiver checkpoint holds, agreed-parent state, source-side writer lock, subvolume boundaries, and no dual transport remain mandatory safety invariants.

## Closure decision and next work

The pre-change snapshot of source, effective inventory topology and installed state is complete, reproducible and safely stored. **Step 1 accepted and CLOSED.** Start Step 2 as one coherent Ledger-style refactor; retain Playbooks current SHA as rollback, review source/receiver tag and role dispatch, audit external caller use before retiring old wrappers, and run consolidated tests before any controlled apply. **Do not mark Steps 2–4 CLOSED yet.**
