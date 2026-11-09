# 0040-FEAT — 3H.5r Receiver prepare: read-only approval review

Status: **OPEN — no live prepare authorised**. Prepared 2026-10-30.

## Scope

This stage captures a repeatable **read-only** pre-transaction snapshot. It does not invoke `btrfs-agreed-parent-prepare-endpoint.py --request`, create a pending state, transfer snapshots, promote the parent, release previous, enable pruning, or restart timers. The deployed endpoint is already capable of writing receiver state; installation alone does not authorise invocation.

## Existing accepted evidence

- 3H.5q: 20/20 source and installation regressions; Ansible review and installation of prepare-only endpoint plus import-only dependencies on `backup`.
- Installed files on `backup`: transition.py and prepare-verifier.py `0644 root:root`, prepare-endpoint.py `0755 root:root`; remote compilation passed.
- Receiver read-only observation: established `20261030-030033Z` / `d901ddd2-66c7-0b42-b26c-ab6886273b7a`, pending and previous null, transition/prune authority false.
- Source observer: `comparison: matched` between mars and backup with the same quiescent durable state.
- 3H.5n read-only planner previously produced a hypothetical prepare for B `20261030-170009Z` / `a9b78fb9-4da6-cf4f-b242-13909f574193`; all six mutation-authorisation flags false.

These observations are point-in-time and must be refreshed before a later state-changing authorisation.

## Read-only pre-approval inspection

**Existing SSH terminal on `mango`** (the Ansible controller; do not paste `set -e` into the interactive shell):

```bash
cd /home/richard/playbooks

ansible mars -b -m command \
  -a '/usr/local/libexec/btrfs-agreed-parent-source-observer.py --observe' \
  --vault-password-file ~/.vault_pass.txt

ansible backup -b -m command \
  -a '/usr/local/libexec/btrfs-agreed-parent-endpoint.py --observe-receiver' \
  --vault-password-file ~/.vault_pass.txt

ansible mars -b -m command \
  -a '/usr/local/libexec/btrfs-agreed-parent-locked-prepare-plan.py --target 20261030-170009Z' \
  --vault-password-file ~/.vault_pass.txt

ansible mars -b -m shell \
  -a 'systemctl is-active btrfs-native-push.timer btrfs-snapshot-prune.timer; systemctl is-enabled btrfs-native-push.timer btrfs-snapshot-prune.timer' \
  --vault-password-file ~/.vault_pass.txt
```

The final timer inspection may return a nonzero status when inactive/disabled; that is not a gate failure by itself. Read the output; **both timers must remain non-active**. Never infer disabled from inactive. Review the plan's exact B identity anew; if the proposed candidate is no longer present or valid, **stop** and select a fresh candidate through the existing read-only process rather than substitute one manually.

## Go/no-go review conditions

1. Source observer reports `comparison=matched`, source and receiver established identities A equal, pending=null, previous=null, and both observed transition/prune authorities false.
2. Receiver's independent observation corroborates established A and receipt/snapshot evidence, with no in-progress transition.
3. Locked read-only prepare-plan succeeds, has exact schema-1 operation=`prepare`, `transaction_id` identical to candidate timestamp, `expected_before` identical to observed receiver durable state, `expected_receiver_after` differing **only** by pending=B, and all six `authorizes_*` flags are false.
4. Candidate B is independently verified on `mars`, is newer than A, and is still present. Do not assume its continued existence from an older log.
5. Both timers on `mars` are stopped and remain stopped; no pruning or replication can race the candidate or agreed-parent state. Confirm the receiver's own pruning activity and the relevant locks/journals before authorising mutation.
6. Record raw outputs in this feature's `evidence/` or `reports/` directories in the Diaries parent repository, with timestamp and Git revision, separately from Playbooks.
7. Prepare execution procedure must use the **fresh read-only plan's exact request**, not a hand-edited JSON fragment. Any uncertain outcome requires a fresh authenticated read-only `get-state` and reconciliation; **do not blindly retry** and do not write the state directly.
8. Approve the precise target B, execution transport (root stdin on backup), lock ownership, postcondition and recovery procedure separately. No approval is implied by this document.

## Expected state only if a subsequent prepare is expressly approved

- `backup`: established=A, pending=B, previous=null after persisted read-back.
- `mars`: established=A, pending=null, previous=null until a *separate* source-prepare stage.
- No B receipt is necessary for receiver `prepare` before B transfer. B's eventual promotion requires verified receiver receipt.
- No snapshot replication, promotion, previous-parent acknowledgement, release, or pruning occurs in this stage.

## Ambiguous outcome and rollback limits

A prepare request could have persisted pending=B even if its SSH response was lost. Recover by **read-only observation first**, compare to exact before/expected-after state, and stop on any third state. Do not claim a rollback command exists or delete/edit the durable state; define and test a controlled recovery/abort procedure before permitting the live operation. Existing 3H.5k reconciliation is a contract and does not itself perform a remote operation.

## Gate

**3H.5r review prepared; live mutation remains NOT AUTHORISED.** Attach new read-only outputs and obtain a separate decision before invoking the endpoint.
