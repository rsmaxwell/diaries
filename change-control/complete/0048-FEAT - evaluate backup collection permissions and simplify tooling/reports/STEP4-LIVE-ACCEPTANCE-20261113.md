# 0048-FEAT — Step 4 live deployment and operational acceptance review

**Review date:** 13 November 2026 (UTC)
**Status:** LIVE DEPLOYMENT AND OPERATIONAL VERIFICATION PASS; formal feature closure requires a final Diaries commit and operator acceptance.

## Evidence and provenance

- Pre-change Playbooks: `df68a0e3bc57bae29a76f46a58c30835126d7f20` (retained rollback reference).
- Published Playbooks: `c5109340a2fe13296a2343c682e1079d1a212c8d` (`0048-FEAT: use Git-native backup collection permissions`).
- Published controller: `83cba342d9ffe7da51a97bda9231f32d02beb2e3` (pins updated Playbooks submodule). Inventory pin unchanged.
- Publication log: `evidence/Step 3/publication-*.txt` (operator run 2026-11-13 08:33 UTC).
- Corrected deployment log: `evidence/Step 4/deployment-*.txt` (operator run 2026-11-13 08:53 UTC). The earlier 08:35 attempt exited early because nested SSH consumed streamed Bash input; it stopped before deployment and remains historical failure evidence. The corrected run was complete.
- Operational health log: `evidence/Step 4/final-backup-health-*.txt` (operator run 2026-11-13 09:00 UTC).

## Confirmed results (as recorded by the operator)

1. Published Playbooks uses ordinary Git-checkout metadata: five relevant source directories `0755` and nine filter files `0644`, with no Ansible mode setting for synchronized directories and no rsync `--chmod` override. The old active `source-modes.json` was deleted; completed 0047 reports and restoration tools remain historical.
2. The targeted `mars` check-mode preview reported `ok=14`, `changed=2`, `failed=0`, `unreachable=0`. The two changes were `install_user_scripts | Copy scripts` and `install_machine_scripts | Copy files`. Templated scripts and cron tasks were unchanged.
3. The live first Ansible run reported `ok=14`, `changed=2`, `failed=0`, `unreachable=0`. The second run reported `ok=14`, **`changed=0`**, `failed=0`, `unreachable=0`.
4. SHA-256 readback verified all nine installed include/exclude files against the published Playbooks source. The same verifier asserted five installed synchronized directory modes `0755`, nine filter modes `0644`, ownership `richard:richard`, no named/default ACL on all 14 paths, and all seven separately templated launcher modes `0744`. It also asserted user cron/log `0750`. All checks passed; not every individual assertion printed a separate output line.
5. Parent access boundaries stayed `/home/richard=0750` and `/root=0700`. Root backup cron retained `15 2 * * * /root/scripts/backup/backup.sh ...`. Backup-related systemd timers were listed in read-only inspection. Sudoers and `richard`'s sudo-group membership were not changed.
6. `diaries-backup-status --limit 3` on `mars` reported `diaries_verification=valid`, 73 complete timestamp sets, 0 incomplete sets, 20 retained distinct backups, verified pull `20261113-003059Z` (verified 01:30 UTC), accepted off-site snapshot `20261113-030001Z` with verified receiver identity, and incremental next preflight from `20261113-080013Z` using parent `20261113-030001Z`. This is a readiness check, not a new replication exercise.
7. Btrfs reported `qgroups_total=86`, `qgroups_stale=2`, `qgroups_under_deletion=0`, `qgroups_status=ok`. Stale-qgroup recurrence is separately owned by 0039-DEF. The status tool also names an earlier history-verification configuration limitation tracked by 0035-FEAT. Neither finding is attributed to this permissions change.

## Security decision and rollback

The five installed descendant directories changed from `0750` to `0755`, while `/home/richard` and `/root` still deny unrelated traversal. The nine regular filters changed from `0664` to `0644`, eliminating group-write. Their contents did not change. Actual readers and executor paths were reviewed in Step 1 and tested through Step 3 read-only access and Step 4 deployment checks. No additional privilege grants, credentials or snapshot/backup mutations were authorised.

Rollback is defined, not performed: return the Playbooks submodule to `df68a0e3bc57bae29a76f46a58c30835126d7f20`, reconcile the prior source-mode contract and installed `0750`/`0664` modes using the preserved 0047 procedure, and verify the result before further deployment. No backup dataset rollback or destructive snapshot action is implied.

## Acceptance disposition

**The technical gates P0–D4 and the Playbooks/controller portion of D5 have passed.** The former 0047 permission oscillation is resolved in a clean clone and in a real repeat Ansible run. No further installation, snapshot, backup or replication tests are required specifically for this change.

**Formal 0048 closure accepted by operator.** Review this report, preserve the actual evidence log files under the feature directory, publish the accepted change-control records from the Windows Diaries repository, and move the feature from `in-progress` to `complete` only upon operator acceptance.
