# Step 9 Gates 9A and 9B — verified-state adoption (2026-10-15)

## Gate 9A — PASS (read-only live preflight)

Source: operator `mango` transcript `gate9a-mango-20261015-111615.txt`; run with `ansible-playbook verification/0035-step9/preflight.yaml --ask-vault-pass`. Recap: `mars`, `backup`, `pluto` each ok=2 changed=0 failed=0.

- `mars`: `btrfs-snapshot-create.timer`, `btrfs-snapshot-prune.timer`, `btrfs-native-push.timer` enabled and active; next push scheduled 2026-10-16 03:30 UTC. `snapper-timeline`, `snapper-boot`, `snapper-cleanup` disabled and inactive. Latest push service Result=success, ExecMainStatus=0. No legacy remote rsync phase configured.
- `mars` snapshot status: 52 complete paired sets, zero incomplete. Verified production backup ID `20261015-003023Z`; checkpoint hold `20261013-171228Z`, protected replication parent `20261015-030004Z`. Dry-run retention keeps all 52, proposes 0 deletions **at this moment only**.
- `backup`: create/prune timers disabled/inactive, push timer inactive; legacy `/@data/backup` and native receipts remain present.
- `pluto`: existing `.diaries-backup-generations` schema-2 publication directory present.

## Gate 9B — ACCEPTED (no-change migration)

The observed running scheduler state is the target design. No redundant cutover or timer mutation is required. This is **acceptance of an existing state**, not evidence of a fresh deployment or new pruning test. In particular, the prune timer was already enabled and active before this acceptance; Gate 9B does not authorise any new manual `--apply` operation or deletion of historical Snapper snapshots. Maintain source checkpoint/replication pins and passive off-site receiver policy.

## Gate 9C — PASS; Step 9 CLOSED

Read-only `verification/0035-step9/verify-gate-9c.yaml` passed on `mars`, `backup`, and `pluto`, each `ok=2 changed=0 failed=0`. Source timers, snapshot holds and replication protections, receiver passive status, published schema-2 generations and last successful push were confirmed. See `gate9c-mango-20261015-112318.txt` and `STEP-9-CLOSURE-20261015.md`. Overall 0035 feature closure remains separate.
