# 0040-FEAT Step 3E — Common-parent contract (first gate)

Status: IN PROGRESS. Do not deploy or enable receiver pruning.

## Changes

- `btrfs-native-push --check-common-parent` obtains the current accepted receiver listing and checks that the newest matching snapshot remains a read-only source of the expected lineage and UUID. Existing native-push lock is held by main during this read-only diagnostic. It emits `authorizes_prune: false`.
- Snapshot manager **unconditionally rejects `receiver-prune`**, including with `receiver_prune_enabled: true`. The earlier Step 3D prototype's approval file was not sufficient to show that the parent still exists on mars at deletion time. This gate prevents accidental execution while the coordination protocol is incomplete.
- No timers, defaults, installed configurations, endpoint permissions, or production snapshots changed.

## Local evidence

- Python compilation: passed.
- Step 3E offline common-parent scenarios: passed (valid pair, wrong UUID, missing source, duplicate and malformed receiver entries, deletion hard-blocked).
- Existing remote-backup `verify-native-btrfs-push.py`: passed.

## Remaining acceptance gates

- Protect the verified common parent continuously across source and receiver pruning (cross-host lock/lease protocol, lock ordering, failure handling); a point-in-time read-only observation is **not** sufficient.
- Enforce receiver receipt and source snapshot identity under the final coordinated protocol.
- Prove common parent remains present following successful prune and across concurrent push attempts.
- Test successful deletion in disposable Btrfs, interrupted transaction recovery, missing parent, partial receive, lock contention, wrong UUID, and orphan receipts.
- Keep `receiver_prune_enabled` false until the above tests and controlled deployment gates pass.

## Follow-up commands (Cygwin terminal)

Run the test on mango from the feature's tests directory, passing the two Playbooks paths in the shown order. See the accompanying response for an exact command.
