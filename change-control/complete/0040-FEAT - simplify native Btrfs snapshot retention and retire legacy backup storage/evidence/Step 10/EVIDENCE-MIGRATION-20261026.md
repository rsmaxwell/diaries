# 0040-FEAT — Step 10 evidence migration acceptance (26 October 2026)

## Decision

**ACCEPTED: temporary evidence transferred into the Windows Diaries change-control workspace.** This is evidence storage reconciliation, not authorisation for further deletion or closure of Step 11.

## Source and destination

- Former temporary collection: `mango:/home/richard/0040-step10-evidence/`.
- Permanent Windows repository location, relative to Diaries root: `change-control/in-progress/0040-FEAT - simplify native Btrfs snapshot retention and retire legacy backup storage/evidence/Step 10/0040-step10-evidence/`.
- WinSCP copied the *source directory itself* into Step 10, so the additional `0040-step10-evidence` directory level is intentional and retained. Original relative names below that level are unchanged per the displayed listings.
- The operator subsequently deleted the old `mango` directory with WinSCP. A WinSCP screenshot showing `/home/richard` without that directory was accepted as visual confirmation; a separate command-line absence test was not recorded.

## Transfer verification

1. Original and destination enumerations each reported **136 files**.
2. The one generated `__pycache__` `.pyc` file was excluded from content validation.
3. SHA-256 checksum lists contained **135 lines each**. Comparing the sorted hash-value multisets produced `PASS: all 135 evidence file-content hashes match` on 26 October 2026.
4. The original direct `diff` failed because WinSCP included the `0040-step10-evidence/` path prefix on Windows and Cygwin formatted binary-mode paths with `*`. The visible hashes themselves were equal. **Qualification:** the sorted-hash comparison proves equality of the content-hash multiset, not an independent one-to-one filename-to-hash mapping; filename correspondence has not been independently machine-verified.

## Evidence retained

Retirement manifests, production execution logs, pilot and batch results, manager and receiver status, Ansible check/deploy/idempotency results, and inventory/configuration backups. These files are historical evidence, not deployed Playbooks source.

Important existing manifest identities:

- `mars-retirement-approved-manifest.json` (17 historical Snapper targets): SHA-256 `643c3dff637be45da4188f9991a2bddb27a8bb894d474aebd2318c5ebfa412b4`.
- `backup-retirement-approved-manifest.json` (113 original batch targets): SHA-256 `1d25d3095b36fec8ce95cbab062ece9e2d5da2c72431c47eef78af0bbdfc1e64`.

The retirement work on `mars` native `root` snapshots on 26 October is **Step 11** evidence, not part of the historical Step 10 transfer. Its on-host durable receipt must be retained separately until captured in the change-control workspace.

## Documentation consistency

Any older 0040-FEAT documentation describing `/home/richard/0040-step10-evidence/` as the *current* raw-evidence location is superseded by this acceptance record. The directory has been removed from `mango` by the operator.

Do not move 0039-DEF to `complete`: the operator reopened it under `change-control/in-progress` for continuing stale/orphaned qgroup work.
