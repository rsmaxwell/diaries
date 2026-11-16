# 0041-FEAT — Isolate native Btrfs replication with dedicated service accounts

**Type:** Feature
**Status:** TECHNICALLY ACCEPTED — formal closure pending final Diaries Git commit (16 November 2026).
**Implementation:** Playbooks `0904bc7ebe801e391a3aa4dc59bbc9ccc7dfa532`; private Ansible controller `e325227` pins that revision; inventory `ebcce026723db37b9b53b76ba21903a351d48466` unchanged.
**Source of truth:** Reports and raw logs retained in this feature directory. The main scheduled-run acceptance log is `evidence/Step 12/scheduled-replication-20261116-092125Z.txt`.

## Objective and accepted outcome

Replicate native Btrfs snapshots from `mars` to `backup` using dedicated, narrowly privileged service identities instead of `richard` as the transport identity. Preserve `richard`'s personal administrative SSH and sudo access and all existing snapshot-retention, pruning, lock, protected-parent and rollback mechanisms.

**Achieved:** The canonical `btrfs-native-push.service` now runs as `User=btrfs-send` and `Group=btrfs-send`; its fixed no-argument sudo gate invokes the reviewed privileged transaction engine. The engine invokes SSH as `btrfs-send` using a dedicated Ed25519 key to `btrfs-receive` on `backup` via port 39263 and a root-managed pinned host key. The receiver's root-managed forced dispatcher and privileged gate allow validated `status`, `receive`, and `advance` requests only. General sudo, shell requests and tested command injection attempts were rejected. `richard`'s existing administrative access was preserved.

The 03:30 UTC timer remains the sole authoritative scheduled sender. Existing root-managed snapshot creation, sender/receiver retention and qgroup maintenance were not migrated to the service identities. Receiver pruning was **already enabled** before 0041 and remains separate; the original 27 October 0041 baseline statements about disabled pruning and an unfinished 0040 are historical and superseded.

## Acceptance evidence

- **13 November, Step 1:** Read-only privilege, lock, owner, service and replication baseline captured; `evidence/Step 1/privilege-baseline-20261113-101958Z.txt`.
- **15 November, Steps 2–6:** Restricted-identity design and source candidate reviewed; 8 security tests plus 25 existing replication tests passed; Ansible syntax and partial `--check --diff` verified. `evidence/Step 2/candidate-verification-20261115-140646Z.txt`. Live first-install provisioning intentionally followed only after this review.
- **15 November, Step 7:** Additive deployment to `mars`/`backup`, SSH host key matched and dedicated read-only status passed; `evidence/Step 7/additive-provision-20261115-142639Z.txt`.
- **15 November, Step 8:** Negative SSH/sudo tests passed; additive playbook rerun gave `changed=0` on both hosts; `evidence/Step 8/security-idempotence-20261115-143643Z.txt`.
- **15 November, Step 9:** Disposable full/incremental native Btrfs transfer, interrupted-stream refusal, successful retry, checksum/UUID checks and fixture cleanup passed; production agreed-parent state unchanged. This test used the existing `richard` transport, not the dedicated receiver gate. `evidence/Step 9/disposable-native-transfer-20261115-144655Z.txt`.
- **15 November, Step 10:** Supervised **production** incremental cycle through dedicated identities passed, parent advanced `20261115-030001Z` → `20261115-140017Z`, verified at both ends. `evidence/Step 10/step10-execute-20261115-145938Z.txt`.
- **15 November, Step 11:** Canonical sender service changed through Ansible to `btrfs-send`; timer and protected state unchanged. `evidence/Step 11/service-execute-20261115-151925Z.txt`.
- **16 November, Step 12:** First unattended 03:30 UTC replication started 03:30:05 and exited successfully 03:30:25, accepted parent advanced to `20261116-030016Z`; receiver identity, read-only snapshot, state ownership and backup health verified. `evidence/Step 12/scheduled-replication-20261116-092125Z.txt`.

Earlier failed/incomplete attempts remain preserved and **must not** be mistaken for accepted runs. See `IMPLEMENTATION-STEPS.md` and `reports/FINAL-ACCEPTANCE-AND-CLOSURE-20261116.md`.

## Scope, security and rollback

Both service users are non-administrative and receive only specified fixed `sudo` commands; the receiver SSH credential is forced-command restricted. The trusted privileged Btrfs transaction implementation continues to own manager locking, lineage validation, protected state, receive and recovery semantics. The final design is **restricted-entrypoint privilege separation**, not a fully unprivileged Btrfs engine.

The pre-cutover service definition and the `legacy` sender identity mode remain documented as a rollback route. A `--rollback` launcher exists in the Step 11 feature tooling and uses Ansible to restore the former canonical service definition. **Rollback was prepared but was not executed as a live production rollback test**; do not claim otherwise. Any future rollback must first check current agreed-parent state, active jobs and current Ansible source. Do not manually rewrite agreed-parent records or delete snapshots. No private keys are retained in evidence or Git.

No additional live Btrfs transfer or restore test is required solely for this closure. Post-closure renaming or redesign of backup/status management utilities is deliberately deferred to a separate feature.

## Formal closure procedure

1. Inspect this consolidated README, `DESIGN.md`, `IMPLEMENTATION-STEPS.md`, the final acceptance report and retained raw evidence; verify no unrelated local modifications were included.
2. Record the operator's formal approval of the accepted evidence and disclosed rollback-test limitation.
3. Move this entire feature directory from `change-control/in-progress/` to `change-control/complete/` in the authoritative **Windows Diaries** checkout, preserving every report, script and raw log.
4. Stage only the previous `todo/0041-FEAT...` deletion and new `complete/0041-FEAT...` directory, inspect `git diff --cached --check`, then commit. Preserve other changes and Git submodule revisions.

**Formal closure remains pending until the move, operator acceptance and Diaries Git commit are evidenced.**
