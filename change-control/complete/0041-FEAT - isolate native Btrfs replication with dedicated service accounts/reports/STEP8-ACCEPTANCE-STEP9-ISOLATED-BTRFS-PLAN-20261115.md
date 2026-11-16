# 0041-FEAT — Step 8 accepted technical evidence and Step 9 disposable Btrfs test

Date: 2026-11-15. Feature remains IN PROGRESS.

## Step 8 technical verification

Live log: `evidence/Step 8/security-idempotence-20261115-143643Z.txt`.

Passed account isolation, no unrestricted sudo, root-controlled receiver authorized_keys, dedicated read-only status/UUID agreement, five rejected arbitrary SSH commands, and idempotent additive deployment: changed=0 on both mars and backup. The original 03:30 service/timer and inactive candidate remain unchanged. Step 8 technical verification is complete; formal closure requires normal acceptance procedure.

## Step 9: disposable native Btrfs component integration

Use `tools/run-0041-step9-disposable-from-cygwin.sh` from Windows. It executes `tests/verify-0041-step9-disposable-on-mars.sh` via mango, saving one evidence log inside the feature. It creates only uniquely named, unmanaged `.0041-disposable-*` fixtures on the existing Btrfs filesystems, exercises full and incremental kernel Btrfs send/receive, intentionally truncates one stream, retries the fixture, checks received UUID/payload, confirms existing agreed-parent hashes unchanged, then deletes only its own verified fixture subvolumes. It refuses while the source push or receiver prune is active.

**Scope limitation:** The disposable stream test uses the existing privileged `richard` SSH transport, *not* the new receiver forced-command `receive` path. The new root gate is intentionally bound to production Btrfs paths and protected parent state; adding a test-only root-path override would enlarge production privileges. Separate Step 8 tests already verified dedicated status and rejected SSH commands.

## Remaining acceptance

After Step 9, perform one supervised ordinary incremental send through the dedicated `btrfs-send` → `btrfs-receive` path, with read-only preflight, manager-lock contention and before/after parent/UUID receipt checks. Do not turn on candidate scheduler until accepted. Do not blindly roll back agreed-parent records after a successful receive. Retain legacy root service as rollback. Keep personal richard SSH/sudo unchanged.

If fixture cleanup fails, stop and inspect exact named fixture paths; never invoke generic deletion against historical backups.
