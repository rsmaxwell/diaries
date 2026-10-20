# 0037-FEAT Step 6 — Guarded legacy deletion

**State: SOURCE IMPLEMENTED, OPEN. Date: 2026-10-19.**

## Changes

- Added separate `legacy-delete` command; it is not reachable from `run`, `prune`, or the existing timers.
- Requires `--execute`, root privileges (existing manager entrypoint), the manager lock, a root-owned non-symlink approval policy not writable by group/others, matching local hostname, source, Snapper config and exactly one positive numeric ID.
- Policy additionally requires explicit `enabled: true` and `allow_delete: true`. **No approval policy is created, distributed or activated by this feature package.**
- Verifies source/subvolume identity and read-only Btrfs metadata via the Step 4 inventory; checks complete native snapshot sets, pins and holds, retention and the newest legacy anchor via fresh plans. Target must be `WOULD-DELETE` on both checks with identical metadata.
- Invokes only `snapper -c CONFIG delete ID`, once, and aborts on failure. Never deletes Snapper-managed snapshots using raw `btrfs subvolume delete`.
- Existing native `run`, `prune`, scheduler controls, replication and off-site receiver paths are unchanged.

## Tests

Local source verification: `python -m py_compile` PASS; 20/20 existing Step 5 adversarial tests PASS; 14/14 Step 6 guarded command tests PASS. Test mocks prevent invoking any live Snapper delete. `mango` verification is still required.

## Next gates

1. Copy only the replacement manager into `~/playbooks/roles/snapshots/files/` on `mango` using WinSCP. Do **not** deploy to `mars` yet.
2. Run the feature-local Step 6 tests from Cygwin over SSH to `mango` and capture output in `evidence/Step 06/results.txt`.
3. Review the source and run existing Playbooks regressions on `mango`.
4. Steps 7–10 remain mandatory before first controlled live deletion. Operator-approved IDs must be separately authorised.

## Important limitations

- These are mock-driven source tests, not an acceptance of a destructive production run.
- `legacy-delete` never performs a multi-ID cleanup; no unattended legacy pruning is provided.
- Deletion cannot be rolled back merely by reverting source code.
- A manually created approval policy in combination with `--execute` can cause a real deletion: do not create such a policy until the feature's operator acceptance gate.
