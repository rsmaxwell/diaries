# 0040-FEAT — Step 12 simplified replication: formal source and disposable Btrfs acceptance

**Decision date:** 5 November 2026  
**Decision:** **ACCEPTED — development/source tests and disposable real-Btrfs integration only.**  
**Feature/Step status:** **0040-FEAT Step 12 remains OPEN** for operational deployment, acceptance of unattended operation, and separately gated receiver pruning. Steps 13 and 14 remain OPEN.

## Operator decision

The operator explicitly accepted the simplified replication source and disposable real-Btrfs integration tests on 5 November 2026. The acceptance covers the simpler native send/receive approach with a compact common-parent file on each host, non-blocking local locks, next-scheduled-invocation cleanup and retry of an unambiguously incomplete candidate, and lost-acknowledgement reconciliation. Ordinary logs are sufficient; the abandoned transactional journal/staging architecture is not required.

## Accepted primary evidence

| Evidence | Observed result | Acceptance |
|---|---|---|
| `evidence/Step 12/raw-logs/note(20261105-133205).txt` | 17 simplified core, 3 simplified protection, and 11 existing prune-guard Python tests PASS; prune-source selection and shared retention checks PASS | Accepted earlier (superseded core total by the 18-test run below) |
| `evidence/Step 12/raw-logs/note(20261105-175338).txt` | Updated core: **18/18 tests PASS**, including configured-lock back-off, incomplete-candidate cleanup, receiver-ahead reconciliation, and atomic state readback | **ACCEPTED** |
| `evidence/Step 12/raw-logs/note(20261105-180932).txt` | Independent lock-contention diagnostic: subprocess exit **75**, stderr `DEFERRED: local snapshot-manager lock busy` | **ACCEPTED** |
| `evidence/Step 12/raw-logs/note(20261105-175454).txt` | Disposable real-Btrfs interrupted receive left incomplete subvolume; receiver deferred on lock; exact incomplete subvolume cleaned and incremental receive retried; receiver-ahead acknowledgement reconciled without retransmission; parent/prior states agree and remain protected; overall PASS | **ACCEPTED** |

The two earlier failed disposable integration runs (lock-collision harness mismatch) are **historical failed evidence**, not a reason to repeat the now-passing test. The previous lock correction is present and supported by both the dedicated and integrated lock checks.

## Source provenance

- Diaries checkout observed at `e5aea34179f3c4c74649c472e5226ee4b43246c2` in the disposable integration preflight log.
- Playbooks Git HEAD observed at `bdba058b0f3b634f94e7da4b7ab62eeadfa625b6`, with significant **uncommitted/extra files** in the source working tree. This revision alone **does not identify the actual tested simplified runtime**.
- Independent diagnostic SHA-256 of the tested `btrfs-simplified-replication.py` on `mango`: `9be64295a6b6807df0fcd33d924b7a6549959f2a03dcab2953dcf0ac77fa6297`.
- Disposable integration test SHA-256 on `mango`: `b3b86f50733eb18e48622dd4ae80cf37bfa75d2dd4a12d59eff5496c015b9bbf`.
- Both SHA-256 values are observations from the operator's diagnostic, **not** a claimed production install verification.

## Accepted scope and residual work

**Accepted:** core code correctness, regression coverage, actual disposable Btrfs interruption, safe next-run retry, lost-ack recovery, no-overwrite/parent safety in tested cases, and non-blocking collision handling. The accepted correctness tests need not be repeated unchanged.

**Not accepted:** operational SSH/sudo/Ansible integration between `mars` and `backup`, installed-runtime parity, bootstrapping/reconciling production simplified state files, production service cutover, overnight operation, exact receiver-prune protection under the simplified record, or activation of receiver pruning. No full restore or repeat of the previously accepted 1 November A→B manual transfer is required solely by this acceptance.

**No mutation approval:** This decision is not an authorisation to delete existing production snapshots, modify protected recovery points, enable receiver pruning, bootstrap state, or switch the 03:30 timer/service. Do not change the 48/14/12/24/5 retention policy. Keep the older native replication command available for rollback until operational acceptance.

## Outstanding Step 12.4 operations

1. Read-only source/install/timer/lock/state/SSH checks on `mars` and `backup`; collect actual Btrfs parent identities and reconcile local differences against the current Playbooks tree.
2. Review a limited Ansible `--check --diff` for **install-only** simplified command deployment; retain current service ExecStart and 03:30 UTC timer. Treat any unexpected role side effect as a blocker.
3. Under a separate controlled rollout decision, install identical simplified commands on both hosts and verify installed hashes and SSH command privilege path. Establish new parent state only from an agreed matching Btrfs identity.
4. Execute a controlled operational normal sender/receiver cycle (not a full restore). Verify identities, lock back-off, local/remote agreed-parent and prior protection, and log status; then switch systemd ExecStart with rollback evidence, retaining the schedule.
5. Keep receiver pruning **disabled** pending its independent protection and dry-run acceptance gate.
6. Record immutable Git revisions, diffs, receipt/rollback material, health after scheduled invocation, and operator acceptance. Close Step 12 only on that evidence.

**Historical evidence preservation:** previous staged/journal/scope experiments may be archived under this feature; test/runtime cleanup must not remove necessary native/pruning checks, active rollback files, or accepted raw logs.
