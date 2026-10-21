# Step 2 — Design and rollback acceptance

**CLOSED — 20 October 2026.** Operator evidence supplied from `mango` and `backup`.

## Decisions and observations

- `local-backup.yaml` selects only `mars`; `remote-backup.yaml` selects only `backup` via distinct inventory groups, with no duplicate-key warnings.
- The updated playbooks passed Ansible syntax checks; `git diff --check` and `bash -n` for both backup wrapper scripts passed after LF/EOF cleanup.
- Wrapper no-argument mode is check/diff; an explicit `--apply` is required for production updates. Actual no-argument remote wrapper run executed in check mode.
- `backup` is a receive-only target. Native received history remains at `/@data/mars-received/@data`, with receiver metadata under `/@data/mars-received/.replication-state`. The manager's `/@snapshots` repository is separate; it must not be repointed into received history.
- The check-mode plan: `backup: ok=22 changed=5 unreachable=0 failed=0 skipped=13`. Changes correspond to manager, backup-history tool, schema-2 verifier, manager JSON, and two legacy-prune unit files (the last two updated in a single Ansible loop task). No activation of local create/prune/legacy timers was proposed. No receiver subvolume or receipt deletion was proposed.
- The proposed JSON removes the obsolete writer lock and verification dataset paths, with `verification.required=false`. It does not make the manager authoritative for the received history.

## Rollback inventory (root-owned on backup)

Directory: `/root/remote-backup-pre-reconcile/`, mode `0700`, created on `backup` before deployment. Each copy was present and its SHA-256 matched the Step 1 installed baseline:

| File | SHA-256 |
|---|---|
| `btrfs-snapshot-manager` | `b1ff38c4fdfacabc6f394d3f35de95b90c2061bf84b1721a7e0c0da1e88c6a99` |
| `btrfs-snapshot-manager.json` | `eec8a849cacbc9ee5d27334ac8511065fc0cafc31cabb9ba45a184c8e577c7e6` |
| `diaries-backup-history` | `1b40c70be484b0268fb2ba1c9558b98ec150651e37e6535aa030158c437be206` |
| `complete-dataset-manifest.py` | `6878a61aeaf4abfe561d9be2c883bb12fb2d67b72b5b7ec0b9420c018fad6cc3` |

All four `cmp` commands produced no difference output. The final reported exit code `0` directly covers the last comparison; matching hashes independently cover all four. Retain protected copies until post-deployment acceptance and rollback disposition. **Restoring the old JSON recreates the known status failure; rollback is emergency-only, not the intended steady state.** If rolling back installed unit changes, review actual changed files and use `systemctl daemon-reload` as appropriate; do not delete snapshots or receipts.

## Deferred to next gates

Step 3: non-production source regression and negative checks, including receiver-only invariants, default wrapper dry-run and `--apply` argument validation. Step 4: refreshed exact review of Ansible `--check --diff` against then-current source. Step 5: real deploy only after these gates. Step 6: read-only post-deployment host/receipt identity verification.

No production installation was changed at Step 2.
