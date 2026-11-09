# 0040-FEAT — Step 3F source pin gate

Status: **PARTIAL — Step 3 remains OPEN**. No production deployment or deletion authorised.

## Change

The existing `btrfs-native-push.py` now exposes `--protect-common-parent`. It acquires the existing native push lock, verifies a common accepted parent, calls the existing constrained `protect-source` endpoint to persistently pin that parent under the snapshot-manager lock on mars, then revalidates the common-parent identity. It deliberately never releases that pin automatically and always returns `authorizes_prune: false`.

The command **modifies source-side protection state if explicitly run**; it is NOT a read-only diagnostic. Do not run the new option on production as part of this stage. `--check-common-parent` remains the read-only diagnostic.

## Source-level evidence

- Python compilation: PASS.
- `step03f-source-pin.py`: PASS — successful persistent pin, mismatched pin UUID, changed parent after pin, and missing common parent, using mocked endpoint calls (no live changes).
- Existing Step 3E `step03e-common-parent.py`: PASS.

## Unresolved safety gates

- This is a **durable source pin**, not a distributed lock held across receiver pruning.
- The receiver writer lock is not retained by this command; a receiver prune still requires a lock-held protocol and live receipt/UUID revalidation.
- A persistent source pin is not a receiver-side deletion approval, nor evidence that receiver-side snapshots remain available after command exit.
- Need explicit pin lifecycle/recovery, least-privilege coordination, receiver-side transaction journal recovery, disposable real-Btrfs deletion tests, adversarial concurrency tests, and regression of the normal push flow.
- Receiver deletion must remain disabled; the Step 3E guard has not been removed.

## Review instruction

Review and apply the Playbooks ZIP independently of the feature-local Diaries evidence ZIP. No Ansible apply is part of this gate.
