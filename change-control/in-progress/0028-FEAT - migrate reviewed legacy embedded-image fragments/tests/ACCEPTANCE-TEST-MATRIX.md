# 0028 — Consolidated acceptance test matrix

These are **planned** tests, not executed results. Record test ID, command,
revision, input hash, result, raw log and evidence path after real execution.

| ID | Fixture / action | Required result |
|---|---|---|
| T01 | Frozen historical + live candidates, one new, one stale, one pre-existing IMAGE | Coverage and drift explicit; existing IMAGE not converted |
| T02 | Disposition duplicate, missing reviewer, missing source ordinal, bad enum | Strict manifest rejection, no writes |
| T03 | Repeated same `src`, 2+ images, mixed case HTML, missing `src` | Stable ordinal enumeration, no accidental removal |
| T04 | HTML entities, whitespace, malformed tags, quoted attributes, links/figure/captions, Unicode | Only approved spans change; unrelated text byte-for-byte stable |
| T05 | External/data URL, traversal, absolute/symlink, no file, unsupported file | Fail closed / whole Fragment deferred |
| T06 | 0024 `UNIQUE_LOCAL_SUFFIX`, case collision, identical basenames, checksum drift | Cannot automatically authorize conversion |
| T07 | Valid `CONVERT_TO_IMAGE`, one attached Image | Original ID/Page/date stays; Marquee removed; text exact |
| T08 | Explicit approved null-Image conversion, zero-image source | Requires review justification; no fake catalogue ID |
| T09 | Split one MARQUEE with 3 images | Original ID/Marquee retained; 3 IMAGE IDs, Image relations, ordinal order |
| T10 | Split with captions and other transcription | Captions allocated once as reviewed; original non-image text unchanged |
| T11 | KEEP_LEGACY and DEFER with images | No mutation or version bump; decisions reported |
| T12 | Mixed existing IMAGE/MARQUEE on same date; two sources split | Global date order stable, four-decimal sequences contiguous, versions correct |
| T13 | Two dates, fail injected inside second date | Entire second date rolled back; first committed with journal, resumable |
| T14 | Fail after insert, before Marquee delete, during resequence, before journal commit | Zero partial rows from failed transaction |
| T15 | Apply same reviewed plan twice; restart between | Second run `ALREADY_APPLIED`, zero duplicate rows/new IDs, check full postimage |
| T16 | Apply with changed original version, HTML, Marquee/page, image metadata or editor lock | Refuse stale plan before DB write |
| T17 | Dry-run on snapshot | Identical DB, MQTT, Files checksums; complete planned diffs |
| T18 | Responder restart/replay after apply | New/changed canonical/date topics match DB; removed Marquee/tree retained topics tombstoned |
| T19 | Stop after commit but before replay; restart later | No duplicate DB inserts, replay converges |
| T20 | Restoration of matched production DB and Files snapshot in isolated stack | Backup readable; counts, constraints and file checksums valid |
| T21 | Angular editor + diaries-web fixtures | Converted, split, legacy and deferred rows render with correct date/order |
| T22 | Reference-aware Image deletion, normal text updates, locking/chronology | Existing 0025/0027 protection and UX have no regression |
| T23 | 0022 candidate coverage, 0024 Image IDs, 0028 journal | Every candidate has one decision, every split has exact generated-ID mapping |
| T24 | Production writer-stop and current deployed versions before apply | All locks/sessions/writers quiescent; strict preflight and backup receipts pass |
| T25 | Production smoke and final retained-state diff | No unexplained differences; reports and recovery window archived |

Consolidate JUnit, DB integration, client, reader and restored-production
rehearsal into a practical verification run. Mark each case **PASS/FAIL/NOT RUN**
with evidence; absence of a run is not a pass. Do not target live production
from automated failure-injection fixtures.
