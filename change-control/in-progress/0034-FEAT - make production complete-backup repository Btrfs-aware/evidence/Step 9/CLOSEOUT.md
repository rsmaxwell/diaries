# 0034-FEAT — Step 9 close-out: production migration without backup destruction

**Status: CLOSED**  
**Closed:** 2026-10-09  
**Scope:** Step 9 only; 0034-FEAT remains IN PROGRESS (Steps 10–11 outstanding).  
**Hosts:** `mango` (Ansible/source tests); `pluto` (production).  

## Acceptance results

| Gate | Live evidence | Outcome |
| --- | --- | --- |
| Source regression | Twelve suites and Python `py_compile` on `mango`; subsequent symlink regression also passed | PASS |
| Read-only predeploy inspection | `capture-predeploy.yaml` `ok=9 changed=0 failed=0`; original ID `20261007-145013Z`, preflight pass, ext4/`auto` → `full-copy` | PASS |
| Private safety capture | `ok=15 changed=3 failed=0`; private capture `20261009-152441Z`, saved `.env` checksum and historical inventory | PASS |
| Ordinary Playbooks deployment | `./scripts/diaries.sh` `ok=46 changed=3 failed=0`, new separate `DIARIES_COMPLETE_BACKUP_PUBLISHED_ROOT`; no backup pruning | PASS |
| Before-publication preservation | `verify-postdeploy.yaml` `ok=17 changed=2 failed=0`: exact historical ID set; historical restore preflight; transitional pilot access; saved `.env` checksum and disposable rollback copy | PASS |
| First stable publication | `backup-dataset.sh publish`: schema-2 ID `20261009-153243Z`, 89 durable Files, 100032776 bytes, DB custom+SQL dumps; `PUBLISHED` and `VERIFIED`; responder restarted | PASS |
| Published-symlink bug correction | Existing `diaries-backup` pointer caused `publish-preflight` path dereference / basename rejection; corrected configured path, `mango` regression pass, Playbooks redeploy `ok=46 changed=2 failed=0`, `pluto publish-preflight` pass | PASS |
| Post-publication preservation | `verify-postdeploy.yaml -e '{"step9_allow_new_backups": true}'` `ok=18 changed=2 failed=0`; all predeploy IDs retained, new IDs permitted with explicit opt-in, rollback copy checksum match | PASS |
| Second capture-only candidate | Plain `backup-dataset.sh` produced verified schema-2 ID `20261009-154847Z`, 89 files, 100032776 bytes; pointer still named earlier generation | PASS |
| Real rsync/locking acceptance | Live `verify-pluto-rsync-lock.py` on `pluto`; shared reader lock held publisher blocked; received schema-2 old ID `20261009-153243Z`; pointer advanced only afterward to `20261009-154847Z`; older generation retained and scratch removed | PASS |

## Repository preservation / final state

- **Immutable timestamp-ID backups retained:** `20261007-145013Z`, `20261009-153243Z`, `20261009-154847Z` under `/home/richard/projects/diaries/data/dataset-backups/production/`.
- **Stable path:** `/home/richard/projects/diaries/data/diaries-backup` → `.diaries-backup-generations/20261009-154847Z` after live contention test.
- **Previous stable generation retained:** `20261009-153243Z` under `.diaries-backup-generations/`.
- **Transitional pilot symlink** under the legacy repository preserved; no deletion or repurposing.
- **Predeploy safety evidence:** `/home/richard/projects/diaries/data/0034-step9-safety/20261009-152441Z` (private on `pluto`; do not export the saved `.env` into Git).
- **Pre-existing incomplete partial workspace:** `.20261007-143438Z.partial` observed and deliberately not cleaned.
- **Filesystem:** production repository on ext4; `auto` selected full-copy, not reflink.

## Resolved defect and test adjustment

After the first successful publication, `publish-preflight` failed because a `Path.resolve()` on the configured stable path dereferenced `diaries-backup` to the timestamp generation directory. The publisher contract requires the literal stable basename. Production path handling was corrected to preserve the symlink path, source regression added, redeployed and successfully retested on `pluto`. Separately, the original exact-ID postdeploy inventory assertion was preserved as the default, while post-publication acceptance explicitly opts into subset preservation via a true Boolean `step9_allow_new_backups`.

## Boundaries and deferred work

The evidence establishes successful *non-destructive restore preflight*, not a production restore or full `mars`/`backup` replica-and-snapshot rehearsal. Those follow-on gates remain assigned to Steps 10–11 (including 0035 integration). Step 9 did not rebuild Docker images or change Java/Angular. No destruction of existing backups is authorized by this close-out.

**Decision: Step 9 CLOSED on 2026-10-09. 0034-FEAT remains IN PROGRESS.**
