# 0041-FEAT — Final technical acceptance and closure reconciliation

**Prepared:** 16 November 2026.
**Decision recommended:** Accept Steps 1–12 technical evidence; authorise moving feature to `complete` after review and commit.
**Formal closure:** Technical acceptance complete; feature moved to complete; final Diaries Git commit pending.

## Technical decision

**PASS:** dedicated `btrfs-send` → `btrfs-receive` replication is operational through constrained service-specific privileged gates. The scheduled `btrfs-native-push.timer` fired 16 November 2026 at 03:30:05 UTC; service executed as `btrfs-send`, streamed an incremental snapshot through the dedicated key and receiver dispatcher, exited 0 at 03:30:25 UTC, and verified common parent `20261116-030016Z`. Sender/receiver state hashes matched; both agreed-parent files remained root-owned mode 0600. Backup health showed 76 complete snapshot sets, zero incomplete, 22 distinct retained Diaries backups, 2 stale qgroups with status `ok`. Latest verified Diaries pull `20261116-003112Z`. Subsequent 09:00 snapshot was correctly only the **next** incremental candidate, not a failed offsite transfer. Primary raw log: `evidence/Step 12/scheduled-replication-20261116-092125Z.txt`.

Step 8 account and sudo denial checks, restricted SSH dispatcher and idempotence passed; Step 9 disposable native Btrfs binary transfer with interruption/retry passed and fixture subvolumes were removed; Step 10 live dedicated incremental transfer passed; Step 11 service cutover passed. See README and reconciled implementation steps for per-step evidence.

## Git receipts

| Repository | Accepted commit / revision | Recorded state |
| --- | --- | --- |
| `playbooks` | `0904bc7ebe801e391a3aa4dc59bbc9ccc7dfa532` | 13-file implementation commit; working tree clean |
| Private `ansible-controller` | `e325227` | Only `playbooks` gitlink advanced from `c510934` to `0904bc7`; working tree clean |
| Private `inventory` | `ebcce026723db37b9b53b76ba21903a351d48466` | Unchanged |
| Windows Diaries | `ef535341c7726806e3d283d76a9eb13c4427a83a` **before** closure commit | New feature directory untracked and old `todo/0041` tracked files deleted; final commit still required |

## Rollback readiness, caveats and scope discipline

The Step 11 scripts provide `--rollback` via Ansible to the former root-running service, and the original admin access remains available. **The production rollback command was not executed**, so do not record it as a passed live rollback rehearsal. An unattended single scheduled cycle passed; no multi-day observation claim is made. The disposable fixture used `richard` for SSH, while Step 10 and Step 12 independently proved live dedicated-identity transfers. These qualifications are accepted only if the operator explicitly approves the final report.

The Step 7 failed paste, Step 8 working-directory failure, Step 11 locale failure, premature Step 12 run and Step 12 first reporting-permission failure remain preserved in raw logs. None is a current uncorrected replication failure. No need to re-run Btrfs transfers for closure.

**Out of scope after closure:** generic `btrfs-backup-status` naming/redesign, application-specific reporting, and any other management command rationalisation. Record those separately after 0041 closes.

## Formal acceptance record

- [x] Implementation and first scheduled run technically verified.
- [x] Source and controller commits recorded.
- [x] Inventory revision unchanged.
- [x] Raw evidence present and not ignored (14 logs; original failures retained).
- [ ] Operator reviews and accepts technical gates and disclosed rollback-test limitation.
- [ ] Move full feature directory to `change-control/complete/` in authoritative Windows Diaries checkout.
- [ ] Verify staged paths, file modes, whitespace and retained evidence; commit Diaries.
- [ ] Record final Diaries commit ID and confirm feature exists only under `complete/`.

**Closure declaration:** Do not mark formally CLOSED until the outstanding items above are completed.
