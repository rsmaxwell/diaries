# 0028 — Design and interface contract

**State:** proposed implementation contract, not implemented or approved for production.
**Reviewed against:** `diaries-sources-20261117-185710.zip`, generated 2026-11-17 18:57 UTC.
**Owner of changes/evidence:** Diaries parent `change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/`.

## 1. Objective and scope

Deliberately migrate the *reviewed* legacy HTML `<img>` occurrences carried by old
Fragments to the existing first-class IMAGE model, without changing unrelated
text, Page ownership, dates, marquee geometry, reusable Image bytes, or existing
IMAGE Fragments. No automatic classification on detection alone. No Marquee
schema removal, new editor/reader feature, permanent Ansible role, or responder
startup auto-migration. 0029 owns final constraint/legacy cleanup.

Keep current invariants:

- `Fragment.page_id` authoritative; `type=MARQUEE` permits a Marquee and forbids `image_id`.
- `type=IMAGE` forbids a Marquee, and may reference zero or one catalogued Image.
- An Image may be referenced by any number of Fragments; deleting a Fragment
  must not delete its Image or its file.
- A deliberate `KEEP_LEGACY` MARQUEE may retain inline image markup, expressly
  recorded as a compatibility exception.
- `DEFER` leaves the *entire* candidate unchanged; resolution remains outstanding.

## 2. Verified starting interfaces (2026-11-17 source)

| Existing implementation | Contract 0028 must respect |
|---|---|
| `migration/migration0022/Migration0022Inventory.java` | Read-only CSV generator; fields include `fragment_id`, `fragment_version`, `inferred_page_id`, `marquee_id`, `embedded_image_count`, `embedded_image_src_values` and `text_md5` |
| `migration/migration0022/LegacyImageDetector.java` | Uses tolerant Swing HTML parser to inventory `<img>` sources, **not** an edit-safe source-span parser |
| `migration/migration0024/CandidateCrossReference.java` | Provides ordinal, status, Image ID, path and source SHA-256; allows `UNIQUE_LOCAL_SUFFIX` fallback, **which is only a review hint** |
| `ImageReconciler`, `ImagePathPolicy`, `Image` | Canonical Files-root paths, catalogue checksums and supported MIME are the matching authority; do not infer by basename |
| `Fragment`, `Marquee`, `Image` | JPA type/page/image relationships; Marquee still stores page_id; Fragment text max 4096 characters |
| `FragmentSequenceNormaliser` and `FragmentRepositoryImpl` | Sequence is DECIMAL(10,4), sorted **by date and sequence/id**, not just one Page; version bumps accompany changed sequences |
| `FragmentPublishDTO`, `MarqueePublishDTO` | Fragment retained topics `diaries/fragments/{id}` and `diaries/dates/{y}/{m}/{d}/{id}`; Marquee topics `diaries/marquees/{id}` and `diaries/diaries/{diaryId}/{pageId}/{marqueeId}` |
| `Synchronise` | DB/retained reconciliation is available; verify **both updated values and obsolete-key tombstones** |
| 0027 release evidence | Editor and reader support IMAGE and legacy compatibility; IMAGE authoring has been production-enabled |

**Source caveats.** The packaged 0022/0024 implementations do not contain their
actual generated candidate/reconciliation CSVs. The static 0022 review ledger is
historical and may not match current production rows. Existing IMAGE Fragments
created by 0027 must not be treated as legacy candidates. Obtain fresh read-only
snapshots before judging match counts, schema anomalies or whether any migration
is safe to perform.

## 3. Work location and operating model

Implement the maintained utility in `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/migration/migration0028/`,
with named JUnit and database integration tests under the corresponding
`src/test/java/.../migration/migration0028/`; register a guarded explicit
Gradle JavaExec task `migration0028ReviewedFragments`. This is application
code in the responder Git submodule, not a permanent Playbooks operation.
Put one-time wrappers, manifest templates and rehearsal helpers under this
feature's `tools/` and `tests/`. Do not add migration logic to normal responder
startup or long-lived production Ansible roles.

The utility has distinct modes:

