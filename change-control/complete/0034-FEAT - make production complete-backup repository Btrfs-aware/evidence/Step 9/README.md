# 0034-FEAT Step 9 — deploy on `pluto` without destroying existing backups

**Status:** **CLOSED** — source regressions and controlled `pluto` acceptance passed (2026-10-09).  
**Date:** 2026-10-09.

## Implementation decision

Step 9 preserves the frozen 0033 command contract rather than silently changing every complete backup into a publication:

- plain `backup-dataset.sh` remains a timestamp-ID complete capture only;
- `backup-dataset.sh preflight` remains its non-mutating preflight;
- new `backup-dataset.sh publish-preflight` validates the separate publisher layout and then runs the existing capture preflight, without stopping the responder or creating backup/publication media; and
- new `backup-dataset.sh publish` preflights publication, creates and fully verifies the normal legacy timestamp-ID backup, then publishes **that exact completed directory** into the separate immutable generation store and stable `diaries-backup` pointer.

This ordering is important. If publication fails, the timestamp-ID backup has already been completed and remains valid historical recovery media. The publisher's existing atomic/locking contract preserves the previous stable generation until a replacement has copied, validated and acquired the exclusive handover lock.

## Production migration tooling

Playbooks `verification/0034-step9/` now contains:

- `capture-predeploy.yaml` — read-only inventory by default; explicit opt-in writes a private 0700 safety directory on `pluto` containing the predeploy `.env` (0600), checksum, non-secret storage contract, timestamp-ID inventory, publication paths, backup preflight and deployment state. The secret `.env` is intentionally kept on `pluto`, not copied into change-control evidence.
- `verify-postdeploy.yaml` — run immediately after the normal Diaries Ansible deployment and before any new backup. It requires exact equality of pre/post legacy backup IDs, the final separate published-root setting, integrated `publish-preflight`, a historical restore preflight, transitional Step 6 pilot restore preflight when present, and a checksum-valid saved `.env`. It demonstrates rollback material by copying the saved `.env` to a disposable file, comparing the checksum and removing only the disposable copy; it never replaces live configuration.
- `verify-pluto-rsync-lock.py` plus `run-rsync-lock-proof.yaml` — mutating second-generation acceptance. A real `rsync -a --delete` reads the current stable path while holding the same shared `.diaries-backup.lock` contract used by the `mars` pull. Publication of the second already-completed legacy backup must remain blocked while rsync is active. The received scratch tree must verify as the complete first backup ID before publication is allowed to advance to the second. The previous immutable generation must remain retained.

The transitional Step 6 publication below `data/dataset-backups/production/diaries-backup` is not deleted or silently repurposed. The final root is `data/diaries-backup`, outside the legacy timestamp-ID repository and restore-state tree.

## Source regression performed against the supplied 2026-10-09 bundles

The prepared source passed the complete existing Step 8 regression set plus the new Step 9 publication-wiring regression:

1. complete-dataset manifest;
2. isolated publisher/locking;
3. replication staging;
4. production backup/restore semantics;
5. historical Step 3 Btrfs-strategy compatibility;
6. production complete-dataset tooling;
7. stable publication configuration/path isolation;
8. **new Step 9 production publication wiring**;
9. restore-source compatibility;
10. production storage isolation;
11. production deployment contract; and
12. `mars` pull ownership/delete-scope contract.

Python syntax compilation also passed for the changed production engine, new publication-wiring test and new live rsync-lock verifier. A disposable local smoke test of `verify-pluto-rsync-lock.py` passed with two synthetic schema-2 generations and a real throttled rsync: writer blocked under the reader lock, the received tree verified as the first ID, publication advanced afterward to the second ID, and the previous generation remained present.

The prepared-source results were subsequently confirmed by `mango` and controlled live `pluto` tests. See `CLOSEOUT.md` and the supporting `RUNTIME-*.txt` records in this directory.

## Production acceptance and closure (2026-10-09)

**CLOSED.** All Step 9 acceptance gates have production evidence. The read-only predeploy inventory and private safety capture succeeded; ordinary Playbooks deployment preserved the prior backup ID; first `publish` verified and published a new schema-2 backup. A discovered `publish-preflight` symlink dereference defect was corrected in the production engine, regression-tested, redeployed, and successfully retested. Post-publication verification confirmed that the old IDs remain present (the assertion permits new IDs only with the explicit boolean option). A second capture-only backup produced an unpublished candidate; the live throttled `rsync`/`flock` verifier proved that the publisher waits for the reader, the receiver gets precisely the old generation, the publication then advances, and the prior generation is retained.

Backup IDs: historical `20261007-145013Z`; first new/published `20261009-153243Z`; second new/candidate/final published `20261009-154847Z`. The stable pointer after locking acceptance names `20261009-154847Z`; the legacy transitional symlink was left untouched. Both new captures verified schema-2 manifests, each with 89 durable files / 100,032,776 bytes, plus custom and SQL PostgreSQL dumps. Runtime post-publication Ansible verification completed `ok=18 changed=2 failed=0` (the changes were disposable rollback-copy creation/removal). Live rsync-lock verification ended `PASS: 0034 Step 9 live rsync/publication contention proof` and removed its scratch workspace.

**Evidence limits:** source/log evidence proves successful historical restore **preflight**, not an actual destructive restore; production replication to `mars`/`backup` and 0035 snapshot integration belong to Steps 10–11. No Docker image build was required. The older `.20261007-143438Z.partial` workspace was not modified or cleaned. See `CLOSEOUT.md` and `RUNTIME-*.txt`.
