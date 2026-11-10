# 0042-FEAT — Execution and acceptance reconciliation (10 November 2026)

**Status:** Steps 1–2 technically verified and Step 3 core host checks passed; final readback and formal feature closure remain outstanding. This report reconciles the user-supplied terminal output; it does not represent commands executed by the assistant.

## Source and test acceptance — Step 1

- Playbooks worktree branch `main`, original HEAD `e0da797310ab452ddc61e7368c50a444fe881e41`.
- Exact-file manifest checked all **215** candidates against Git tracking and SHA-256. One compressed rollback archive was read back and verified before `git rm` staged precisely 215 deletions.
- Archive: `evidence/Step 1/0042-retired-playbooks-20261110-081412Z.tar.gz`. Receipt: `evidence/Step 1/0042-source-retirement-20261110-081412Z.json`. Both were subsequently copied from mango into the authoritative Windows Diaries feature directory.
- Initial regression failed because a synthetic state file was not owned by root. A test-only correction preserved root ownership enforcement and added a negative ownership test. The resumed run passed all eight retained suites (including simplified sender 25 tests, cutover readiness 5, protection 4, receiver retention 17 and 0039 qgroup maintenance 22).
- Git diff and staged diff checks passed. The 215 deletions were still **staged, not committed** at the last observed checkout status. Uncommitted 0039 changes were also present.

## Deployment — Step 2

- `ansible-playbook btrfs-replication.yaml --syntax-check --vault-password-file ~/.vault_pass.txt`: PASS.
- `--check --diff --limit 'mars,backup' --skip-tags qgroup-maintenance`: 0 changes and 0 failures on both hosts.
- Actual deployment used the same `--skip-tags qgroup-maintenance` boundary. Outcome: `mars` 14 OK/0 changed/0 failed; `backup` 25 OK/0 changed/0 failed. No Btrfs transfer or quota cleanup was invoked.

## Host and integration acceptance — Step 3

- Read-only host absence audit: 39 of 39 legacy `mars` paths absent and 35 of 35 `backup` paths absent.
- Active `btrfs-native-push.service` `ExecStart` invokes `/usr/local/bin/btrfs-simplified-replication sender cycle`. Its historic unit name is intentionally retained.
- Sender status: `relation=equal`, `receiver_parent_verified=true`; receiver independently reported the identical agreed parent `20261110-030004Z`.
- `mars` native push and qgroup cleanup timers enabled/active; `backup` simple receiver prune and qgroup cleanup timers enabled/active.
- `mars`: 70 complete snapshot sets, 0 incomplete, verified Diaries production backup `20261110-003113Z`, 3 eligible stale qgroups between daily scheduled cleanup runs, 0 unmarked orphans.
- `backup`: 33 complete snapshot sets, 0 incomplete, 0 stale qgroups; snapshot-manager status OK.
- Windows Cygwin `tar` transfer of the feature evidence from mango finished successfully; all six evidence filenames enumerated in the Windows worktree.

## Outstanding closure requirements

1. Execute and preserve one read-only `/usr/local/sbin/diaries-backup-status --json` readback from `mars`, planned in Step 3 but not shown in the captured deployment/host log.
2. Compare the copied rollback tarball SHA-256 to the `archive_sha256` inside the JSON receipt; do not presume byte-level matching solely from transfer success.
3. Record **separate** Git commit(s) and revisions for 0042 changes in Playbooks and the Diaries change-control tree, without inadvertently sweeping in the independently uncommitted 0039 work. Confirm repository status and planned staging before committing.
4. Obtain the user's formal acceptance, update step status to CLOSED and move `0042-FEAT` from `in-progress` to `complete` only when all close-out evidence is accepted.

Raw evidence: `evidence/Step 1/source-verification-20261110.txt`, `evidence/Step 2/deployment-20261110.txt`, `evidence/Step 3/post-deployment-20261110.txt`, together with the Step 1 archive, receipt and exact-path manifest. Reuse the accepted historical 0040 transfer/restore evidence; no repeat is necessary.