| Mode | DB writes | Output |
|---|---|---|
| `analyse` | No | Fresh inventory, source-resolution and exception report |
| `validate-manifest` | No | Typed/semantic/schema validation of all reviewed decisions |
| `dry-run` | No | Exact per-date edit/insert/delete/version/order/text/MQTT plan |
| `apply` | Yes, explicitly authorised | Transaction receipts, durable journal, fail-stop errors |
| `postflight` | No | Reconciled post-state, chronology and retained-state evidence |

Default mode is `analyse` or `dry-run`, never `apply`; require explicit config,
new/empty output directory, manifest locations, approved plan and expected
hashes. The tool must work **offline with the responder and other writers
stopped**. Plan database mutations without MQTT access; after commit, resume
only the compatible responder and use its normal DB-to-retained replay. This
avoids publishing before commit and means replay/tombstones are a separate,
mandatory acceptance operation. During this window block client writes and
public reading of partially synchronized state if necessary.

## 4. Frozen input package and stable identities

Use **two authoritative reviewed CSV files** rather than repeating potentially
contradictory dispositions on every image occurrence:

1. `0028-dispositions.csv`: exactly one row for each **source Fragment**, including
   all the original 0022 legacy candidates and any later-discovered candidates.
   Contains `fragment_id`, `expected_fragment_version`, `page_id`, `marquee_id`,
   `fragment_type_before`, `year`, `month`, `day`, `sequence`, `original_html_sha256`,
   `embedded_image_count`, `disposition`, `review_note`, `reviewed_by`, `reviewed_at`.
2. `0028-image-decisions.csv`: exactly one row for each embedded `<img>` in each
   source Fragment, including unresolved/retained ones. Contains `fragment_id`,
   `embedded_image_ordinal` (1-based parser order), `original_src`,
   `original_src_sha256`, `resolved_relative_path`, `match_method`,
   `resolved_image_id`, `expected_image_checksum`, `occurrence_action`,
   `image_text`, `review_note`.

Both files are UTF-8 CSV with a versioned schema and explicit header validation.
A source Fragment with zero images has one disposition row, zero occurrence rows
and requires an explicit justification. Use the templates in `tools/templates/`.
The `original_src` value is **reviewed content**, not an executable URL/path.
`image_text` is reviewed assigned text/caption for a newly created IMAGE
Fragment, not a copy of the complete transcription.

Allowed `disposition`: `CONVERT_TO_IMAGE`, `SPLIT_MARQUEE_AND_IMAGE`,
`KEEP_LEGACY`, `DEFER`. Allowed `occurrence_action`: `REMOVE_AS_IMAGE`,
`KEEP_INLINE`, `DEFER`. All rows for one source Fragment must be consistent:

- `CONVERT_TO_IMAGE`: existing Marquee is a purely historical anchor; **at most
  one** `REMOVE_AS_IMAGE` occurrence, all embedded elements must be accounted
  for, no unreviewed HTML removal, Image ID may be blank only when explicitly
  justified. If multiple embedded images require retention, use a reviewed split
  or defer; never attach several Images to one Fragment.
- `SPLIT_MARQUEE_AND_IMAGE`: a real MARQUEE is retained; each approved
  `REMOVE_AS_IMAGE` becomes one ordered IMAGE Fragment, and each has exactly
  one reviewed valid Image ID. If any inline occurrence is unresolved, default
  to `DEFER` the whole source rather than silently convert a partial set.
- `KEEP_LEGACY`: all occurrences `KEEP_INLINE`; no text/Marquee/Image mutation.
- `DEFER`: all occurrences `DEFER`; no mutation. Still count as an unresolved
  prerequisite for later 0029 cleanup where applicable.

Unknown dispositions, duplicated ordinals, conflicting `fragment_id` fields,
missing review identity, stale versions, unseen `<img>` sources, or missing
reference evidence are fatal validation errors. All row and header hashes,
expected release revision, database identity and Files-root identity form the
signed-off plan identity. A manifest edit requires re-validation and re-approval.

