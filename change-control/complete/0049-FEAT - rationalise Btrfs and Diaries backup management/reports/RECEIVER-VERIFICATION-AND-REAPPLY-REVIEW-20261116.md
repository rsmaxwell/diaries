# 0049 — Receiver verification and Ansible reapply review (16 November 2026)

Status: **partial acceptance; live replication and strict idempotence outstanding**.

## Receiver verification

- `btrfs-backup-status --local-only`: HEALTHY.
- 40 received snapshot sets, newest `20261116-030016Z`.
- Qgroups: 43 total, 0 stale, 0 under deletion.
- Receiver agreed parent `20261116-030016Z`, prior `20261115-140017Z`; JSON status readback succeeded.
- Receiver retention preview: 0 deletion candidates, 2 independent holds, 27 historical receipts preserved, 0 orphaned.
- `0049 RECEIVER VERIFICATION: PASS`. No live prune ran.

## Ansible reapply

- Play succeeded: `mars: ok=26 changed=0 unreachable=0 failed=0`; `backup: ok=34 changed=1 unreachable=0 failed=0`.
- The single changed task on `backup` was `Btrfs backup | Install host-aware read-only infrastructure report` (`btrfs-backup-status`). This applies the updated report, rather than demonstrating strict idempotence.
- Re-run the two-host Ansible play after this update to demonstrate `changed=0` on both hosts.

## Still required

- First post-0049 sender cycle through `btrfs-push.service`, with `mars` service journal, sender preflight/readback and verified state alignment.
- Receiver readback demonstrating the newly advanced agreed parent and continued hold protection.
- Strict Ansible idempotence (`changed=0` both hosts) after last source correction.
- Retain existing data, holds and accepted 0040/0041 recovery evidence.

## Evidence files

- `BACKUP-POST-CUTOVER-VERIFICATION-20261116.txt` (raw receiver terminal log).
- `MANGO-ANSIBLE-REAPPLY-20261116.txt` (raw controller terminal log).

No 0049 acceptance gate or feature closure is claimed on the basis of these two logs alone.
