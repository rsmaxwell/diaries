## Phase 1 — baseline and evidence

Phase 1 evidence is complete as of 2026-09-12. The latest Files-root check is
[files-root-verification-20260912/verification-summary.json](files-root-verification-20260912/verification-summary.json).
It supplements the preserved header-only `files-root-summary.json` with full-file
readability and case-folded collision results. Known extension mismatches and
the reviewed 0022 reconciliation findings remain inputs for later phases.

Confirm 0022 is deployed and 0023 consumer changes are complete.
    Confirmed:
    - 0022 is deployed
    - 0023 consumer changes are complete

Record the responder/client/web versions used as the 0024 baseline.
    versions at baseline:    (as shown by     "git rev-parse HEAD")
        diary:         220e728388a989379841c6b2d43f1426cde14514
            responder: 2798bec79d9e4e1b649cf51256f5eeac58c63017
            client:    7311ec8f443b6fe752b2de3f69bc6415e5dc48b7
            web:       06453f7622f35a83c7a4b320c120e6ba99967a23

Back up the development database used for implementation tests.
    - data\database-backups\development-infrastructure\diaries-development-20260912-094003.dump
    - data\database-backups\development-infrastructure\diaries-development-20260912-094012.sql

### 0022 candidate/review evidence freeze

The complete static candidate/review input set is frozen in
[0022-frozen-20260912-complete](0022-frozen-20260912-complete/README.md), with
filenames and SHA-256 hashes in
[SHA256SUMS.txt](0022-frozen-20260912-complete/SHA256SUMS.txt) and verification
details in [verification.json](0022-frozen-20260912-complete/verification.json).
It supersedes the unchanged earlier partial snapshot `0022-frozen-20260912/`.

The 22 original input files comprise the review ledger, eight reconciliation
reports, six inventory outputs and seven planner outputs. All eight ledger
report hashes and all 15 planner input hashes match. All 73 image-bearing
database Fragments occur exactly once in the reviewed candidate report. The
legacy-image CSV alone contains only 22; the other 51 are classified as
orphan/inconsistent in the full inventory.

The Phase 1 evidence-freeze checkbox is complete. Archived planner validation
is `VALID`, with 62 warnings and `applyReady=false`: 61 Page-ownership cases
remain unresolved and Fragment 1738 has a reviewed MARQUEE override with a
separate source-only IMAGE target. These are preserved for later work. This
snapshot establishes the static 2026-09-11 evidence inputs, not final production
state or authorization to apply a Fragment migration.

### File RPC response compatibility baseline

Completed on 2026-09-12. See [rpc-responses/README.md](rpc-responses/README.md)
for the 33 captured MQTT cases, actual payload/status shapes, replay commands,
known baseline defects and intentional 0024 compatibility exceptions.
[SHA256SUMS.txt](rpc-responses/SHA256SUMS.txt) freezes this evidence package.
The three response JSON files in this directory are representative raw capture
records; the complete case set is under `rpc-responses/capture-20260912/`.

The harness uses the real responder file handlers, Authorization and MQTT RPC
dispatcher, a separate localhost Mosquitto broker and synthetic files/claims.
It does not start the full responder or access the database. Two repeat captures
matched all normalized baseline responses. All ten new client compatibility
tests and the client production build passed. The pre-change responder tests
and build also passed (127 tests, zero failures/errors/skips); see
[baseline-tests.txt](baseline-tests.txt) and
[validation.json](rpc-responses/validation.json).

### Files-root inventory relative-path correction

On 2026-09-12 the original CSV was found to have 97 rows with 97 blank
`relativePath` fields. The original calculated-property expression was
reproduced under Windows PowerShell 5.1: `[IO.Path]::GetRelativePath` is not
available there, and `Select-Object` leaves the failed calculated field blank.
The original capture's shell version was not recorded.

