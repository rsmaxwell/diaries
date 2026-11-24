# 0028 — Step 2 implementation delivery and limitations

**Delivery:** Java implementation for the 71 explicitly reviewed in-place
`CONVERT_TO_IMAGE` sources plus one auditable `DEFER`. This is not production
acceptance or permission to run `apply`.

## Source changes

`diaries-responder` submodule:

- `migration/migration0028/`: strict RFC-4180 CSV reader; immutable SHA-pinned
  V2 manifest loader; lossless **inspection-only** tolerant HTML parser;
  JDBC store and 5-mode explicit CLI; exact reviewed JSON dry-run plan.
- `src/main/resources/migration0028/001-create-journal.sql`: version-1 source
  and occurrence journal schema, installed separately (never automatically).
- `build.gradle`: explicit `migration0028ReviewedFragments` Gradle JavaExec task.
- `src/test/java/.../migration0028/`: pure validation and HTML unit cases.

Five modes are implemented: `analyse`, `validate-manifest`, `dry-run`, `apply`
and `postflight`. Default Gradle mode is `validate-manifest` and Java CLI
mode is `analyse`; neither performs writes. DB read-only modes use only SELECT.
`apply` requires a reviewed plan and a separate scope-specific approval JSON,
including review hashes, exact DB and Files-root identities, declared stopped
writers, approver identity/time, and an explicit production flag for production
scope. The program does not open MQTT connections.

## Approved 71-row mutation semantics

- Existing Fragment **ID, date, sequence and lock metadata** are preserved.
  `page_id` becomes the reviewed destination; `type=IMAGE`;
  `image_id` becomes the reviewed catalogue Image; `text` becomes the
  reviewed caption; `image_link_url` is preserved exactly where approved.
- A source Marquee is never deleted, detached, re-created, or geometrically
  modified. Its ID, page, version and numeric geometry must match the frozen
  review before and after conversion.
- Source HTML is compared by SHA-256, and inspected for exactly one matching
  image, the expected link and no unapproved narrative text. The original
  HTML is stored in the private database journal on a successful conversion.
- Image metadata and the existing file's SHA-256 must match the reviewed
  catalogue; no image or Files-root bytes are written.
- Date order is preserved without resequencing: the accepted manifest has one
  IMAGE replacement **per existing Fragment** and no insert or split. No
  unrelated Fragment sequence/version is changed.
- Each date commits in one transaction, with session advisory lock,
  row/version/Marquee locking, source SHA verification, journal uniqueness
  and transaction-local journal rows. Later-date failures roll back that date
  and stop the run. Earlier committed dates are verified and report
  `ALREADY_APPLIED` on a resume, without duplicate inserts.
- Postflight reads the source journal, observed IMAGE fields, Marquee geometry,
  link, chronology, and catalogue/file digests. MQTT replay and visual Reader
  regression remain **separate mandatory acceptance evidence**.

## Explicit limitations and acceptance status

The planned generic `SPLIT_MARQUEE_AND_IMAGE` workflow, arbitrary multi-image
HTML node surgery, zero-image conversion and `KEEP_LEGACY` are **not**
implemented in this exact-scope tool: the 72-row reviewed manifest contains
none of those mutations. An unknown disposition/multiple ordinal/destructive
review action fails before any DB write. If 0028 later needs them, the
implementation/acceptance matrix must be expanded and reaccepted.

Off-host checks performed when preparing the source package:

- Java 21 source compilation with minimal API **stubs**, not a real Gradle
  dependency build: PASS (syntax/type-shape check only).
- Nine CSV/HTML regression methods run using a lightweight local assertion
  harness: 9 PASS, 0 FAIL (not a claim of a Windows JUnit run).
- The HTML inspector checked all 71 preserved 21-November source occurrences:
  71 PASS, 0 FAIL. This was a read-only offline source inspection, not a
  live DB run; no private source HTML is in the ZIP.

**NOT YET TESTED:** Windows Gradle build and real JUnit, PostgreSQL schema
installation, DB integration, failure injection, restored-production rehearsal,
production migration, MQTT replay, editor/reader post-migration acceptance.
Step 2 therefore remains **OPEN**.
