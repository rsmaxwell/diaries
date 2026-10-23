# 0040-FEAT — protected-parent UUID transaction binding

Source baseline: uploaded `playbook-sources-20261023-171046.zip`. Previous candidate coordinator and checkpoint-hold gates are accepted.

The internal receiver coordinator now forwards the session's expected protected-parent UUID to its injected transaction callback. The manager's internal `receiver_delete_one_locked()` requires this UUID and rejects a missing, malformed, or mismatched UUID against the verified protected-parent receipt before the pending journal is created. No CLI, permission, schedule, retention setting, or deletion capability is enabled by this change.

Local source regression: `receiver-parent-uuid-binding.py`: 5/5 passed, using simulated callback and static contract checks. This is **not** a live source-held lease or destructive Btrfs rehearsal.

The trusted live lease, both receiver locks, privileged endpoint integration, interrupted transaction recovery rehearsal, and production enablement remain outstanding. Production receiver pruning must remain disabled.
