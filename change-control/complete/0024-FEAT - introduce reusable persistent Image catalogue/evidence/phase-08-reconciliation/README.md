# 0024 Phase 8 — existing-file reconciliation utility

Implemented 2026-09-13. This phase supplies the administrative utility and its
actual-copy idempotency proof. Live reconciliation/deployment remains Phase 11.
The Files tree, live database, Fragment HTML and frozen 0022 evidence were not modified.

## Implementation

- `migration/migration0024/Migration0024ImageCatalogue.java`: CLI/configuration,
  input fingerprints and forced non-mutating schema configuration.
- `ImageReconciler.java`: two-way scan, reviewed plan validation, one-transaction
  inserts, verification and hashed evidence, including failure outcomes.
- `CatalogueStore.java`: existing Image repository/JPA transactions and the same
  PostgreSQL `pg_unicode_fast` lowercase expression as the unique index.
- `CandidateCrossReference.java` and `EvidenceCsv.java`: evidence-only CSV parsing,
  local path matching and candidate identity preservation.
- `utilities/ImageCatalogueService.java`: exposes the existing catalogue lock to
  serialize reconciliation with UploadFile/DeleteFile operations.
- `build.gradle`: adds the `migration0024ImageCatalogue` JavaExec task.
- `ImageReconcilerTest.java` and `ImageReconciliationIntegrationTest.java`: focused
  file, evidence, rollback, replay and actual PostgreSQL tests.

No RPC, client contract, retained topic shape, database schema or deployment
configuration changes are needed. The command never publishes MQTT itself:
normal responder startup replays the committed database afterwards.

## Run the command

From the `diaries` directory, use absolute configuration/evidence paths:

```powershell
.\gradlew.bat :diaries-responder:migration0024ImageCatalogue `
  '-PmigrationConfig=C:/work/reconcile/config.json' `
  '-PmigrationOutput=C:/work/reconcile/dry-run' `
  '-Pmigration0022Candidates=C:/work/frozen/image-candidates.csv'

# Review the inventory, every conflict and candidate reference, and archive/hash it.
.\gradlew.bat :diaries-responder:migration0024ImageCatalogue `
  '-PmigrationConfig=C:/work/reconcile/config.json' `
  '-PmigrationOutput=C:/work/reconcile/apply' `
  '-PmigrationMode=apply' `
  '-PmigrationPlan=C:/work/reconcile/dry-run/0024-create-plan.json' `
  '-Pmigration0022Candidates=C:/work/frozen/image-candidates.csv'
```

`migrationMode` defaults to `dry-run`. Apply requires the additional
`migrationPlan` parameter: fingerprints must come from the reviewed dry-run,
not from a fresh unreviewed scan at apply time. Evidence directories must be
new/empty and outside the Files root. A standalone packaged invocation is also
supported using `java -cp <fat.jar>` and the fully qualified main class with
`--config`, `--output`, `--mode`, `--plan`, `--0022-candidates`.

Use the normal responder JSON, with the root/database deliberately pointing at
the intended environment. Schema must already exist. The command disables
automatic schema creation/update; it uses configured administrative credentials.
It records input filenames/hashes, resolved root, database identity, build version,
timestamps and mode. Credentials and absolute host paths do not enter CSV rows.
Plans/summaries necessarily contain the resolved root identity. All output files
have hashes in `SHA256SUMS.txt`; preserve these with the reviewed plan.

Apply binds configuration/candidate hashes, resolved root, database identity,
all observed file fingerprints and existing Image metadata. File bytes are hashed
and decoded again before commit. Normal file operations share the same process
and filesystem lock, and a PostgreSQL table lock serializes Image writes for the
batch (five-second lock timeout). Stop external writers for the maintenance
window: these locks do not control arbitrary NAS tools or direct database clients.
Directory identity/contents are checked without relying on directory timestamps,
which Windows can update during reads. The private `.image-staging` tree is
excluded; recovery material there needs separate review. Apply may create that
private directory/lock file but never rewrites image bytes.

An apply creates only reviewed safe rows. Existing metadata conflicts, missing
bytes, case/normalization aliases, links and unsupported/undecodable files are
reported, not repaired. Supported content with a misleading extension keeps its
path and receives byte-derived MIME/dimensions. The shared inspector's default
20 MiB encoded, 40 million decoded pixels and 256-frame limits apply. `UNREADABLE`
includes corrupt/strict-decoder-rejected content and limit violations; `detail`
explains known inspection failures without exposing host paths. Readable rejected
bytes still receive a full SHA-256 fingerprint.

