# 0040-FEAT — Step 13: bounded source-pruning catch-up

**Prepared:** 8 November 2026
**Status:** SOURCE CHANGE PREPARED AND OFFLINE TESTED; NOT DEPLOYED; PRUNING NOT REACTIVATED; STEP 13 OPEN.

## Why this is needed

On 30 October, `mars` source pruning was deliberately left stopped while hourly snapshot creation resumed for the simplified replication rehearsal. This was not a failed pruning service. The service's last recorded result was successful (`ExecMainStatus=0`), the `btrfs-snapshot-prune.timer` is enabled but inactive, and `btrfs-snapshot-create.timer` runs hourly.

On 8 November, the read-only source retention plan returned `RETENTION sets: total=273 keep=69 sources=1` and `Would delete 204 complete timestamp sets`. The 204 `WOULD-DELETE` records were counted by the prior verification and neither `20261108-030011Z` (current agreed parent) nor `20261107-030031Z` (prior) was proposed for removal. Both checkpoint holds were listed. Thus the prior check of those 204 rows was valid; an earlier interpretation questioning the parser was incorrect.

The operational issue is that the existing source `prune` command has no per-execution limit, so starting a `Persistent=true` timer could immediately issue all 204 deletions. Btrfs qgroups status reported 456 stale groups, separately tracked in 0039-DEF; do not infer that it makes every deletion unsafe, but monitor it during resumed retention.

## Permanent Playbooks change (separate ZIP)

- Add optional source `prune --max-delete N`, where N must be 1..10. Continue validating the *full* eligible deletion set before selecting up to N complete timestamp sets, retaining the existing newest-first ordering and protection of replication/agreed parents and held checkpoints. Preserve legacy uncapped manual calls and the independent receiver protocol unchanged.
- Install source prune service with `--max-delete {{ btrfs_snapshot_prune_max_delete }}`; default cap 10 sets per scheduled operation.
- Add `btrfs_snapshot_prune_activation_enabled` default `false`, independent of hourly snapshot creation, so deploying these protections does **not** start the paused pruning timer. The setting does not stop an already-active timer.
- Validate the new options' types and limit in Ansible. Maintain 15-minutes-past-the-hour cadence if/when approved.

**Source-bundle basis:** `playbook-sources-20261108-080057.zip`. Compare each modified path against the current `/home/richard/playbooks` version and do not overwrite unrelated changes. The actual Playbooks commit reported by the last live review was `e5ae755`.

## Review and acceptance sequence

1. Preserve verbatim logs `evidence/Step 13-14-final-review-20261108.txt`, `evidence/Step 13-14-snapshot-timer-diagnostic-20261108.txt`, and `evidence/Step 13/step13-source-pruning-{readiness,dry-run}-20261108.txt` in authoritative Windows Diaries, with verified hashes. These source files are currently on `mango`.
2. Use Beyond Compare 4 to inspect/apply only the separate Playbooks ZIP to `/home/richard/playbooks` on `mango`. Verify Git branch, commit and working tree first. Run snapshot-manager existing and new offline regressions; run Playbooks syntax and `--check --diff` for `mars`; confirm `--check` does not start pruning or remove snapshots. Inspect changed service command and the independent activation gate.
3. Deploy the updated manager/service with `btrfs_snapshot_prune_activation_enabled=false` and verify timer remains inactive. Capture exact Playbooks commit, installed binary hash, service ExecStart and live parent/holds statuses. Do not use `--tags activation` to start the timer during this deployment.
4. Fresh read-only dry-run: verify every `WOULD-DELETE` timestamp against current/prior parent and both holds, and compare candidate count with complete-set inventory. Existing validation checks for incomplete sets and unsafe writable/symlink paths must pass. Review the plan and explicitly accept the limited catch-up before resuming. No automatic approval is implied by this report.
5. After approval, set `btrfs_snapshot_prune_activation_enabled=true` in the effective permanent Ansible configuration, run the Playbooks activation task, and verify at most 10 sets deleted per service run, the next timer activation, active `btrfs-native-push.timer`, unchanged agreed parent, checkpoint holds, updated status, and qgroups trends. Do not force a full catch-up, use the uncapped `prune` command or run a complete restore test.
6. Reconcile temporary evidence and final operational Playbooks source into feature Step 13 reports, then assess Step 13 and Step 14 closure; 0041-FEAT dedicated privilege hardening remains excluded.

## Preparation verification

The new synthetic source-prune tests passed in a local copy of the supplied Playbooks sources, including 1/2/10 set limits, dry-run, unchanged uncapped CLI semantics, invalid-cap rejection, full-plan prevalidation and both parent pins. Existing `verify-btrfs-snapshot-manager.py` passed. The Python manager compiled. Ansible syntax, live check mode, installed hashes and deployment have **not** been run for this proposed change.
