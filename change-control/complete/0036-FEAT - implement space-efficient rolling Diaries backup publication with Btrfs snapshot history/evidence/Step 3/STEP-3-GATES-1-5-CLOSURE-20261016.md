# 0036-FEAT — Step 3 Gate 1–5 evidence reconciliation and formal closure

**Recorded:** 2026-10-16  
**Decision:** **Step 3 CLOSED — implementation and pre-cutover verification complete.**  
**Not authorised:** production fixed-capture enablement, replacement of `diaries-backup` symlink, migration of `mars` working dataset, timer changes, cleanup of 0034 publications, or pruning any historical snapshot.

## Basis and acceptance

### Gate 1 — Real PostgreSQL dump and restore: PASS / CLOSED

**Evidence:** Operator's `pluto` command output dated 2026-10-15, `verify-0036-disposable-pg-dump.sh postgres:18-alpine`, **exit 0**. Disposable PostgreSQL 18 became healthy; table `diary_probe` created with two rows; `docker compose exec -T pg_dump` generated custom and SQL dumps; `pg_restore --list` checked; custom dump restored into a second database and both rows read. The initial PGDATA/tmpfs Compose startup failure was corrected by using the image's default storage arrangement. This is isolated database evidence, not a live production dump.

### Gate 2 — Real fixed-root schema-2 writer/validator: PASS / CLOSED

**Evidence:** Operator's `mango` result dated 2026-10-15, `python3 roles/diaries/tests/verify-0036-real-schema2-fixed-manifest.py`. Real writer created schema-2 manifest and explicit backup ID under `diaries-backup`; real validator checked all dataset components; fixed-root verification required explicit opt-in; Files and database corruption invalidated the marker; restoration allowed re-verification; invalid fixed-root name refused. Synthetic dump bytes in this test; real dump covered by Gate 1.

### Gate 3 — Read-only host NAS mount: PASS / CLOSED

**Evidence:** Operator's targeted Ansible run `ansible-playbook diaries.yaml --limit pluto --ask-vault-pass --tags 0036-host-nas` plus `pluto` `findmnt`, `ls` and `find` outputs dated 2026-10-16.

- Source: `//nas.tail636235.ts.net/photo`; mount: `/mnt/nas-diaries`; filesystem CIFS.
- Effective options include `ro,nosuid,nodev,noexec`; user mapping shows `uid=1000,gid=1000`.
- As `richard`, directory traversal/enumeration succeeded under `nancy-and-ronald-maxwell/documents/sea-captains-chest/diaries-content/files/`, returning `diary-1828-and-1829-and-jan-1830`.
- Scope limited to new read-only host mount; Docker-managed `diaries_nas-photo` was not reconfigured.
- Intermediate permission errors and an Ansible attempt to chmod a read-only mounted root were corrected by only creating mountpoint when absent and adjusting mount user mapping.

### Gate 4 — Safe source coordination with `mars`: PASS / CLOSED

**Source evidence:** `mango` output `verify-0036-fixed-source-coordination.py` and `verify-diaries-pull.py` on 2026-10-16: marker/digest fail closed; writer/reader exclusion; inherited 0034 receiving publication, 0035 writer-lock and snapshot eligibility contracts still pass regression.

**Cross-host evidence:** Operator's real `mars` invocation of `verify-0036-cross-host-coordination.py --pluto pluto ...` on 2026-10-16: guarded SSH/rsync copied and independently verified disposable schema-2 dataset; missing marker refused; held source exclusive lock refused concurrent reader; previously received verified copy survived rejected transfers; test reported cleanup of temporary paths. This did **not** switch live scheduled `mars` pull.

### Gate 5 — Evidence reconciliation: CLOSED

The four gates above support Step 3 pre-cutover closure. No repeat of the accepted 0034/0035 full acceptance matrices or 0035 quantitative measurements is required. Any gap concerning actual unattended production cycles and off-site receipts is explicitly deferred to Step 8, not implied as passed here.

## Architecture / state preserved

- Fixed working schema-2 structure `database/`, `files/`, `verification/`, `dataset-manifest.json`; no schema change.
- New host NAS path is read-only, `/mnt/nas-diaries`, with existing Docker CIFS arrangement maintained.
- Fixed capture is opt-in / disabled; source guard is pre-cutover tested; existing `pluto` scheduled legacy publisher, published symlink and restore assets remain authoritative.
- `mars` still uses legacy 0034 receiving publication; Step 4 will implement and verify the incremental Btrfs working-copy pull.
- 0035 timestamp Btrfs snapshots and pruning, plus `mars`-initiated Btrfs send/receive off-site replication to `backup`, retain their existing contracts.
- Superseded 0036 hard-link generation / maintenance-image experiments are not approved as the final design; remove them only through controlled reconciliation, not by deleting 0034/0035 historical functionality.

## Next step and constraints

**Proceed to Step 4:** adapt `mars` pull to reusable Btrfs working dataset, with scoped `rsync --delete`, verification marker lifecycle, existing locks and snapshot eligibility. Keep cutover disabled and preserve rollback.

**Step 8 acceptance:** remove `0036` from permanent operational variable names, mount paths, service/unit identifiers, Docker image names and deployed scripts; `0036` remains acceptable in change-control records and tests. Do not discard legacy recovery data without explicit approval.

## Evidence provenance

This record reconciles operator-provided command transcripts from 2026-10-15 and 2026-10-16 and the previously accepted source regression reports. It does not assert a new production deployment, current remote commit hash or unperformed end-to-end restore.
