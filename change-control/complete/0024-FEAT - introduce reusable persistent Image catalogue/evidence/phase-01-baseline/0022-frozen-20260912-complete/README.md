# Frozen 0022 candidate/review evidence for 0024

Status: **COMPLETE for the Phase 1 static candidate/review evidence freeze**.

This snapshot supersedes `../0022-frozen-20260912/`, which remains unchanged as
the earlier partial snapshot. Use this complete snapshot as the static 0022
evidence supplied to 0024 reconciliation. It does not establish production
deployment, current database state, current file availability or migration
approval.

## Provenance and selected files

All 22 input files were copied byte for byte from the restored `../0022/`
directory. The exact source-to-snapshot filename mapping, source/copy hashes and
UTC capture timestamp are recorded in `verification.json`.

| Restored source under `../0022/` | Snapshot destination | Files |
| --- | --- | ---: |
| `review-ledger.json` | `review-ledger.json` | 1 |
| `diaries-static-reconciliation-with-images-3-20260911/` | `reconciliation/` | 8 |
| `diaries-0022-inventory-final-20260911/` | `inventory/` | 6 |
| `diaries-reviewed-migration-plan-20260911/` | `planner/` | 7 |

The ledger identifies the static reconciliation baseline refreshed at
`2026-09-11T08:40:02.5304003+01:00`, originally located at
`C:\temp\diaries-static-reconciliation-with-images-3-20260911`.
Its review ledger and eight reports also match the previous partial snapshot.
Diaries checkout at capture: `220e728388a989379841c6b2d43f1426cde14514`.
This is the archiving checkout, not a claim about the original tool revisions.

Earlier ledgers, earlier inventories/reconciliations, applier SQL packages,
rehearsal logs and backup files in the restored directory are not selected as
0024 reconciliation inputs and are outside this manifest's coverage. The exact
original tool revisions and database-backup association are not established by
the selected reports. No database restore or migration was performed to freeze
this evidence.

## Integrity and candidate coverage

- All eight reconciliation report hashes match the review ledger.
- All 15 entries in `planner/input-checksums.sha256` match the selected ledger,
  six inventory files and eight reconciliation reports.
- All 22 copied input files match their restored sources.
- The full inventory contains 2,307 Fragments. Exactly 73 contain an embedded
  image: 22 classified `LEGACY_IMAGE_CANDIDATE` and 51 classified
  `ORPHAN_OR_INCONSISTENT`. None contain multiple embedded images.
- `planner/image-candidates.csv` has exactly one row for each of those 73
  Fragment IDs, with no missing, extra or duplicate ID. 71 image references
  match the raw inventory; the two different references for Fragments 84 and
  1182 exactly match explicit `image.relative_path` overrides in the ledger.
  Preserve both raw and reviewed paths in reconciliation evidence. The
  inventory summary records 72 unique embedded image sources.
- The planner records 2,329 source records, 2,330 planned targets and 73 deferred
  IMAGE actions. These are different counts from the 73 existing database image
  candidates and must not be treated as interchangeable identities.

**Do not supply only `inventory/0022-legacy-image-candidates.csv`: it contains
only 22 of the 73 database image candidates.** Supply the full inventory and
review context. Use the original Fragment ID for database candidates and the
source key for source-only records; neither sequence nor path alone identifies
a candidate.

The archived planner validation is `VALID`, with zero errors and 62 warnings:
61 unresolved Page-ownership cases and the reviewed override retaining Fragment
1738 as MARQUEE. The separate IMAGE source
`fragments/1832/06/27-m3-img3018-murder-of-nicholas-fairles-image` is preserved in
the plan/ledger/source evidence. It has no database Fragment ID in this static
baseline. Its source identity must remain distinct from Fragment 1738 when
cross-referencing its path. The 73 IMAGE targets comprise 72 existing database
targets plus this source-only target. The archived planner reports
`applyReady=false`.

These warnings and deferred decisions do not prevent freezing this static
evidence. They are not resolved or approved by this freeze. 0024 classifies
candidate path matches and creates Image catalogue rows only; Fragment
conversion, splitting, HTML changes and Marquee changes remain outside 0024.
The archived `005-apply-safe-types.generated.sql` is provenance only and must
not be executed as part of 0024 reconciliation.

## Checksum manifest and future use

`SHA256SUMS.txt` records lowercase SHA-256 and relative filename for every file
in this snapshot except the manifest itself. `.gitattributes` disables text
normalization so Git preserves the hashed line endings. Hashes refer to file
bytes, not parsed/re-exported JSON or CSV.

Before using the snapshot, recompute every listed hash and stop on a missing
file, mismatch or unexpected file. Retain this manifest with the 0024 run
outputs and record this snapshot's name. Preserve every supplied candidate in
the cross-reference, including unresolved, external, invalid or ambiguous
paths. Do not merge away distinct candidates sharing an image path.

Keep the snapshot unchanged. Corrections require a new explicitly identified
snapshot and a recorded comparison with this one. Current production state and
the actual Files root require their own 0024 dry-run evidence; a static report
does not establish that a historical path still exists or has unchanged bytes.
