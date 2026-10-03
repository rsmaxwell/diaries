# 0031-FEAT final acceptance matrix

This matrix maps every acceptance criterion from the 0031 feature README to authoritative evidence. Earlier live tests are reused where they already prove the required behaviour; Step 16 adds the exact-candidate final regression and restore rehearsal.

| Acceptance criterion | Evidence | Final disposition |
| --- | --- | --- |
| Production and development no longer use the same physical mutable Files root. | Step 10 seeds `files-development-common`; Step 11 proves all local modes resolve it; Steps 13–14 compare production `files` and non-production roots independently. | **Evidenced** |
| Every independently persisted local database dataset has an explicitly assigned mutable Files root. | Steps 2–3 freeze/implement the per-mode defaults and common pair; Step 6 rejects crossed pairs. | **Evidenced** |
| Modes intentionally sharing one database dataset share exactly the corresponding Files root and this is documented. | Steps 2, 6, 11 and 15; Step 11 runtime summary proves all three normal local modes select `common` + `files-development-common`. | **Evidenced** |
| Original read-only diary scans may still be shared without duplication. | Steps 3, 6, 11, 14 and 15 retain `${DIARIES_NAS_CONTENT_PATH}/diaries` -> `/data/diaries:ro`. | **Evidenced** |
| Docker responders continue to see the stable runtime path `/data/files` regardless of physical NAS location. | Steps 3, 11 and 14 mount selected physical roots at `/data/files`. | **Evidenced** |
| `Image.relativePath` remains environment-neutral and relative to the configured Files root. | Step 4 stable URL/path regression; Step 13 controlled Image 88 lifecycle and Step 15 architecture docs. | **Evidenced** |
| Deleting an Image in development cannot remove or alter the production physical file. | Step 13 local common delete with production BEFORE/AFTER complete Files SHA-256 inventory unchanged. | **Evidenced** |
| Uploading/replacing an Image in development cannot alter production physical files. | Step 13 authenticated local upload/observe/delete with production BEFORE/AFTER inventory unchanged; overwrite rejection also verified. | **Evidenced** |
| Production Image lifecycle operations cannot alter non-production Files roots. | Explicit production selector/mount guards from Steps 5–6; Step 14 pre/post activation inventories prove every `files-development-*` root unchanged by production operation. | **PASS — evidenced structurally and by deployed mount/root controls; Step 16 deliberately introduced no unnecessary production Image mutation.** |
| Image catalogue reconciliation is clean or has explicitly reviewed exceptions for every migrated database/Files pair. | Step 9 pre-split reconciliation/dispositions; Step 12 local common and production post-split reconciliation; Step 14 repeats production Step 12 semantic baseline. | **Evidenced** |
| A missing Files-root configuration fails clearly rather than silently selecting the shared production path. | Step 3 Compose `:?` guard; Step 5 Ansible assert/no role default; Step 6 Windows pair guard; Step 16 exact-candidate source tests. | **PASS — evidenced by the final exact-candidate regression** |
| Production Ansible generates the intended production Files mount from an explicit variable. | Step 5 source verification and Step 14 deployed pre/postflight with `DIARIES_FILES_DIR=files`. | **Evidenced** |
| Local Docker Compose generates the intended non-production Files mount from an explicit variable. | Steps 3 and 6 source checks; Step 11 real rendered/mounted local Docker captures. | **Evidenced** |
| Backup/restore documentation treats the database and Files root as a matched dataset. | Steps 7 and 15; Step 16 `ROLLBACK.md`. | **Evidenced** |
| Existing `/files/...` HTTP URLs and Image `relativePath` values do not change merely because the backing root is isolated. | Step 4 responder unit/runtime regression; Step 11 HTTP 200; Step 13 controlled upload returns/serves stable `/files/...`; Step 14 existing production object served unchanged. | **Evidenced** |
| Existing responder/client/web Image behaviour remains unchanged apart from environment isolation. | Step 13 end-to-end lifecycle and cross-mode proof; Step 14 production health/static-serving proof. Step 16 additionally runs the exact-candidate full Java tests and Angular production build. | **PASS — exact-candidate Java tests and Angular production build passed** |

## Additional Step 16 completion requirements

The implementation plan also requires:

- an exact-candidate final configuration/precedence regression including paired common override, isolated defaults and one-sided mismatch rejection;
- final Diaries + Playbooks source identities;
- one non-production restore/reconciliation rehearsal using the preserved Step 8 backup and intended Files root; and
- a concrete rollback procedure that never merges divergent roots automatically.

All four are satisfied. The authoritative captures are:

```text
runtime/final-regression-20261003-104658
runtime/restore-rehearsal-20261003-104511
```

The final regression passed the complete Java responder/web suite and Angular
production build, as well as the accumulated Diaries/Playbooks 0031 gates. The
restore rehearsal restored the checksum-pinned Step 8 common dump into
disposable PostgreSQL and reconciled it read-only against
`files-development-common`.

**Close-out decision:** **COMPLETE — 2026-10-03.** Every README acceptance
criterion has supporting evidence and there is no unexplained pending row.
0031-FEAT may be moved to `change-control/complete`.