Archive full original HTML and hashes only in suitably access-controlled,
non-public evidence/backups; never copy private diary text into public logs,
shared source ZIPs or the public Playbooks repository.

## 5. Source-to-Image matching

- Parse the *live original* Fragment HTML as a tolerant HTML fragment. Enumerate
  every `<img>` including missing/empty `src`, retaining stable 1-based ordinal,
  exact source and original text checksum.
- Use `ImagePathPolicy` and 0024 canonical path/checksum data; strip only known
  and explicitly reviewed legacy `/files/` prefixes, decode URLs carefully and
  reject traversal, absolute paths, external schemes, symlinks and invalid names.
- `EXACT` canonical match is preferred. 0024 `UNIQUE_LOCAL_SUFFIX` is **not
  authorisation** to mutate: record it as an exception requiring independent
  user-reviewed path, image ID and checksum. Never match on basename alone.
- Fail closed when file or Image row is missing, mismatched, ambiguous,
  checksum-drifted or unsupported. `EXTERNAL_URL`, data URLs and unknown forms
  require `KEEP_LEGACY` or `DEFER` unless explicitly and separately resolved.
- Require the approved Image ID, canonical path, current checksum and
  catalogue existence to agree with review evidence immediately before write.
- One Image can legitimately satisfy many approved source occurrences.

## 6. Exact text transformation

Use a real tolerant HTML parser to identify nodes; require defensible original
source spans or another verified lossless approach when removing approved tags.
The old `LegacyImageDetector` is for discovery only and **cannot safely remove
markup**. Never use string-wide regex/replace for editing.

Before committing any row, produce original HTML SHA-256, proposed HTML,
proposed SHA-256 and a byte/character-level diff. Preserve non-approved nodes,
text, whitespace and formatting. If the parser reserializes unrelated text,
changes HTML entities/attribute quoting, cannot isolate an `<img>` or wrapper,
leaves unexpected markup, or exceeds Fragment text length, **fail closed** for
review rather than silently accepting drift. Do not remove a figure caption,
link or surrounding block unless separately reviewed. Image captions are
allocated explicitly; leave transcription only on the MARQUEE by default.

Ensure the final HTML is still acceptable to the existing Angular legacy HTML
pipe and `diaries-web` sanitizer. Test tricky HTML, case folding, malformed
markup, adjacent images, attributes, `srcset`, nested links, Unicode and
repeated identical `src` values.

## 7. Transaction, sequencing and journal

1. Perform **full-batch preflight** read-only against the current DB and files.
   Refuse any unreviewed candidate or stale expected version, unexpected
   Page/Marquee/type/image/lock state, or inconsistent output plan.
2. Quiesce all writers, drain sessions, take and verify a fresh database backup
   and Files-root recovery point; record versioned deployment/migration tool
   identity and a restored rehearsal result.
3. Acquire one migration-level PostgreSQL advisory lock and lock all affected
   Fragment/Marquee rows in deterministic ID order. Process each **affected
   date as one transaction** (because ordering is date-wide). A failure rolls
   back that entire date, including every insert, update, Marquee delete,
   sequence change and journal entry. Stop the run on failure; earlier dates
   may remain committed and are tracked in the journal for safe resume.
4. For `CONVERT`: retain original Fragment ID/Page/date; set `type=IMAGE`,
   reviewed `image_id`, exact approved text; delete legacy Marquee in the
   same transaction, retaining its old ID/page/diary for later tombstone
   verification. Preserve all unaffected metadata including lock state.
5. For `SPLIT`: retain original Fragment ID/Page/Marquee/date and its approved
   non-image text as `MARQUEE`/null image; create one new `IMAGE` per approved
   image occurrence with its own generated ID and text; no Marquee for new rows.
6. Build a list for the whole date ordered by existing `(sequence,id)` as a
   baseline; inject newly created IMAGE rows immediately after their original
   in approved ordinal order. Resequence the entire resulting date to
   `1.0000, 2.0000, ...` using `DECIMAL(10,4)` rules, once per date. Lock and
   version any changed survivors; publish their final versions later through
   replay. Verify no unrelated source IDs, dates or relative chronology moved.
