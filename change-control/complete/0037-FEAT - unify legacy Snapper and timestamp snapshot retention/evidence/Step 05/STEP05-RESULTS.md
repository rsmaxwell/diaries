# 0037-FEAT Step 5 — Adversarial regression results

**Status: CLOSED (2026-10-19).**

## Execution

- Initiated in the Windows Diaries checkout using Cygwin and `ssh mango 'python3 - /home/richard/playbooks/roles/snapshots/files/btrfs-snapshot-manager.py'`, with `tests/step05-adversarial.py` supplied over stdin.
- Test target: actual Playbooks source at `/home/richard/playbooks/roles/snapshots/files/btrfs-snapshot-manager.py` on `mango`.
- Results written locally by `tee` to `evidence/Step 05/results.txt` (user's successful command output also supplied in `note(20261019-192135).txt`).
- **Result: 20 tests executed in 0.011 s; all `ok`; final `OK`.**
- No remote test files were installed, and no deployed managers, timers, Snapper configurations or live snapshots were modified by this exercise.

## Verified test cases

| Group | Tests | Result |
|---|---:|---|
| Compatibility | 1 | PASS |
| InventorySafety | 7 | PASS |
| PlanningSafety | 12 | PASS |
| **Total** | **20** | **PASS** |

Specifically covered: native-only retention unchanged, duplicate config mappings, duplicate snapshot numbers, missing `.snapshots` in an empty configuration, Snapper command failure, invalid CSV headers, missing numbered snapshot directory, unknown source, distinct source scopes, duplicate timestamps, incomplete native sets, legacy-only anchor preservation, missing holds/pins, non-timeline exclusions, native keeper precedence, absent legacy inventory, pin/hold keepers, read-only plan without delete invocation, and recent snapshots.

## Findings and deferred checks

- **Non-blocking for read-only planning:** a non-existent configured Snapper source can surface an unwrapped `FileNotFoundError` instead of `SnapshotError`. It prevents planning; improve operator diagnostics before deletion becomes available.
- **Mandatory in Steps 6–7:** deletion-time changes/races, disappearance of a previously planned candidate, per-delete identity/protection revalidation, and failure of the Snapper delete command. These are not claimed as tested in Step 5.
- This successful mocked regression suite does not authorise snapshot deletion or prove deletion safety.

See `STEP05-FORMAL-CLOSURE.md` for the decision.
