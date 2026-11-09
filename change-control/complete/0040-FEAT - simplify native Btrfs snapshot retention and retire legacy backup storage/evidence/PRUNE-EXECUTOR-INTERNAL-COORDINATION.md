# 0040-FEAT — Internal candidate transaction coordination

Status: source-level implementation and local tests only; production deletion remains disabled.

Adds an internal receiver `execute_candidate_transaction_locked()` function which enforces:

- Protected-parent/candidate identifier and UUID validation.
- Current receiver retention candidate membership and no claimed deletion authority.
- Live source-pin callback before a second full receiver planning check.
- Fail-closed rejection if retention plan changes.
- Injected transaction callback after those gates; source-pin callback passed again to the underlying manager's `receiver_delete_one_locked()`.
- Exception propagation, preserving the manager's existing pending journal recovery procedure.

**Not a trusted production lease.** The callbacks in regression are mocks, and the function is not routed from the CLI. The future execution service must hold manager + receiver writer locks and a sender-bound authenticated session for the entire transaction, invoke the existing manager's journal-based deletion primitive and provide its privileged endpoint under a separately reviewed, restricted permission gate. Historical recovery checkpoint exclusions and disposable real-Btrfs crash recovery need acceptance before any production enablement.

Local evidence: `python3 test-executor.py roles/btrfs-replication/files/btrfs-native-push-receiver.py`: 8 tests OK. No live host contacted, no snapshot modified.