Ordinary pre-commit failures roll back the entire insert batch. Failure evidence
marks rolled-back rows, uncertain commits, or a committed batch whose later
verification/reporting failed. Do not infer that an uncertain commit did nothing;
inspect the database and a new dry-run before retrying. Connection/configuration
errors before a batch starts can fail before evidence exists. Do not reuse an
old output directory. A same-plan retry accepts only identical rows already
created by that plan; drift or unrelated new rows require fresh review.

Both frozen candidate schemas are accepted: planner `legacy_image_reference`
and inventory `embedded_image_src_values` (including multiple sources). The
report preserves Fragment ID, input row, source index and source SHA-256. Safe
local URLs are decoded once. Exact matches precede a unique local suffix match;
`matchMethod` records that inference. Unsafe/conflicting matches stay ambiguous.
External URLs and invalid local paths never become create instructions. No
conversion decision or Fragment HTML edit is made.

## Actual-copy proof

See `idempotency-proof.json` and the four independently hashed run directories.
The source copy contains all **87 files / 93,058,826 bytes**, including hidden
`Thumbs.db` files. `source-copy-sha256.csv` records every filename and hash;
source-before, copy and source-after hashes agreed during copying. The original
Files root was read only. The restored fixture used backup
`diaries-development-20260912-203528.dump` (SHA-256
`fe0e187eda4fe4c7923590f7ec5e36871ced87e2ba8fa6d3f882e0b0992d6b86`).
PostgreSQL 18 and Mosquitto 2.0.22 ran in dedicated temporary containers.

| Run/check | Result |
| --- | --- |
| Reviewed dry-run | 71 creates, 12 rejected images, 4 unsupported files, 10 directories |
| First apply | 71 rows committed |
| Second dry-run | 71 matches, zero creates |
| Second apply | Zero inserts; all 71 rows and metadata identical |
| Copied file verification | All 87 original file hashes unchanged |
| Diary/Page/Fragment/Marquee verification | Counts and whole-row fingerprints unchanged after apply and startup |
| Actual packaged responder startup | 71 retained Image topics, QoS 1, exactly matching all database metadata |
| Frozen 0022 cross-reference | 73 candidates: 60 matched, 13 ambiguous |

The retained check used a late subscriber, verified the retained flag and QoS
of every message, and compared both topic IDs and complete JSON payloads with
PostgreSQL rows. The responder used the copied Files tree mounted read-only.

## Conflict review and remaining data work

`conflict-review.json` reviews every rejected image. Eleven PNGs have an invalid
CRC on the ancillary `iCCP` colour-profile chunk. The JPEG
`img2926-burnhopeside-hall.jpg` has 1,573 trailing bytes after its final end marker;
the current strict inspector requires the marker at the file end. These findings
do not establish that their visible pixels are unusable. They explain why the
shared inspector excludes them. No decoder rule was relaxed and no file repaired.

Four `Thumbs.db` files are unsupported generic content and are correctly excluded.
The two known extension mismatches are accepted using their actual byte types;
paths/extensions remain unchanged.

`candidate-review.json` explains the 13 ambiguous candidates: twelve reference
rejected files; Fragment 1564 has a suffix that matches two different local Image
paths. An equal checksum does not merge path identities. Keep these unresolved
for explicit content review and later 0028 decisions. A zero-create second run
proves idempotency; it does not claim every legacy file is now a valid Image.

Phase 8's utility and proof are complete. Content repair decisions, remaining
0024 deployment gates and 0028 conversion decisions are separate follow-up work.

## Local reconciliation addendum — 2026-09-23

The previously rejected local image files were repaired, the two misleading
filename extensions and associated metadata/references were corrected, and the
reviewed reconciliation was applied to the development database. The follow-up
dry-run found 83 catalogue matches, zero creates and zero conflicts, with all 73
candidates matched to one Image. See the archived
[local reconciliation evidence](local-reconciliation-20260923/README.md).

This addendum resolves the local data-review items described above. The original
actual-copy proof remains unchanged as the audit record of the pre-repair state.
Production reconciliation remains a Phase 11 activity.

## Validation

The final complete responder suite and build passed: **232 tests, zero failures, zero errors, zero skips**, with PostgreSQL and MQTT integration enabled. See `test-results.json` and `test-build.log`. The final packaged utility also replayed the original 71-image plan: 71 `ALREADY_MATCHED`, zero inserts and complete verified candidate evidence (`final-same-plan-replay`).

Existing Gradle deprecation and Shadow service-merge warnings remain. No client code or RPC contract changed; client tests/build were not rerun for this administrative command. The local cross-component check used the actual packaged responder, restored PostgreSQL database and isolated MQTT broker. No live deployment was performed.
