# Step 5 — Isolated publisher implementation and evidence

Status: **CLOSED 2026-10-09 — isolated publisher and source regression; production integration intentionally deferred.**

## Delivered

- `roles/diaries/files/sync/scripts/complete-dataset-publisher.py` (Playbooks source; not called by the current production backup command)
- `roles/diaries/tests/verify-complete-dataset-publisher.py` (synthetic schema-2 fixture on disposable filesystem)
- `preflight`, `create <completed-directory>`, `verify-current`, `show-current-id`, `pin-run -- <command>`.
- The stable `diaries-backup` symlink points to `.diaries-backup-generations/<backupId>`; private staging uses `.staging-*/<backupId>` with schema-2 verification before promotion. An exclusive `flock` governs publication; a shared lock protects `pin-run` reader execution. Previous generations remain in the store; no automatic garbage collection.

## Isolation and limitations

- `create` is a **publisher of an already verified completed schema-2 directory**, not a production capture command. It does not run PostgreSQL, copy NAS Files, invoke rsync, or change the current 0033 backup engine. 0034 later steps must wire capture into this publication protocol, configure the external path and implement the actual production replication reader.
- Existing production `backup-dataset.sh` still creates legacy timestamped complete backups; the 0033 restore tooling is untouched.
- Test proves corrupted candidate rejection, two IDs, reader blocking handover, previous generation retention and scratch cleanup. It does not prove real `pluto` rsync correctness, power-loss durability under all filesystems, live interrupted database dumps, or 0035 snapshot gating. These belong in Steps 6–9.
- **Do not deploy or enable this isolated tool on `pluto` as a production publisher yet.** It has no role template/configuration integration by design.

## Regression

Run from Playbooks root:

```bash
python3 roles/diaries/tests/verify-complete-dataset-publisher.py
```

All 14 assertions passed in local isolated execution on 2026-10-08. Additional existing suite execution was attempted but the combined run exceeded the execution time limit; do not claim a complete suite pass from this session. Run normal Playbooks regressions after applying overlay.

## Next gate

Step 6: inventory and integrate source rsync with the `pin-run` shared-lock protocol; build receiver staging/verification handoff. Later steps handle production integration, host configuration and deployment.

## Formal closure (2026-10-09)

See [CLOSEOUT.md](CLOSEOUT.md), original `mango` evidence, and the corrected deployment-contract regression. The operator run identified an out-of-date permanent-script allowlist; the source fix and successful rerun are recorded. Production integration remains deferred.
