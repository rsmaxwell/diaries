# 0040-FEAT — Production promotion manifest

**Status: IN PROGRESS — source cleanup and controlled non-destructive deployment accepted; final promotion revision and Steps 9–14 acceptance pending.** The previous planning statement below is historical, not the current operational state.

## Original design extension (historical planning record)

23 October 2026: include retiring the unnecessary `mars` `/media/usb/@snapshots/root/<timestamp>` history and changing the shared manager to accept `@data`-only timestamp sets. Permanent Playbooks changes are anticipated for snapshot creation configuration, paired-set validation, retention tests and retirement controls. **No source promotion, timer change, deletion or deployment has occurred as a result of this documentation update.** The existing active `mars` legacy prune service requires separate compatibility and migration assessment.

## Track future promotions

| Revision | File path (Playbooks repository relative) | Reason | Target host(s) | Test evidence | Check/diff evidence | Deployment evidence | Rollback |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Pending | Pending | Shared manager/source and receiver config | `mars`, `backup` | Pending | Pending | Pending | Pending |

Record: immutable Git revisions, reviewed diffs, program parity hashes, config differences, timer enablement, native sender/receiver health, positive/negative test results, no changes to unintended hosts, accepted deletions, capacity metrics and full close-out. Nothing under this feature tree is automatically deployed.

## Source/deployment reconciliation — 25 October 2026

The new shared manager implementation has been installed on `mars` and `backup`, and source/install SHA-256 was verified as `cb4785a3880f83201e7718f10fd8a053f4f0cce2b5a9f65f09c0374c5ebd132e`. The renamed entry point is `btrfs-replication.yaml`. Its two-host check-mode idempotency evidence is `mars changed=0 failed=0` and `backup changed=0 failed=0`. The production receiver remains protected; receiver-prune activation is not accepted. The original in-progress source modifications and deletions are in Playbooks working tree based on `a8f857c3b4f2ff57dd83d58bbbe0a99150797625`, **not yet an immutable committed promotion**. Record the final Playbooks Git revision and source diff at commit/release.

| Workstream | Changed files / surface | Accepted evidence | Remaining gate |
| --- | --- | --- | --- |
| Shared manager | `roles/snapshots/files/btrfs-snapshot-manager.py`, tests, native snapshot role | Source/install parity and host inventory verification | Final Git revision and feature completion |
| Snapper retirement | Removed active Snapper helpers, legacy units, retirement role tasks and entry playbook; cleaned relevant inventory | Source regressions, controlled host retirement and active-reference audit | Separate native `mars` root retirement; preserve rollback/evidence |
| Replication playbook rename | `native-btrfs.yaml` → `btrfs-replication.yaml`; role defaults/README/tasks and remote references | Syntax pass; `mars` and `backup` `--check --diff` both `changed=0` | Include in final source commit |
| Protection idempotency | `roles/btrfs-replication/tasks/native.yaml`, `tests/verify-replication-protection-idempotency.py` | Formatting-independent `mars` check; fixture cases missing/disabled/wrong path passed | Preserve regression in commit |
| Operational documentation | `roles/local-backup/README.md` | Removed obsolete legacy-pruning instructions | Final documentation audit |

The backup-only 115 original legacy Snapper snapshots, plus the APT-generated extra snapshot and empty legacy container subvolumes, were retired under their separately documented guarded approvals. This does not close overall Steps 10–11 or authorise deletion of received snapshots. Keep the raw evidence/approved manifest on `mango` until it has been archived as historical evidence; do not move evidence scripts into permanent operational roles.
