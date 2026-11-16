# 0049 — First post-cutover Btrfs push acceptance (16 November 2026)

**Stage result: PASS for live replication functional acceptance.** This report records evidence, not formal feature closure.

## Source evidence

- Original `mars` terminal log: `evidence/Step 4/MARS-FIRST-PUSH-ACCEPTANCE-20261116.txt`.
- Command was executed interactively on `mars`: `sudo -n systemctl start btrfs-push.service`; prior and subsequent read-only `btrfs-replication sender status` used `BTRFS_REPLICATION_IDENTITY_MODE=dedicated`.

## Observed results

- Before the run, source and receiver agreed-parent records both identified `20261116-030016Z`, UUID `b3fe0423-b878-da4f-8619-fd31ca950963`.
- Preflight selected incremental target `20261116-150008Z`, UUID `818b8956-76de-564f-8351-37cc89037d14`.
- At 15:56:13 UTC, `btrfs-push.service` started with systemd user `btrfs-send` and elevated only the constrained sender-cycle helper. The transfer used SSH as dedicated remote user `btrfs-receive`, with the pinned host key and restricted identity parameters visible in the systemd journal.
- At 15:56:28 UTC, the journal reported `SUCCESS: common parent advanced to 20261116-150008Z`, and systemd reported successful completion.
- After the run, sender status reported `receiver_parent_verified=true`, `relation=equal`, `preflight.action=up-to-date` and matching source/receiver state: parent `20261116-150008Z` (UUID `818b8956-76de-564f-8351-37cc89037d14`) and prior `20261116-030016Z`.
- `btrfs-backup-status` on mars reported `HEALTHY`; `btrfs-push.service` showed success at 15:56:28 UTC and timer showed next run on 17 November at 03:30 UTC. The report correctly states that an independent transfer receipt is unavailable; this is distinct from successful identity readback.
- Mars qgroup status was `ok` with 2 stale qgroups (95 total, 0 under deletion), already covered by separate defect 0039. No retention prune or restore was run.

## Remaining acceptance requirements

- Obtain independent post-transfer **backup host readback** of current/prior agreed parents, retained snapshot identity and protected receiver retention preview; verify no unexpected deletes.
- Repeat Ansible on `mars` and `backup` to establish strict `changed=0` idempotence. Previous reapply recorded `mars changed=0`, `backup changed=1` due to installation of the updated `btrfs-backup-status` command.
- Complete final source/host revision and rollback manifest, verify no duplicate timers, and record operator acceptance. Do not mark Step 4 CLOSED or move feature to `complete` without accepted evidence.
