# 0028 Step 1 — source readiness / implementation report (18 November 2026)

**State:** Step 1 IN PROGRESS; production inventory **NOT RUN**; no production
writes, service restarts, restores or migrations performed in this increment.

## Files inspected

- `diaries-sources-20261117-185710.zip` (source snapshot; no `.git` metadata)
- `playbook-sources-20261117-185515.zip` (production deployment layout)
- `0028-FEAT-planning-package-20261117.zip` (current design, steps and manifests)

The 0022 `Migration0022Inventory` is genuinely read-only but predates typed
Fragments: its SQL selects the legacy columns and **does not export**
`fragment.type`, `fragment.page_id` or `fragment.image_id`. It is not a
sufficient current-schema inventory by itself. The 0022 `LegacyImageDetector`
is a discovery parser, not a lossless HTML editor.

The 0024 `CandidateCrossReference` produces path/ID suggestions including
`UNIQUE_LOCAL_SUFFIX`; those are not authorised identity matches. The 0024
Image catalogue is now separate from fragment ownership, and Files integrity
must be verified independently.

The actual generated 0022 legacy-candidate and 0024 cross-reference CSV files
were not present in the inspected ZIP. The historical 0022 review ledger **is**
present at `change-control/complete/0022-FEAT - migrate fragments to explicit
page ownership and type/0022-static-baseline-20260911/review-ledger.json`.
It contains 42 decisions, of which 3 are typed IMAGE and only 2 have an
explicit database Fragment ID. It is historical review evidence, **not** the
complete candidate inventory.

The current responder models confirm Fragment `page_id`, `type`, `image_id`,
lock user/session and an optional Marquee relationship; Image has canonical
relative path and checksum. The current Playbooks role defaults production
Compose to `$HOME/projects/diaries`, database service `diaries-db` with
PostgreSQL 18 and `POSTGRES_USER`/`POSTGRES_DB` environment variables. The
actual live deployment directory, schema, versions, gate and service state
remain to be checked on pluto.

## This package delivers

- `tools/step1_inventory.py`: a one-shot SSH/Compose/psql **read-only** current
  database export with SHA-256, anomaly reporting and two entirely **unreviewed**
  manifest drafts. It runs on mango and streams CSV from pluto without a remote
  script/evidence directory. Python 3 stdlib only.
- Optional historic 0022 CSV, separate 0022 review ledger, and 0024 CSV
  cross-reference: drift and hint reports, **without approving an Image**.
- `tests/test_step1_inventory.py`: fabricated-data offline checks.
- `tools/STEP1-COLLECTION-RUNBOOK.md`: commands and evidence acceptance checklist.
- `.gitignore`: prevent accidentally committing private production diary text.

## Test evidence for packaging

The package author ran `python3 -m unittest discover -s .../tests -p
'test_step1_inventory.py' -v` against fabricated inputs in the isolated authoring
environment. All five tests passed. This is **local code-only evidence**, not a
result of Windows/mango execution or a production inventory.

## Outstanding acceptance work

1. Verify actual Windows/mango branch, revisions, dirty trees and submodules.
2. Verify production service versions, read/write gate and deployed schema.
3. Run the read-only current-schema snapshot on pluto and retain its receipt.
4. Locate/freeze actual historical 0022 and 0024 reports or document loss and
   regenerate with justified provenance.
5. Independently reconcile Files-root content, Image rows and checksums.
6. Manually approve every source and occurrence decision; freeze hashes.
7. Accept all evidence before Step 1 may be marked CLOSED.

The planned feature `IMPLEMENTATION-STEPS.md` and design contract are unchanged;
this is an **incremental Step 1 execution-preparation package**, not the final
gate closure.