[generate-files-root-inventory.ps1](scripts/generate-files-root-inventory.ps1)
now verifies and removes the Files-root directory prefix, normalizes separators
to `/`, and rejects blank paths before exporting. It supports both Windows
PowerShell 5.1 and PowerShell 7, accepts `-FilesRoot` and `-OutputFile`, and
refuses to overwrite existing output. That version wrote the sibling
`files-root-inventory.corrected.csv`; the signature-aware version below writes
`files-root-inventory.detected.csv` by default.

The corrected script was run against the actual configured P: Files root in
Windows PowerShell 5.1. The resulting
[files-root-inventory.corrected.csv](files-root-inventory.corrected.csv) has
97 entries: 87 files and 10 directories, zero blank paths and zero duplicate
paths. SHA-256:
`393cfeb1dd4973303dfca86198f314cd1e390b9807a84a5c88b20562b3fccf3f`.
The original CSV is preserved as historical evidence; use the corrected CSV for
relative paths. This scan read NAS metadata only and did not modify NAS content.

Validation passed on PowerShell 5.1 and 7.6.5 with synthetic nested directories,
spaces and Unicode filenames, a trailing separator on the root, an empty root,
and attempted overwrite of an existing report. No application code or
configuration changed, so application builds/tests were not required.

That scan fixed path generation only. The metadata-only CSV does not establish
file-content readability or supported image types; see the subsequent scan below.

### Image types detected from file contents

