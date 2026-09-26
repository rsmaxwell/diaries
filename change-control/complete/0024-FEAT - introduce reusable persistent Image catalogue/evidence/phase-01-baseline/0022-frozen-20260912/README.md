# 0022 evidence snapshot for 0024

Status: **PARTIAL — not yet the complete candidate/review input set**.

This snapshot preserves the restored 2026-09-11 static reconciliation baseline
and its review ledger. It is not evidence of the final production migration.
The snapshot capture time and per-file verification results are recorded in
`verification.json`.

## Provenance

- Source, relative to the Diaries repository:
  `change-control/complete/0022-FEAT - migrate fragments to explicit page ownership and type/0022-static-baseline-20260911/`.
- Source review ledger: `review-ledger.json`.
- Source reports:
  `reconciliation/diaries-static-reconciliation-with-images-3-20260911/`.
  These are copied into this snapshot's `reconciliation/` directory without
  modifying their bytes or basenames.
- Ledger baseline refresh: `2026-09-11T08:40:02.5304003+01:00`.
- Original reconciliation directory recorded by the ledger:
  `C:\temp\diaries-static-reconciliation-with-images-3-20260911`.
- Diaries checkout at capture: `220e728388a989379841c6b2d43f1426cde14514`.
  This identifies the checkout used to archive the evidence, not the original
  tool revision or the deployed production version.
- The restored reports do not establish the exact database backup identity or
  original tool revisions; these remain to be supplied with the remaining
  baseline provenance.

The source summary records 2,329 valid sources, 2,307 database Fragments, one
explicit IMAGE source, 29 legacy identity collision groups and enabled image
file validation. These counts are reconciliation counts, not a verified count
of all embedded-image candidates.

All eight reconciliation report hashes match the existing review ledger.
The ledger itself and the reports are also hashed independently in this
snapshot's `SHA256SUMS.txt`. This verifies consistency with the supplied ledger;
it does not establish independent authenticity or approve any migration.

## Missing evidence

The restored folder contains neither the matching generated 0022 inventory nor
the reviewed planner outputs. Obtain the originals from the same static run:

```text
inventory/
  0022-inventory.csv
  0022-legacy-image-candidates.csv
  0022-safe-marquee-candidates.csv
  0022-anomalies.csv
  0022-summary.json
  005-apply-safe-types.generated.sql
planner/
  validation-report.json
  migration-plan.json
  migration-plan.csv
  sequence-plan.csv
  image-candidates.csv
  summary.json
  input-checksums.sha256
```

Verify the planner's input hashes against the inventory, reports and ledger,
record its validation status and review its warnings before declaring the input
set complete. Do not substitute an inventory generated from today's live
database for the historical inventory without explicitly recording a new
baseline and reviewing the differences. The historical documentation's 73
database image candidates cannot be verified from this partial package alone.

The ancillary source files `image-file-layout.txt` and `reconcile-command.txt`
remain in the restored source folder. They are not included in this snapshot's
reconciliation inputs or checksum coverage.

## Freeze and use

`SHA256SUMS.txt` lists every snapshot file except itself, with lowercase SHA-256
and a path relative to this directory. `.gitattributes` disables Git text
normalization here so a later checkout preserves the hashed bytes. No original
report or ledger was re-exported or edited.

Keep this snapshot unchanged. When missing evidence is restored, create a new,
complete snapshot and explicitly identify it as superseding this partial one.
Preserve this snapshot and its manifest for traceability.

Before a 0024 reconciliation run, verify the complete snapshot's manifest and
archive it with that run's outputs. Stop on any missing file or hash mismatch.
The existing Phase 1 freeze checkbox must remain unticked until the complete
candidate/review evidence is available and verified.

0024 must preserve candidate and Fragment/source identity when reporting path
matches. Review decisions are historical evidence; they do not authorize 0024
to convert Fragments, change HTML or apply the archived 0022 SQL. Those Fragment
conversion decisions remain with 0028.
