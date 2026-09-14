# 0024 Phase 10 - local full-stack smoke test

**Passed on 2026-09-14**, 19:02:42 to 19:04:53 UTC. The complete runner is
`scripts/windows/validation/smoke-image-catalogue.cjs`; prerequisites and rerun
commands are in `scripts/windows/validation/README.md`.

The run exercised the freshly packaged responder and web JARs, production Angular
bundle in headless Chrome, Mosquitto with the application ACL, and PostgreSQL
restored from `diaries-development-20260912-203528.dump`. It used newly created
containers and a separate local Files-tree copy. Development services, production,
NAS content and the original Files copy were not modified. Cleanup completed
without failures. No application runtime code was changed in this phase.

## Results

| Measurement | Before uploads | After uploads/guards | After reconciliation and each restart |
| --- | ---: | ---: | ---: |
| Image rows | 0 | 3 | 76 |
| Canonical retained Image topics | 0 | 3 | 76 |
| All retained topic keys | 10,572 | 10,575 | 10,648 |
| Business files, excluding private staging | 91 | 95 | 95 |
| Diaries | 10 | 10 | 10 |
| Pages | 683 | 683 | 683 |
| Fragments | 2,329 | 2,329 | 2,329 |
| Marquees | 2,269 | 2,269 | 2,269 |

Before reconciliation, the runner deliberately inserted one Image row whose
file was absent. The 76 final rows therefore comprise three uploaded Images,
72 reconciled Images and that one missing-file fixture. There are 75 matching
files and one explicitly reported missing file. A retained topic is still
published for the missing-file row because PostgreSQL remains authoritative.

Snapshots `01-before.json` through `05-second-restart.json` record every file's
SHA-256, every retained topic payload's SHA-256, all Image rows, and complete-row
aggregate hashes for Diary, Page, Fragment and Marquee. The aggregate hashes
include count, content, sequence, type, ownership and lock fields. The before/after
guard snapshots match in files and Images; chronology hashes match throughout.
The two final snapshots are equal in full.

## Dataset and checks

| Case | Observed outcome |
| --- | --- |
| `smoke-ui.jpg`, uploaded through the actual Angular file chooser | Successful JPEG upload, one canonical Image publication, file listing and decoded thumbnail |
| `smoke-twin.jpg`, identical JPEG bytes at another path | Successful separate Image ID with the same checksum; metadata included in the MQTT RPC response |
| `smoke-octet.png`, uploaded with `application/octet-stream` | Detected as `image/png`, catalogued, published and previewed in the client after restart |
| `smoke-generic.bin` | Successful generic upload with no Image ID or catalogue row |
| `smoke-pre-existing.png` | Reported `CREATE_MISSING`, inserted by the reviewed plan, then `CATALOGUED_MATCH` |
| Existing upload, with and without overwrite; uppercase path alias | 409 conflict; no file, Image or chronology mutation |
| Generic deletion of `smoke-ui.jpg` and missing `smoke-absent.png` | 409 conflict, preserving catalogue ownership even when bytes are absent |
| Corrupt PNG uploaded through RPC | 400 rejection; no file or catalogue mutation |
| Existing `smoke-corrupt.png` | `UNREADABLE`; retained for explicit review, never silently repaired |
| Native Linux `smoke-case/Photo.png` and `smoke-case/photo.png` | Two `CASE_COLLISION` records; neither silently chosen or catalogued |
| Image row for `smoke-absent.png` | `DATABASE_ROW_MISSING_FILE`; row and topic preserved |

The original copy contained 87 business files, plus a private staging lock.
Four pre-existing smoke files bring the initial business-file count to 91;
four successful uploads bring it to 95. The private staging area is excluded
from business-file totals and reconciliation, as in the application contract.
File hashing runs in Linux to preserve the deliberately case-colliding names.

The dry run reported 72 `CREATE_MISSING`, three `CATALOGUED_MATCH`, one
`DATABASE_ROW_MISSING_FILE`, two `CASE_COLLISION`, thirteen `UNREADABLE`, five
`UNSUPPORTED` and eleven directories. The approved synthetic plan inserted all
72 safe rows. Reapplying that exact plan inserted zero rows; a subsequent dry
run reported no `CREATE_MISSING` and 75 `CATALOGUED_MATCH`. The excluded findings
remain visible. The twelve original rejected images, original extension
mismatches and frozen 0022/Phase 1 evidence were not repaired or rewritten.

## Browser and restart evidence

The current client signed in through the real responder, opened Fragment 4 on
Page 685, selected its existing MARQUEE, used Fit selection and Zoom in, uploaded
a JPEG and decoded its thumbnail. It listed and decoded the PNG after the
responder restarts. The web reader exercised the same selected MARQUEE and zoom
controls; its month-reader HTML was identical before and after reconciliation
and restarts. Screenshots are included in `run/`.

The selected source-page image is synthetic, generated at the page's actual
6,191 by 4,657 dimensions with the existing marquee bounds. The database page,
fragment and marquee were not edited. This validates viewing and selection,
not content editing or ImageFragment creation.

The web readiness reports match all four database object counts, with zero
invalid messages. Existing baseline diagnostics (60 Fragments without a Page
ID and 81 legacy type fallbacks) are preserved; they are not introduced by
Image catalogue reconciliation.

All test editing clients were quiesced before reconciliation. The administrative
utility ran with the production catalogue/file locks in the responder fixture's
filesystem; the idle responder remained available. It was then restarted twice.
The first restart published the newly committed catalogue. The second reproduced
the exact same database, file and retained-state snapshot.

## Storage and deployment implications

An initial Windows-backed Docker bind mount exposed the staging directory as
mode 777 and the responder correctly rejected uploads. The completed test uses
native container storage with an owner-only staging directory, exercising the
existing permission, locking, hard-link and atomic-move requirements. No storage
check was weakened. Files live in the disposable container layer; no named data
volume is created or removed.

The runner also waits for RPC readiness rather than merely HTTP availability,
and reserves one HTTP port across responder restarts because Docker's automatic
port allocation changed on restart during runner development.

This test does not certify the production NAS mount's storage capabilities.
Phase 11 must verify them on the configured deployment filesystem before
enabling uploads. Production deployment and live reconciliation remain undone.

## Evidence identity

`run/summary.json` is the successful run result. `run/artifacts.json` hashes the
actual JARs, Angular output and executed runner. RPC responses, live Image
publications, reconciliation plans/inventories/results, web readiness reports,
screenshots and filtered operational logs are also included. Authentication
replies and upload bytes are excluded from the filtered logs.

The bundle adds artifact-build logs, runtime image identities and final diff
checks. `SHA256SUMS.txt` freezes the package; `run/SHA256SUMS.txt` preserves the
runner's own original evidence manifest. Earlier failed fixture-development runs
remain in ignored build output and are not presented as passing evidence.