Completed on 2026-09-12 using the updated
[generate-files-root-inventory.ps1](scripts/generate-files-root-inventory.ps1).
The script reads up to 16 bytes from each regular file and identifies JPEG,
PNG, GIF87a/GIF89a and WebP candidates from their signatures. Filenames do not
determine `detectedMimeType`. WebP requires `RIFF`, `WEBP` and a recognized first
chunk (`VP8 `, `VP8L` or `VP8X`). Signature references:
[WHATWG image MIME patterns](https://mimesniff.spec.whatwg.org/#matching-an-image-type-pattern)
and [WebP container specification](https://developers.google.com/speed/webp/docs/riff_container).

The newly generated
[files-root-inventory.detected.csv](files-root-inventory.detected.csv) preserves
all 97 paths from the corrected CSV and adds:

- `detectedMimeType`: supported image MIME type detected from bytes, otherwise blank;
- `signatureStatus`: `IMAGE_SIGNATURE`, `NO_SUPPORTED_SIGNATURE`, `UNREADABLE`,
  `SKIPPED_LINK` or `NOT_APPLICABLE`;
- `headerBytesRead` and `headerHex`: the inspected prefix, for review;
- `extensionStatus`: `MATCH`, `MISMATCH` or `NOT_APPLICABLE`;
- `inspectionError`: the reason if header inspection failed.

Directories are not inspected as files. Reparse points are recorded and skipped;
the traversal does not descend into directory links/junctions. Enumeration
errors stop the report, while individual header-read errors produce explicit
`UNREADABLE` rows. Existing output is never overwritten.

The actual P: Files-root scan in Windows PowerShell 5.1 produced:

| Result | Count |
| --- | ---: |
| Regular files | 87 |
| Directories | 10 |
| JPEG signatures | 51 |
| PNG signatures | 32 |
| GIF / WebP signatures | 0 / 0 |
| No supported image signature | 4 |
| Header-read failures | 0 |
| Links/reparse points | 0 |
| Extension mismatches | 2 |
| Blank relative paths | 0 |

The four nonmatching files are `Thumbs.db` files. The extension mismatches are:

| Relative path | Detected type |
| --- | --- |
| `diary-1831/images/img2805-blue-posts-pub.jpg` | `image/png` |
| `diary-1832/images/img3018-murder-of-nicholas-fairles.png` | `image/jpeg` |

They remain unchanged on the NAS. These are findings for reconciliation; an
extension mismatch does not by itself mean that the image bytes are corrupt.
The detected CSV SHA-256 is
`eb2a751fa41411fec41f528ba5ee7be1ffee0ae3b400e09f18b3d2a91d513d05`.
Both earlier CSVs are preserved; use the detected CSV for candidate MIME types.

Validation: [test-files-root-inventory.ps1](scripts/test-files-root-inventory.ps1)
passed in Windows PowerShell 5.1.26100.9444 and PowerShell 7.6.5. Each run checked
20 file cases, including actual PNG/JPEG fixtures renamed to misleading or
missing extensions; both GIF headers; all three WebP chunk variants; fake,
empty and truncated headers; a non-WebP RIFF file; and a locked file. It also
checked nested paths, skipped junction traversal, empty-root output, preservation
of fixture bytes and refusal to overwrite evidence. Header-only fixtures test
identification, not image decoding. No application code/configuration changed;
application tests/builds were not required for this script change.

To repeat the tests, pass a new disposable workspace directory:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\test-files-root-inventory.ps1 -WorkDirectory C:\path\to\diaries\build\new-signature-test
```

A recognized signature establishes an image candidate, not a fully valid or
decodable image. This bounded scan verifies header readability only; full-file
readability and image decoding are not claimed. The Phase 1 inventory item
was still open at this stage for full-file readability and case-folded path
collision evidence; both were subsequently completed below.

### Files-root summary

On 2026-09-12 the empty [files-root-summary.json](files-root-summary.json)
placeholder was populated from the saved `files-root-inventory.detected.csv`
using [summarize-files-root-inventory.ps1](scripts/summarize-files-root-inventory.ps1).
No new NAS scan was performed. All earlier inventory CSVs are preserved.

The summary records the source CSV filename, SHA-256 and byte length; 97 entries
(87 regular files and 10 directories); 93,058,826 regular-file bytes from
metadata; 83 image candidates (51 JPEG, 32 PNG); four files without a supported
image signature; two extension mismatches; and zero header-read failures or
links. It includes the paths for the four nonmatching files and two mismatches.
The summary's SHA-256 is
`f5ef104d15902692b9a61be218d645c65bc5b6396936919ee8010d2bc06019d5`.
Git attributes preserve its bytes for hash verification.

`generatedAtUtc` is the time this summary was derived, not a new scan timestamp.
The CSV does not contain its original scan time, so `sourceScanTimestamp` is
explicitly null. Full-file readability, image decoding and case-folded collision
checks are explicitly marked as not performed. Unknown failure/collision counts
are null, rather than zero. This summary completes the empty-summary fix; it
did not itself complete the remaining Phase 1 inventory checks. The subsequent
verification package below supplies those checks without changing this snapshot.

For future scans, `generate-files-root-inventory.ps1` automatically calls the
summarizer after writing its CSV. `-SummaryFile` selects the summary filename;
by default the CSV extension is replaced with `.summary.json`. Both output paths
must be new and outside the scanned Files root. To summarize an existing
signature-aware CSV, run from this evidence directory:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\summarize-files-root-inventory.ps1 -InventoryFile .\files-root-inventory.detected.csv -SummaryFile .\new-summary.json
```

The summarizer rejects older CSV schemas, blank or duplicate exact paths,
invalid inspection statuses and a CSV that changes during parsing. It refuses
to overwrite a nonempty summary. `-ReplaceEmptyOutput` permits replacement of
an existing zero-byte placeholder only, and was used for the repair above.

Validation passed in Windows PowerShell 5.1.26100.9444 and PowerShell 7.6.5:
the existing 20 file cases plus a directory and skipped junction reconcile with
summary counts; the source hash matches; unperformed checks remain explicit;
an empty inventory produces zero counts and empty arrays; and placeholder
replacement preserves an existing nonempty summary. No application code or
configuration changed, so application tests/builds were not required.

### Full-file readability and case-folded path verification

Completed on 2026-09-12, 19:25:00–19:25:04 UTC, using Windows PowerShell
5.1.26100.9444 against the configured development Files root:
`P:\nancy-and-ronald-maxwell\documents\sea-captains-chest\diaries-content\files`.

| Check | Result |
| --- | --- |
| Full reads through EOF | 87 of 87 regular files |
| Bytes read | 93,058,826 |
| Read failures | 0 |
| Per-file SHA-256 hashes | 87 |
| Paths checked for collisions | 97 (87 files, 10 directories) |
| Case-folded collision groups | 0 |
| Symlinks/reparse points | 0 |
| Drift from the detected baseline | None |
| Changes observed during verification | None |

The frozen [verification package](files-root-verification-20260912/verification-summary.json)
contains:

- [file-readability.csv](files-root-verification-20260912/file-readability.csv):
  each relative filename, expected bytes, bytes actually read, complete-file
  SHA-256, status and error field;
- [path-conflicts.csv](files-root-verification-20260912/path-conflicts.csv):
  a header-only CSV, meaning zero conflict rows; the summary explicitly records
  97 checked entries and zero groups, so this is distinct from missing evidence;
- [inventory-comparison.json](files-root-verification-20260912/inventory-comparison.json):
  empty difference arrays for baseline-to-before and before-to-after;
- baseline, before and after inventories, and their header-only summaries;
- [SHA256SUMS.txt](files-root-verification-20260912/SHA256SUMS.txt):
  filenames and hashes for all 11 package files other than the manifest itself.

All 11 manifest hashes were independently verified. The manifest SHA-256 is
`a4c04980aed91f748eac5e67ab7abcc1bf91d53be441c0e3777a5c60e358a529`.
Both fresh inventory CSVs are byte-identical to the preserved detected inventory
(`eb2a751fa41411fec41f528ba5ee7be1ffee0ae3b400e09f18b3d2a91d513d05`).
The formerly empty top-level [path-conflicts.csv](path-conflicts.csv) is now a
byte-identical alias of the package report, SHA-256
`e137bdbc9162873e59256114c89ee4f27c0ebf8fe7bdc2d66e7564eb2b2c6c37`.
Earlier populated evidence files and NAS contents remain unchanged.

[verify-files-root-content.ps1](scripts/verify-files-root-content.ps1) opens
regular files read-only, streams 64 KiB blocks through EOF into SHA-256, checks
length and modification time, then inventories the root again. Individual read
failures are recorded and prevent a clean result. Enumeration errors abort;
existing output directories are refused. Link entries are recorded but skipped,
and file path components are checked for reparse points before opening.

[find-case-folded-path-conflicts.ps1](scripts/find-case-folded-path-conflicts.ps1)
compares slash-separated, NFC-normalized paths after invariant lowercasing, using
ordinal grouping across files, directories and links. Original spellings remain
in the report. All 97 actual paths are ASCII. Unicode database collation
equivalence still needs review when implementing Phase 2's uniqueness index;
this report does not claim to test an index that has not yet been implemented.

To repeat the verification from this evidence directory, choose a new output
directory (the existing package is preserved):

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify-files-root-content.ps1 -FilesRoot 'P:\nancy-and-ronald-maxwell\documents\sea-captains-chest\diaries-content\files' -BaselineInventory .\files-root-inventory.detected.csv -OutputDirectory .\files-root-verification-NEW
```

[test-files-root-content.ps1](scripts/test-files-root-content.ps1) passed in
Windows PowerShell 5.1.26100.9444 and PowerShell 7.6.5. Tests cover multiple-buffer
reads and independently calculated hashes, empty files/root, junction exclusion,
an exclusive lock producing a read failure, added-file drift, case-only aliases,
NFC aliases, file/directory collisions, traversal rejection, overwrite refusal,
and manifest verification. Run it with `-WorkDirectory` pointing to a new
directory under `diaries/build`. No application code/configuration changed;
application tests/builds were not needed for this evidence tooling.

These are point-in-time readability checks, not image-decoding validation or an
atomic NAS snapshot. The original baseline had no full-file hashes, so identical
historical contents cannot be proved beyond its recorded metadata and headers.
The two known extension mismatches remain reconciliation findings. The Phase 1
inventory checkbox is now complete.

