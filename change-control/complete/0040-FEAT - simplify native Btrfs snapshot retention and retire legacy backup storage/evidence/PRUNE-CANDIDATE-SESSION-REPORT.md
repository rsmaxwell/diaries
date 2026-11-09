# 0040-FEAT — candidate-scoped session gate

Status: source-level verification PASSED locally; deployment NOT authorised.

Implements `--prune-candidate-check` on mars and the corresponding receiver `--prune-candidate-check --snapshot ... --source-uuid ... --candidate ...`.

Receiver holds its existing writer lock; computes the shared-policy candidate set, challenges mars to reassert the persistent pruning pin, and recalculates the candidate set under the same lock. A changed or ineligible candidate fails closed. Challenge/response is bound to protected parent timestamp, UUID, candidate, and nonce.

No privileged deletion call, deletion CLI, sudoers change, state journal mutation, snapshot deletion, or pin release is introduced. The production pruning capability remains disabled.

Local validation: 9 of 9 focused tests PASS; both Python wrappers compile.

This is a candidate-specific advisory coordination gate, not a continuously enforceable source lease. Do not enable real deletion until cross-host source-lease and transactional interruption/recovery are independently proven in disposable Btrfs tests. Historical checkpoints require explicit protection beyond ordinary retention.
