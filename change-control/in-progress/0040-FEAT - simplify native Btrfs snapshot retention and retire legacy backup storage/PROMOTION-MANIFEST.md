# 0040-FEAT — Production promotion manifest

**Status: NOT STARTED.** No permanent source changes or deployments delivered in this planning package.

## Approved design extension (no promotion yet)

23 October 2026: include retiring the unnecessary `mars` `/media/usb/@snapshots/root/<timestamp>` history and changing the shared manager to accept `@data`-only timestamp sets. Permanent Playbooks changes are anticipated for snapshot creation configuration, paired-set validation, retention tests and retirement controls. **No source promotion, timer change, deletion or deployment has occurred as a result of this documentation update.** The existing active `mars` legacy prune service requires separate compatibility and migration assessment.

## Track future promotions

| Revision | File path (Playbooks repository relative) | Reason | Target host(s) | Test evidence | Check/diff evidence | Deployment evidence | Rollback |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Pending | Pending | Shared manager/source and receiver config | `mars`, `backup` | Pending | Pending | Pending | Pending |

Record: immutable Git revisions, reviewed diffs, program parity hashes, config differences, timer enablement, native sender/receiver health, positive/negative test results, no changes to unintended hosts, accepted deletions, capacity metrics and full close-out. Nothing under this feature tree is automatically deployed.