7. Write a durable SQL journal **inside the same transaction** with a unique
   source Fragment ID, preimage hash/version, disposition, affected date, old
   Marquee ID, postimage hash/version and `(image ordinal -> new Fragment ID)`
   mappings. Include journal schema/version and run/plan ID. Enforce uniqueness
   at the database level so duplicate inserts cannot occur after a crash.
8. On re-run, check committed journal **before** comparing the now-changed
   preimage version. Return `ALREADY_APPLIED` only after verifying the full
   expected post-state, generated IDs and hashes; return a hard conflict for
   divergent post-state. `KEEP_LEGACY`/`DEFER` generate explicit no-op reports,
   not fake mutation receipts.
9. **No MQTT publish inside a database transaction or the offline CLI.** After
   successful apply, restart compatible responder in a controlled way, run its
   DB-to-retained reconciliation, verify updated Fragment JSON, new date topics,
   removed Marquee topics/diary-tree entries and absence of orphan topics.
   Publication failure blocks acceptance but does not trigger blind DB replay.

Suggested durable tables: `migration0028_source` and
`migration0028_image_occurrence`, with migrations, indexes, uniqueness,
readback and rollback scripts in the responder submodule. Do not drop either
until separately approved after 0029; application rollback never silently
reverses user content. Always test crash/resume and conflicting journal rows.

**Sequence capacity check:** DECIMAL(10,4) supports a finite maximum. Validate
full date count before write, including generated rows. If an affected date
has other existing IMAGE Fragments, preserve their exact relative order and IDs.

## 8. Planned CLI and evidence contract

Illustrative planned CLI (not yet implemented; do not run these as commands):

```
:diaries-responder:migration0028ReviewedFragments
  -PmigrationConfig=<responder-config>
  -PmigrationMode=analyse|validate-manifest|dry-run|apply|postflight
  -PmigrationOutput=<new-empty-output-directory>
  -PmigrationDispositions=<reviewed-dispositions.csv>
  -PmigrationImages=<reviewed-occurrences.csv>
  -PmigrationPlan=<approved-dry-run-plan.json>        # apply only
  -PmigrationApproval=<signed-off-approval.json>     # apply only
```

Use normal responder config but require deliberate DB identity/file-root checks;
never log credentials. `apply` must refuse production unless exact manifest,
plan, tool revision, DB identity, approved source hashes and verified backup
receipts match. Out-of-date or changed files require a new review.

Each mode writes a self-contained summary JSON, sorted CSV diagnostics,
input SHA-256 manifest, counts grouped by disposition, per-date order before/
after, old/new HTML digests, catalogued Image provenance, journal receipt,
planned/observed retained-topic deltas and nonzero failure exit status where
appropriate. Dry-run must write **no DB, MQTT or Files-root content**.

## 9. Acceptance and production rollback boundary

- Run restored production-DB + Files-root rehearsal in an isolated environment
  with separate MQTT broker. Confirm backup and Files restore readback first.
- Test per-date atomicity, failure injection at each mutation, repeat apply,
  resume after partial-date success, missing/ambiguous Image, stale revision,
  lock/writer conflict and no-op decisions.
- Compare full pre/post rows, identities, HTML diffs, chronology, 0022/0024
  inventory coverage and journal against the approved expected output.
- Inspect both editor and reader for converted/split/KEEP/DEFER fixtures.
- Stop production writers, validate brand-new backups and rehearse identical
  tool/manifest hashes before **separately authorised** production apply.
- Prefer restore of the pre-migration DB (with the matching Files snapshot) as
  the defined rollback before any new writes are allowed. If new writes have
  resumed, whole-database restore would lose them; stop and design/test a
  journal-based selective reversal rather than silently restoring.
- Disabling IMAGE authoring is not a data rollback. Do not roll reader back
  below 0026; 0029 constraints and Marquee-column cleanup are out of scope.

The complete verification matrix is in `tests/ACCEPTANCE-TEST-MATRIX.md` and
work sequence is in `IMPLEMENTATION-STEPS.md`.
