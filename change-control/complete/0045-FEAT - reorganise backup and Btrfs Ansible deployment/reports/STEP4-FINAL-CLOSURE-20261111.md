# 0045-FEAT — Step 4 final closure reconciliation (11 November 2026)

**Decision: ACCEPTED for formal closure, effective only when the final Diaries move/commit/push and both repository checks succeed.** This report documents the already accepted technical and evidence gates; it is not a claim that an unexecuted Git command succeeded.

## Evidence and publication chain

| Stage | Accepted result and source |
|---|---|
| Dependencies | 0039-DEF and 0043-FEAT closed and published, Diaries `27e6cbd` |
| Step 1 source/baseline | Definitive `evidence/Step 1/baseline-20261111-111819Z/`, schema `0045-static-installed-v2`; source evidence published `bb91e33`; Step 1 acceptance published `731c6a3` |
| Step 2 Playbooks | Source refactor `1939a0984934062d03c01de826ad4a5a87d3338d`, clean/published on `mango`, replacing original layout based on `7dfa93fef6d975aa82f5f4cfdf54497b106e7645` |
| Step 2 verification | 24 snapshot and 36 native replication tasks preserve semantics/order; source entrypoint/role dispatch, Ansible syntax and five permanent regressions passed; four-host caller audit and 27 Jenkins job definitions checked |
| Step 3 first apply | `evidence/Step 3/deployment-20261111-130143Z/`; no changed tasks or host failures; five transient `mars` systemd `ExecStart` history digests identified and reconciled by focused regression tests |
| Step 3 second apply | `evidence/Step 3/deployment-20261111-132219Z/`; `backup-collection.yaml` on `mars` changed=0; `btrfs-replication.yaml` on `mars`/`backup` changed=0; no failed or unreachable targets |
| Step 3 comparison | `mars` and `backup` managed static installed state equal to Step 1 baseline, including files, permissions, relevant package and systemd/security/schedule properties; Docker signing key SHA-256 unchanged |
| Diaries Step 2–3 evidence | Commit `d93779b` pushed to `origin/main` with clean status (`evidence/Step 4/diaries-step23-publication-20261111-140036.txt`) |
| Final feature closure | Apply this package to the Windows Diaries checkout; move entire feature from `in-progress/` to `complete/` and publish its closure commit; command must verify the actual final SHA and both repositories |

## Equivalent installation and health conclusion

No unexpected installed executable, rendered configuration, directory/ACL, cron, service/timer, security guard, retention policy or role/endpoint difference was found on `mars` or `backup` within the accepted managed-assets scope. The five one-shot service differences were *execution-history only*, proven by unchanged installed unit/drop-in bytes and loaded properties. The second apply was idempotent. Live readbacks recorded healthy Btrfs qgroups, zero incomplete timestamp sets and valid Diaries verification on the source. Operational correctness from 0039/0043 is reused; this refactor did not justify a repeat restore or manual replication.

## Operator interface and residual scope

The new `backup-collection.yaml` and `scripts/backup-collection.sh` are available. The original `local-backup.yaml`, `remote-backup.yaml` and companion wrappers are deliberately retained. No legacy caller was found in the audited host files or 27 Jenkins job definitions, but SCM-fetched Jenkinsfiles and unmanaged external schedulers were not exhaustively covered. This is a documented compatibility decision, not an unproved absence claim. The installed `/root/scripts/backup/remote/` on `mars` remains intact. Inventory relocation is reserved for 0046-FEAT; `/etc/ansible` remains the authoritative inventory for 0045.

## Rollback and evidence custody

The accepted pre-refactor Playbooks revision is `7dfa93fef6d975aa82f5f4cfdf54497b106e7645`. If a *new* operational defect is discovered, evaluate rollback to that revision using the same inventory and narrowly scoped normal Ansible operations; do **not** restore, delete or reinitialise snapshot/replication datasets as part of source rollback. No rollback was needed or executed in 0045. Historical failed captures, runtime mismatch, and original Ansible logs remain under this feature's `evidence/` and `reports/` directories and are moved intact. Raw logs with encoded checkpoint receipts are historical operational metadata; no credential disclosure is asserted on the basis of this review.

## Closure execution gate

The authoritative Windows checkout is the Diaries parent (`diaries-application/diaries`), not the separate `mango` Diaries clone. The final closure command must verify: Windows branch `main` at `d93779b` before staging, no unrelated changes, Playbooks `main` at `1939a09` clean/published, required accepted evidence present, only 0045 paths staged, old feature path absent and new complete path present, final Diaries push successful and both worktrees clean/synchronised. **If any check fails, Step 4 / overall feature closure is not yet effective.** The final commit's Git SHA is captured by the command output and the published Git history; it cannot be embedded in its own commit.

**Formal decision:** accept 0045-FEAT as implemented and installation-equivalent, with formal closure upon successful final Git publication. No further host execution or correctness tests are required for this feature.
