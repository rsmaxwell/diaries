# 0040-FEAT — Receiver protected-parent journal contract

2026-10-23 — source-only integration gate.

## Defect

The internal `receiver_delete_one_locked()` previously wrote a pending journal without `protected_parent`, even though `btrfs-native-endpoint --role delete-receiver` requires that field. The endpoint also only checked whether its parent's Received UUID was populated, rather than binding the parent's identity to the transaction.

## Change

The manager validates the protected parent's receipt and writes `protected_parent` and `protected_parent_uuid` into each pending journal. The privileged endpoint independently validates the parent's current Btrfs Received UUID AND its receiver receipt against that journal UUID. Failures occur before any deletion.

Source and receiver locks, retention, ordinary `--latest` replication, and installed configuration are unchanged. No production delete command or sudoers grant is activated.

## Local evidence

- Compilation of both changed Python files: PASS.
- New protected-parent identity contract: 6 tests PASS.
- Updated historical receiver deletion-endpoint regression: 6 tests PASS.
- Updated historical consolidated transaction regression: PASS.

The historical tests were updated only to supply the previously missing protected-parent receipt and UUID.

## Open gates

- Sender-driven, trusted cross-host deletion authority is not yet implemented.
- No live end-to-end prune rehearsal using this exact executor has passed.
- Privileged `delete-receiver` sudoers permission remains disabled.
- Production receiver pruning remains explicitly blocked.

Step 3 and 0040-FEAT stay OPEN.
