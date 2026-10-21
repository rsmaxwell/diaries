# 0037-FEAT — Step 14 formal closure and overall feature acceptance

**Decision: STEP 14 CLOSED — PASS; 0037-FEAT COMPLETE (accepted 20 October 2026).**

Step 13 remains CLOSED, unchanged. This is a change-control acceptance of existing evidence, not an instruction to run a restore, snapshot deletion, replication or backup transfer.

## Final reconciliation

| Criterion | Acceptance |
| --- | --- |
| Steps 1–13 | Previously closed, evidence retained under the feature directory |
| Full Playbooks idempotency after cleanup-task retirement | PASS: `./scripts/local-backup.sh` on `mango`, target `mars`, `ok=64 changed=0 unreachable=0 failed=0 skipped=16` (`note(20261020-174838).txt`) |
| Three old root-owned pilot helpers | PASS: all three **ABSENT** under `/root/scripts/backup/` (`note(20261020-175736).txt`) |
| Btrfs timers | PASS: `btrfs-snapshot-create.timer`, `btrfs-snapshot-prune.timer`, `btrfs-legacy-prune.timer` **enabled** |
| Retired Snapper timers | PASS: `snapper-timeline.timer`, `snapper-boot.timer`, `snapper-cleanup.timer` **disabled** |
| Snapshot manager health | PASS: `filesystem=btrfs`, **59** complete and **0** incomplete timestamp sets, `qgroups_total=155`, `qgroups_stale=10`, `qgroups_under_deletion=0`, `qgroups_status=ok` |
| Diaries verification | PASS: valid `production` dataset; backup ID `20261020-003106Z` |
| Legacy one-time cleanup mechanism | Removed from the latest Playbooks source; current production pull runs as normal user |
| Tagged-run prerequisites | `getent` and `normal_user_home` fact tasks use `tags: always`; previous tagged-run regression addressed |
| Git, Diaries | `19c607e921e6d118d1f4a0fd744deddb82c31d6f`, `main`, clean, synchronized with `origin/main` at captured check (`note(20261020-175644).txt`) |
| Git, Playbooks | `6a80d4f4160574b243a3d1e73e2f8b0fac767846`, `main`, clean, synchronized with `origin/main` at captured check (`note(20261020-175644).txt`) |

The Git identities above are the **pre-closure** source revisions; final closure documentation and the `git mv` relocation will require a subsequent Diaries commit. Do not present those earlier revisions as containing this closure record.

## Scope and explicit non-claims

- No new end-to-end restore, performance benchmark, receiver receipt reconciliation or new off-site replication was performed for Step 14. Previously accepted recovery/replication evidence remains the basis.
- Stale qgroups (`10`) are reported and healthy by the manager; no qgroup deletion is requested.
- Retention holds, existing replication pins and the scheduled daily legacy-prune operation remain under established safety controls; this document does not authorise a manual pruning run.
- The original Step 12 natural daily timer firing was not directly observed during its acceptance; the manual installed oneshot service was exercised and accepted. That limitation remains recorded.
- Historical Step 13 deferred root-helper housekeeping is **resolved** by Step 14 cleanup evidence; retain the old Step 13 record intact as historical evidence.
- Historical optional quantitative transfer / Snapper read-only performance metrics are not an acceptance dependency for Step 14.

## Closure and file promotion

Accepted complete feature directory: `change-control/complete/0037-FEAT - unify legacy Snapper and timestamp snapshot retention/`.

The accompanying package uses **in-progress relative paths** deliberately, so it can be applied to the current repository first. Then move the **entire** directory with `git mv`, preserving all historical evidence, and commit/push. Neither application of this package nor writing this record performs a `git mv` automatically.

```bash
cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries

git mv 'change-control/in-progress/0037-FEAT - unify legacy Snapper and timestamp snapshot retention' \
       'change-control/complete/0037-FEAT - unify legacy Snapper and timestamp snapshot retention'

git status --short
git diff --check
git diff --cached --check
# Review the changed files and links, then commit and push.
```

**Formal feature disposition:** Step 14 **CLOSED / PASS**; 0037-FEAT **COMPLETE**, subject only to committing/pushing the administrative relocation described above. This is not a runtime deployment gate.
