> **SUPERSEDED on 2026-10-15 by `STEP-2-REVISION-20261015.md` and the revised `DESIGN-DECISIONS.md`. Historical design/evidence only; do not implement this rolling-generation architecture.**

# 0036-FEAT Step 2 — design freeze and closure

**Date:** 2026-10-15  
**Result:** CLOSED — design frozen, not deployed.

## Source inspected

- Uploaded `playbook-sources-20261015-123943.zip`: `roles/diaries/files/sync/scripts/complete-dataset-publisher.py` verifies and `shutil.copytree`s the candidate, renames into `.diaries-backup-generations`, atomically updates the symlink and fsyncs parent directories; its publisher lock uses shared for readers/exclusive for create.
- Same bundle: `roles/local-backup/files/backup-machine/diaries-pull.py` holds the whole-backup exclusive lock, pulls via rsync to an empty temporary `incoming/`, verifies it, then invokes the publisher for another full copy, verifies current and writes the verified marker atomically.
- Prior 0036 Step 1 closure, plus 0034/0035 formally accepted operational contracts, are inherited. No repeat Git hashes, timer inventory, snapshot inventory or off-site receipt capture.

## Decisions frozen

See `DESIGN-DECISIONS.md` for full normative contract. Ext4: guarded immutable hard-link reuse only for unchanged regular Files; new independent metadata, changed-file inode replacement; direct atomic adoption of a fully verified staged generation. Btrfs: reflink/COW fresh candidate, changed-only rsync with no in-place writes, direct verified promotion; marker comes last. Maintain `pluto` previous/current plus unacknowledged holds; receiver acknowledges exact ID and manifest digest; backpressure on outage; conservative crash recovery and separate legacy cleanup approval. Preserve every 0034/0035 external contract.

## Closure criteria

- [x] Reviewed actual publisher and pull paths, not only intended architecture.
- [x] Chosen ext4 and Btrfs reuse mechanisms and old-generation immutability rules.
- [x] Frozen ordered publication, marker and receiver-acknowledgement transactions.
- [x] Defined rollback, generation pressure, crash recovery and no-auto-prune boundaries.
- [x] No production modification, no re-run of accepted 0035 evidence.

**Next:** Step 3 — implement on `pluto` with source-level and disposable regressions; Step 4 implements matching `mars` receive/acknowledgement. The exact durable acknowledgement wire/storage layout remains an implementation detail to resolve consistently in Steps 3–4, not a reopened architecture decision.

**Build:** No Diaries Docker image build; only documentation changed here.
