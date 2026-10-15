# Step 3 — Repository capability detection and storage strategy selection

**Status:** Implemented and local regressions passed; production runtime evidence pending.

The production engine resolves its explicitly configured repository root and reports mount point, filesystem type, free/total bytes, configured storage mode, reflink-probe result, and effective strategy. `auto` selects reflink **only** for Btrfs with a successful real `cp --reflink=always` probe within the repository; otherwise it selects full-copy. `required-btrfs` fails closed without a proven clone; `full-copy` deliberately skips capability probing. Unique temporary probe directories are removed automatically. No completed media are changed by the probe.

Step 3 implements **selection**, not reflink Files capture, which is scheduled for Step 4. Until Step 4 is implemented, a real backup with selected `reflink` strategy deliberately refuses to run *before writer quiescence*. Existing full-copy backups remain executable with explicit `full-copy` mode (including on Btrfs). Do not change a deployed production repository to `required-btrfs` until Step 4 is ready.

Run on `mango`:

```bash
python3 roles/diaries/tests/verify-production-btrfs-strategy.py
python3 roles/diaries/tests/verify-complete-dataset-manifest.py
python3 roles/diaries/tests/verify-production-backup-restore-semantics.py
python3 roles/diaries/tests/verify-production-complete-dataset-tooling.py
python3 roles/diaries/tests/verify-production-deployment-contract.py
python3 roles/diaries/tests/verify-production-storage-isolation.py
```

For `pluto`, deploy only the updated production script (normal managed-scripts Playbooks sync), then run `./backup-dataset.sh preflight`. Preserve the printed mount/filesystem/capability/output plus a before/after inventory of completed backups and responder status. To test each configured mode, change the generated `.env` through Playbooks and redeploy configuration, not by editing `.env` in place. On a non-Btrfs repository `auto` and `full-copy` should select `full-copy`; `required-btrfs` should fail before quiescence. On proven Btrfs, `auto` and `required-btrfs` should select `reflink`.

No Docker build is required. No schema-2 changes and no production restore are required. Do not formally close Step 3 until runtime evidence is supplied.
