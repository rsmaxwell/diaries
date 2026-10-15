# 0034-FEAT — Step 11.4 unattended operating arrangements: LIVE ACCEPTANCE CLOSE-OUT

**Status: CLOSED — 2026-10-15 UTC.** The scheduled, source-initiated `pluto → mars → backup` backup chain completed without operator intervention overnight on 2026-10-15. All Gate 6A–6E checks and the final read-only verification playbook passed. Step 11 and overall 0034-FEAT are **not** closed by this document.

## Evidence register — Gate 6A through 6E

| Gate | Host and UTC event | Evidence / result |
|---|---|---|
| 6A | `pluto` publisher scheduled 00:30, completed 00:31:10 | `publish-preflight` and `publish` both `0/SUCCESS`; schema-2 `production` generation `20261015-003023Z`, 89 Files; verified manifest; publisher timer active, next run 2026-10-16 00:30 UTC |
| 6B | `mars` pull scheduled 01:30, completed 01:30:23 | `0/SUCCESS`; `PUBLISHED` and `VERIFIED 20261015-003023Z`; `VERIFIED_RECEIVE`, `snapshotEligible=true`, marker `/media/usb/@data/backup/.diaries-snapshot-verified.json` |
| 6C | `mars` snapshot create 02:00 initially failed on writer lock; recovered at 03:00:35 | `VERIFIED-DIARIES production 20261015-003023Z` manifest `c64f94a5211a16506838e74686ecd95acd56f56f8e98caff6e14c4a4a9ce4b65`; complete root/@data set `20261015-030004Z`; subsequent hourly creates succeeded; pruning kept checkpoint and replication-parent protections |
| 6D | `mars` native push scheduled 03:30, completed 03:31:42; `backup` receipt 03:31:38 | `0/SUCCESS`, `action=incremental`, parent `20261014-100031Z`, accepted child `20261015-030004Z`; receiver receipt `btrfs-incremental`, send/receive exit `0`, `read_only_verified=true`, matching source/received UUID `6f44e0e0-1968-6e4d-a3bd-9f77d71e9a47`; received Btrfs subvolume `readonly`; old source parent released after acceptance |
| 6E | `mango` read-only `verification/0034-step11-4/verify-unattended.yaml` | `pluto ok=3`, `mars ok=6`, `backup ok=3`; all `changed=0`, `failed=0`, `unreachable=0`; fresh publication/pull, service/timer state, receiver immutable receipt, source incremental preflight, disabled legacy rsync and absence of obsolete receiver pull helpers confirmed |

Primary supplied operator transcripts (2026-10-15): `note(20261015-062220).txt`, `note(20261015-062346).txt`, `note(20261015-062530).txt`, `note(20261015-062721).txt`, `note(20261015-062827).txt`, and `note(20261015-064253).txt`. These are conversation-provided runtime evidence, **not embedded copies** in this source patch; retain them with the operator evidence archive if required.

## Protection and lineage

- Independent held recovery checkpoint `20261013-171228Z` remained protected during prune.
- Active replication parent advanced from `20261014-100031Z` to `20261015-030004Z` only after receiver acceptance.
- The receiver receipt records source filesystem UUID `72d1d8ea-900e-4fca-837f-1b1febec036c` and receiver filesystem UUID `b915f967-7cb4-4c14-b11b-f52209637a22`.
- Legacy root rsync off-site phase remained disabled; receiver-side obsolete pull helpers remained absent.
- The independently evidenced Step 11.3 disposable off-site restore Gates A–D remains the recovery proof; this Step 11.4 exercise did not perform a destructive restore.

## 02:00 lock collision — resolved configuration, follow-up still due

At 02:00:01 UTC the Ansible-managed `richard` user cron ran `/home/richard/scripts/backup/backup.sh` simultaneously with the Btrfs snapshot service. The script acquires `/media/usb/@data/backup/.btrfs-snapshot-writer.lock` using `flock -x`; at 02:00:02 the snapshot manager correctly failed closed instead of capturing concurrent writes. The 03:00 snapshot succeeded unattended, enabling the 03:30 replication. This incident did **not** corrupt the accepted dataset or block the overnight end-to-end transfer.

Correction: the **user** backup cron was moved from `0 2 * * *` to `45 1 * * *` (UTC), preserving the home/cron backup and shared lock. The isolated `diaries-user-backup-cron.yaml` change passed Python regression, Ansible syntax, `--check --diff` showing only that cron entry, live deployment (`mars changed=1 failed=0`), repeat deployment (`mars changed=0 failed=0`), and on-host `crontab -l` verification. Root cron, snapshot create/prune and native replication schedules were not changed. Evidence transcripts: `note(20261015-063017).txt`, `note(20261015-063045).txt`, `note(20261015-063145).txt`, `note(20261015-063207).txt`, `note(20261015-063745).txt`, `note(20261015-063836).txt`, `note(20261015-063948).txt`, `note(20261015-064056).txt`, `note(20261015-064119).txt`.

**Residual follow-up (not misrepresented as tested):** inspect the first naturally scheduled 01:45 cron and 02:00 snapshot on 2026-10-16 to demonstrate absence of repeat contention. The cron schedule correction is installed and idempotent, but its next unattended execution had not yet occurred when Step 11.4 was accepted.

## Acceptance boundary and deferrals

Gate 6A–6E operational acceptance **PASSED**; Step 11.4 **CLOSED** on 2026-10-15. Final Step 11 and 0034 feature-wide evidence reconciliation, outstanding acceptance criteria and feature closure remain separate. Do not release checkpoint `20261013-171228Z` during this documentation closure. The `diaries-backup-history` `verification.required=false` configuration limitation is deferred to **0035-FEAT** and is not claimed resolved here. Planned rolling publication / extent-sharing redesign belongs to **0036-FEAT**, not this accepted production contract. No Docker image build, snapshot deletion or production configuration change is performed by this documentation update.
