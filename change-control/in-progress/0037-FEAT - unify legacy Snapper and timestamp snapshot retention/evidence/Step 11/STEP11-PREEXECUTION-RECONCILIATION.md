# 0037-FEAT Step 11 — Fresh pre-execution evidence reconciliation

**Reviewed source bundle:** `diaries-sources-20261020-084807.zip` (capture 2026-10-20, 07:40–07:47 UTC).

**Decision:** **CONDITIONAL GO for candidate identity and retention; EXECUTION NO-GO pending targeted operational inspection.** This report neither authorises another snapshot nor creates an executable approval file. The operator's earlier approval remains limited to one pilot, `mars`/`@data`/`19605`.

## Evidence integrity

- All 19 files listed in `pre-execution/SHA256SUMS.txt` match their captured SHA-256 hashes.
- The manager SHA-256 on `mars` is `3eb8717fdb06410943a2e9513dfc5f3e8b6892021bac0d741b58e2524bdff671`, matching the Step 7/9 tested source.

## Candidate and protection findings

| Criterion | Captured result | Assessment |
|---|---|---|
| Host / UTC | `mars` / `Timezone=Etc/UTC` | PASS |
| Source / Snapper config / ID | `@data` / `@data` / `19605` | PASS |
| Creation | `2026-09-28 00:00:38 +0000` | PASS |
| Btrfs subvolume ID | `20165` | PASS |
| Btrfs UUID | `489332dc-3b48-eb40-b59a-d9bd86cc9915` | PASS |
| Read-only | `ro=true`, `Flags: readonly` | PASS |
| Current legacy-plan | `WOULD-DELETE`; 16 KEEP / 9 WOULD-DELETE | PASS |
| Native sets | 58 complete, 0 incomplete | PASS |
| Native dry-run | Would delete 0 complete sets | PASS |
| Held checkpoints | `20261013-171228Z`; `20261018-165453Z` | PASS |
| Protected replication snapshot | `20261020-030026Z` | PASS |
| Backup receiver | `/@data/mars-received/@data/20261020-030026Z` listed | PASS for presence |
| Backup receipt | Matching `.replication-state/20261020-030026Z.json` listed | PASS for presence |
| Backup concurrent matching jobs | Empty capture | PASS at capture time |

**Recovery limitation:** receiver history and receipt existence do not prove a tested restore, nor did the capture read and compare the receipt body with subvolume UUIDs. This is the same previously accepted evidentiary limitation, not a new restore test.

## Operational issue to resolve before deletion

- `mars/current-jobs.txt` shows `/usr/sbin/snapperd` running. This is a daemon rather than proof of active deletion; check active Snapper operations and any timer-triggered jobs immediately before execution.
- `mars/failures.txt` shows `snapper-timeline.service` as **failed**. This is not an indication the deletion candidate is protected, but the capture alone cannot establish whether legacy scheduling is fully retired or whether a concurrent job could run.
- Native create/prune timers remain enabled and have upcoming schedules. The eventual execution must take place during a quiet interval with the manager's own lock and fresh checks.

**Do not create the root-owned approval file or run `legacy-delete --execute` yet.** First execute the read-only diagnostics below and review the result. If these show no active competing work, the legacy timeline failure is stale/nonoperational and the remaining protections match, a fresh same-session execution GO/NO-GO can be recorded. Any divergence means NO-GO and investigation.

## Read-only next checks on `mars`

```bash
hostname
systemctl status snapper-timeline.service --no-pager
systemctl list-timers --all --no-pager | grep -E 'snapper|btrfs-snapshot|diaries' || true
systemctl is-enabled snapper-timeline.timer snapper-cleanup.timer 2>&1 || true
systemctl is-active snapper-timeline.timer snapper-cleanup.timer 2>&1 || true
ps -eo pid,ppid,stat,etime,args | grep -E '[s]napper|[b]trfs (send|receive)|[b]trfs-snapshot-manager|[d]iaries.*(push|pull)' || true
journalctl -u snapper-timeline.service -n 35 --no-pager
```

These commands are read-only. Preserve their output in `evidence/Step 11/` for audit and later decision. Do not reset failures merely to obtain a clean status.
