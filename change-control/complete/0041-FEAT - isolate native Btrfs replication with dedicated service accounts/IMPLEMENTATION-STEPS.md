# 0041-FEAT — Reconciled implementation and acceptance steps

**Status:** Steps 1–12 technically satisfied; operator formal feature closure and Diaries evidence commit pending. The previous ten-step draft was superseded by the actual numbered execution/evidence sequence. Do not confuse reports produced before a gate with evidence that the gate was accepted.

| Step | Recorded technical result | Primary evidence |
| --- | --- | --- |
| 1 — Privilege baseline | PASS: read-only host, privilege, service, lock and state inventory | `evidence/Step 1/privilege-baseline-20261113-101958Z.txt` |
| 2 — Restricted design/source review | PASS: reviewed least-privilege contract, fixed gates, candidate architecture | `reports/STEP2-CANDIDATE-IMPLEMENTATION-20261113.md` |
| 3 — Source implementation | PASS: candidate Playbooks role and runtime prepared; subsequently committed as `0904bc7` | `evidence/Step 2/candidate-verification-20261115-140646Z.txt` |
| 4 — Security and regression suite | PASS: 8 new security tests + 25 existing replication tests | `evidence/Step 2/candidate-verification-20261115-140646Z.txt` |
| 5 — Integration verification | PASS: disposable full/incremental transfer and interrupted-stream recovery; dedicated production transfer separately passed in Step 10 | `evidence/Step 9/disposable-native-transfer-20261115-144655Z.txt`; `evidence/Step 10/step10-execute-20261115-145938Z.txt` |
| 6 — Ansible preview | PASS: syntax and partial first-run `--check --diff`; reviewed actual preview before controlled provisioning | `evidence/Step 2/candidate-verification-20261115-140646Z.txt` |
| 7 — Additive provisioning | PASS: account, key, sudoers, forced-command installation and dedicated status with production timer preserved | `evidence/Step 7/additive-provision-20261115-142639Z.txt` |
| 8 — Live adversarial security / idempotence | PASS: denied sudo/SSH tests and zero-change Ansible rerun both hosts | `evidence/Step 8/security-idempotence-20261115-143643Z.txt` |
| 9 — Disposable Btrfs recovery | PASS: fixtures cleaned and protected parent unaffected (fixture used legacy SSH transport) | `evidence/Step 9/disposable-native-transfer-20261115-144655Z.txt` |
| 10 — Dedicated live incremental transfer | PASS: common parent `20261115-030001Z` → `20261115-140017Z`; receiver UUID and read-only state checked | `evidence/Step 10/step10-execute-20261115-145938Z.txt` |
| 11 — Canonical scheduler cutover | PASS: production sender service now `btrfs-send`, 03:30 timer and state unchanged | `evidence/Step 11/service-execute-20261115-151925Z.txt` |
| 12 — First scheduled-run acceptance | PASS: 16 Nov 03:30 timer, exit status 0, received UUID/state identity, backup health and protected permissions | `evidence/Step 12/scheduled-replication-20261116-092125Z.txt` |

## Preserved failed/partial runs

- Step 7 first interactive heredoc did not finish and printed a misleading PASS: `evidence/Step 7/additive-provision-20261115-141806Z.txt`.
- Step 8 first verification stopped on a working-directory mistake: `evidence/Step 8/security-idempotence-20261115-143318Z.txt`.
- Step 11 first cutover stopped at locale `C` / non-UTF-8 before deployment: `evidence/Step 11/service-execute-20261115-151430Z.txt`.
- Step 12 premature invocation correctly refused before the scheduled date: `evidence/Step 12/scheduled-replication-20261115-152642Z.txt`.
- Step 12 initial post-run script failed solely on unprivileged snapshot-config reading, while the timer run had succeeded: `evidence/Step 12/scheduled-replication-20261116-091456Z.txt`.

These logs must be retained as historical evidence. Corrected attempts above passed, without repeating expensive snapshot restores or retransmissions.

## Git and formal closure

- Playbooks committed: `0904bc7ebe801e391a3aa4dc59bbc9ccc7dfa532` (13 files, 720 insertions); clean working tree in recorded post-commit output.
- Ansible controller committed: `e325227`, updating *only* the Playbooks submodule pointer; inventory remained `ebcce026723db37b9b53b76ba21903a351d48466`.
- Windows Diaries before closure: branch `main`, `ef535341c7726806e3d283d76a9eb13c4427a83a`, original TODO files deleted from working path, in-progress directory currently untracked; evidence entries not ignored.
- Formal final gate: inspect consolidated report and logs, operator accepts disclosed rollback-test limitation, move entire feature into `change-control/complete/`, stage exactly this feature and commit Diaries. No production re-run is necessary for Git-only closure.
