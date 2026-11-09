# 0040-FEAT — Constrained receiver deletion primitive

Status: source implementation/regression only; **not production-enabled**.

This patch adds a `delete-receiver` role to the constrained Btrfs endpoint. It requires a matching pending transaction journal and receipt, a distinct present read-only received parent, Btrfs filesystem UUID, and received UUID. It deletes only the exact timestamped received snapshot; neither journal nor receipt is removed by the privileged endpoint.

The existing production sudoers template is intentionally unchanged and does not authorise `delete-receiver`. The existing receiver CLI has no call to this role, and production pruning remains disabled. No changes to the `--latest` send path, schedules, retention or snapshots.

Local tests: six fixture-based negative/positive tests passed, Python compilation passed. The positive test mocks the Btrfs deletion syscall, so this does **not** prove a real Btrfs deletion or full transaction. It is a prerequisite for the remaining sender-bound coordinator integration, which must add the `protected_parent` to the journal, acquire the writer lock throughout, validate a persistent source pin, and create a tightly scoped sudoers allowance only after review.

Open gates: trusted sender-to-receiver invocation, journal/parent contract, lock lifetime, constrained sudoers, source protection lifecycle, crash recovery, disposable Btrfs full integration, Ansible --check --diff and guarded activation.
