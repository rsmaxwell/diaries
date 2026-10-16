# 0036-FEAT Step 2 — formal design revision and closure

**Date:** 2026-10-15  
**Disposition:** original Step 2 design SUPERSEDED; revised fixed-working-copy Step 2 CLOSED (documentation/design only). Step 3 experimental implementation remains unaccepted; do not enable production flags.

## Reason for change

Owner clarified intended system: `pluto` timer updates a **fixed** schema-2 dataset with incremental rsync, `mars` pulls to its own fixed Btrfs working dataset, 0035 frequently snapshots and progressively prunes, and `mars` pushes snapshots to `backup` by the existing 0034 Btrfs send/receive. Extra publication generations, hard links, reflink candidates, receiver-acknowledgement machinery and 0036 maintenance container do not meet the intended simplicity objective.

## Accepted delta

- **Unchanged:** schema-2 `database/`, `files/`, `verification/`, `dataset-manifest.json`; PostgreSQL logical dump semantics; verification, historical restore, snapshot scheduling, pruning, protected parents, 0034/0035 send/receive/receipts, and mars-initiated connections.
- **Changed:** physical layout and synchronisation: one current working dataset each on `pluto` and `mars`, updated incrementally using scoped `rsync --delete`, with history held primarily in frequent Btrfs snapshots.
- **Minimal interlock retained:** schedule separation is not a correctness guarantee; pre-existing writer locks/verified-marker gates should stop half-synchronised datasets from being snapshotted or replicated.
- **Superseded:** previous Step 2 immutable generation/hard-link/reflink/acknowledgement design; provisional Step 3 increments. No production rollout of that work.

## Evidence basis and implementation caveat

The uploaded Playbooks source bundle dated 2026-10-15 shows the 0034 publisher and `diaries-pull.py` copy amplification, while the existing 0035 snapshot manager and 0034 replication tools cover the required historical/off-site functions. The later 0036 ZIP increments were applied by the operator to a Playbooks working tree; this design change **does not claim those working-tree changes have been reverted**. Step 3 must reconcile them safely and preserve existing 0034/0035 behaviour.

## Closure checklist

- [x] Written architecture and schema-2 contract revised
- [x] Original Step 2 evidence retained and marked superseded
- [x] Eight-step implementation plan replaced, inheriting accepted 0034/0035 evidence
- [x] Explicit interlock, safe rollback and legacy-cleanup boundaries documented
- [x] No production mutation or Docker build as part of design revision

**Next:** Step 3 — reconcile experimental 0036 changes and implement `pluto` fixed working dataset. Do not interpret this design closure as runtime verification or production approval.
