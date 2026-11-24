# 0028-FEAT - Migrate reviewed legacy embedded-image fragments

<!-- 0028-STEP4-CURRENT-STATUS-BEGIN -->

**Current accepted status (24 November 2026):** Steps 1 and 2 technical
acceptance recorded; **Step 3 CLOSED by explicit owner acceptance** after 71
production conversions, database postflight, MQTT startup synchronisation and
Editor/Reader visual acceptance. Fragment **1564 remains DEFERRED**.
The temporary production migration stage has been SHA-256 archived to ignored
private evidence and removed from `pluto`. **Step 4 remains OPEN** pending
final documentary reconciliation and explicit *feature* closure approval.
See [Step 4 closure review](reports/STEP4-CLOSURE-REVIEW-20261124.md).

Historical planning/status paragraphs below describe earlier checkpoints, not
current production state.

<!-- 0028-STEP4-CURRENT-STATUS-END -->

## Type

Feature

## Status

**ACTIVE — resumed 21 November 2026, after formal closure of 0051.**
[0051 IMAGE links and optional Marquees](../../complete/0051-FEAT%20-%20extend%20IMAGE%20fragments%20with%20links%20and%20optional%20marquees/README.md)
was deployed and formally closed at Diaries parent commit `0818179`.
0028 Step 1 remains **OPEN**: there is no accepted migration manifest, no
restored rehearsal and no authorised production conversion. Historical evidence
and uncommitted work must remain intact.

The retained baseline is the 18 November frozen inventory and private review
export **(15)**, SHA-256
`7ff753b34ea5d7b7f19affdcce23ab2754d4d496544c2b6bffaa4db325250957`.
Its exact copy and check results are under
`evidence/Step 1/private/20261120-export-15-review-check/`. Nine rows pass draft
checks; 63 have outstanding items. These are draft checks, not migration
approval. Preserve all earlier exports and original checksum manifests.

**Resumption requirement (now active):** the pre-0051 IMAGE/no-Marquee rules and mandatory
Marquee deletion described below and in the existing design are historical
planning assumptions. Do not execute them unchanged. 0051 must deliver the
preservation contract and updated review tooling; then reconcile fresh live
evidence, re-review changed expectations, and resume 0028's own acceptance,
rehearsal and explicit production-apply gates. Page, text and Image decisions
remain outstanding independently of 0051.

See [DESIGN-AND-INTERFACE-CONTRACT.md](DESIGN-AND-INTERFACE-CONTRACT.md),
[IMPLEMENTATION-STEPS.md](IMPLEMENTATION-STEPS.md) and
[reports/SOURCE-REVIEW-20261117.md](reports/SOURCE-REVIEW-20261117.md).

## 0051-compatible, read-only review tooling (Step 4 handoff)

The [0051 migration compatibility addendum](DESIGN-AND-INTERFACE-CONTRACT.md#0051-step-4-compatibility-addendum--authoritative-for-resumption-20-november-2026)
and [offline v2 reviewer](tools/step4_0051_compatibility_review.py) supersede the
old no-Marquee IMAGE assumption. The original frozen inputs, private v1 draft
export (15), and all earlier checks are preserved unchanged. A v2 draft is
never implicitly approved; Marquee version/geometry require a fresh read-only
snapshot and any stale row remains a blocker. 0028 Step 1 remains OPEN; no production apply is authorised.

## Resumption execution — 21 November 2026

Run `tools/resume-step1-post0051-readonly.sh` **from the authoritative Windows
Cygwin Diaries checkout** to collect a fresh read-only inventory directly over
SSH to `pluto`, generate a new private v2 review against the archived inputs,
and report draft blockers. It neither changes production nor copies private
HTML to a public repository. See
[reports/STEP1-POST0051-RESUMPTION-20261121.md](reports/STEP1-POST0051-RESUMPTION-20261121.md).

## Priority

High

## Opened

2026-09-08

## Summary

Consume the legacy embedded-image candidate inventory produced by 0022 and the Image catalogue reconciliation produced by 0024. Provide a dry-run and reviewed-manifest migration which deliberately converts each approved legacy row into the accepted typed Fragment model without guessing intent or losing production content.

## Background

Some existing Fragment text contains one or more `<img>` elements. Those rows still have legacy Fragment/Marquee structure and currently render because the image URL is embedded in HTML. Detection alone cannot determine whether the row is:

- fundamentally an IMAGE Fragment;
- a real MARQUEE Fragment with a supplementary image;
- malformed, missing or external content;
- an intentional compatibility exception.

The accepted target invariant remains:

```text
MARQUEE Fragment -> optional Marquee, no Image
IMAGE Fragment   -> optional Image, optional same-Page Marquee, optional imageLinkUrl
Fragment         -> zero or one Image; at most one Marquee
Image            -> zero or more Fragments
```

Therefore a legacy MARQUEE containing several embedded images cannot become one IMAGE Fragment with several attachments. It must be reviewed and, where approved, split into separate ordered IMAGE Fragments.

## Preconditions

- 0022 inventory is complete and preserved.
- 0024 reconciliation maps supported Files-root images to stable Image IDs.
- 0025 supports IMAGE persistence, locking, publication and safe Image deletion.
- 0026 web rendering is deployed.
- 0027 client editing is deployed and verified (completed 2026-10-06).
- a production database backup and Files-root snapshot have been restored and rehearsed in a disposable environment.


## Planning resumption — 17 November 2026

The authoritative 17 November Diaries bundle confirms that **0027 is completed**
(production IMAGE editing enabled on 6 October 2026). The 0026 reader was also
previously deployed. This supersedes the *historical* 1 October 0026 handoff
below; that earlier handoff is retained for traceability.

The 0022 inventory and 0024 reconciliation tools exist, but their **generated
live candidate CSVs are not in the supplied source bundle**. The 0022 baseline
contains historic static-import/review evidence; it is not a substitute for a
fresh inventory of the current database. No candidate counts, approved Image
matches or migration eligibility are assumed. Existing production IMAGE
Fragments created through 0027 must be excluded from legacy conversion.

**Implementation approach:** one explicitly invoked offline responder-side
migration, a reviewed *fragment-level* disposition manifest plus reviewed
*image-occurrence* decisions, deterministic date-wide chronology changes,
transactional durable journalling, and PostgreSQL-to-MQTT replay after writes
are stopped. Preserve all original text and lineage evidence. No automated
production conversion, schema cleanup, Image-file movement or Ansible changes
are authorised by these planning documents.

**Review before copying the package:** the 18:57 source snapshot contains only
this feature's `README.md`; the later screenshot shows
`DESIGN-AND-INTERFACE-CONTRACT.md` and `IMPLEMENTATION-STEPS.md` as well.
Compare those potentially newer local files in Beyond Compare and preserve any
additional local edits rather than overwriting them blindly.

## 0026 Reader Handoff — 2026-10-01

The 0026 web-reader prerequisite is satisfied: the exact reader candidate was verified with controlled IMAGE fixtures, deployed to `pluto`, and production smoke checks passed with `content.filesPath=files`, read-only Image MQTT access and `imageFragmentWritesEnabled=false`.

This does **not** make 0028 executable yet. 0027 remains a prerequisite because migrated rows need an available editor/correction path, and 0028 still requires its own reviewed disposition manifest, disposable rehearsal, fresh production backup/Files snapshot and explicit writer-stop/apply runbook. No legacy conversion was performed by 0026, and the production database still had zero IMAGE Fragment rows at the 0026 deployment close-out.

Authoritative reader evidence is in `../../complete/0026-FEAT - render ImageFragments in diaries-web/evidence/Step 15/`; the completed feature handoff is in that feature's `evidence/Step 16/`.

## Inputs and Preserved Evidence

The migration must consume versioned, reviewable input and analysis evidence:

```text
0022-legacy-image-candidates.csv      # actual 0022 generated name
0024-candidate-cross-reference.csv     # actual 0024 generated name
0028-dispositions.csv                  # one reviewed row per source Fragment
0028-image-decisions.csv               # one reviewed row per embedded image occurrence
```

The 0022 and 0024 generated files are **not contained in the supplied 17 November
source bundle**; recover or regenerate and reconcile them against the live
current-schema inventory before review. See the precise fragment- and
occurrence-level headers in the design contract and `tools/templates/`. Together
the two 0028 manifests carry the original required fields: Fragment ID, expected
version, Page/Marquee, date/sequence, embedded ordinal, original source,
resolved Image ID, disposition, review note, reviewer and timestamp.

Do not accept a manifest when the live row/version, Marquee relationship,
embedded source list or resolved Image differs from the reviewed expectations.

## Allowed Dispositions

### `CONVERT_TO_IMAGE`

Use when the existing Fragment is semantically an image occurrence and its Marquee is only a legacy/artificial anchor.

- preserve Fragment ID, Page, date and sequence;
- set `type=IMAGE` and the approved `imageId`;
- preserve the original same-Page Marquee ID/version/geometry by default when explicitly reviewed under 0051; remove it in the database transaction **only** when separately reviewed and confirmed;
- remove only the reviewed `<img>` markup from Fragment text;
- retain meaningful accompanying text as the IMAGE Fragment text;
- increment/version the Fragment according to the approved migration policy;
- publish the Fragment update and Marquee tombstone after commit.

This disposition is valid only when the candidate resolves to zero or one intended Image. A null Image is permitted only if explicitly reviewed and justified.

### `SPLIT_MARQUEE_AND_IMAGE`

Use when the existing Fragment is a genuine transcription/source fragment but also contains supplementary images.

- preserve the original Fragment ID, Page, Marquee, date and non-image text;
- classify/retain the original as `MARQUEE` with `imageId=null`;
- remove only the approved embedded `<img>` markup;
- create one new `IMAGE` Fragment for each approved image;
- each new Fragment references exactly one Image and has no Marquee;
- place new fragments immediately after the original in embedded-image order;
- normalize all affected sequences deterministically;
- publish every changed/new Fragment after commit.

If useful captions or text are associated with individual images, the reviewed manifest must specify their allocation. The migration must not duplicate the full transcription text onto every generated IMAGE Fragment.

### `KEEP_LEGACY`

Preserve the row, Marquee and HTML unchanged as an explicit compatibility exception. Where the relationship is valid, assign/retain `type=MARQUEE` and `imageId=null`; the embedded HTML is legacy presentation content, not a first-class Image relationship. Record why normalization is inappropriate. A remaining `KEEP_LEGACY` row means the system still intentionally supports legacy inline image markup and final documentation must say so.

### `DEFER`

Make no change. Use for missing files, external URLs, ambiguous matches, undecided semantics or stale inventory. Deferred rows remain an open migration item, block a claim that legacy conversion is complete, and must be resolved before 0029 can enforce any constraint which the row does not satisfy.

## Matching Rules

- normalize relative Files-root paths using the same code/rules as 0024;
- do not match solely by basename;
- prefer exact normalized path;
- checksum may confirm a match but must not silently substitute another historical path;
- record redirects, URL decoding and legacy prefix removal explicitly;
- classify remote HTTP(S), data URLs and unsupported formats separately;
- one catalogued Image may be reused by many conversions;
- ambiguous and missing matches require `DEFER` until reviewed.

## Migration Utility

Implement an explicitly invoked migration utility, not responder startup behaviour. It must support:

```text
analyse/dry-run
validate-manifest
apply
postflight
```

Dry-run output includes planned inserts, updates, deletes, sequence changes, MQTT effects and unresolved candidates. `apply` must be idempotent: rerunning after success reports already-applied outcomes rather than creating duplicate IMAGE Fragments.

Use a migration journal/table or equally durable record mapping each source Fragment/image ordinal to any generated Fragment ID. Execute each candidate as a transaction or use a documented batch transaction boundary that cannot leave a half-split Fragment.

Do not publish MQTT changes before database commit. After apply, run normal responder replay/reconciliation so retained state converges with PostgreSQL.

## Text/HTML Preservation

- archive the complete original Fragment text and a checksum in migration evidence;
- parse HTML with a real HTML parser;
- identify elements by reviewed ordinal/source, not broad string replacement;
- preserve all non-approved nodes, text and formatting;
- canonical serialization changes must be reported;
- sanitise rendered output through the normal consumer policy;
- never remove unresolved embedded images as a side effect of migrating another image in the same Fragment.

## Preflight and Postflight

Preflight verifies:

- every manifest Fragment and version exists;
- Page/Marquee/type state matches expectations;
- every referenced Image exists and its path/checksum matches reconciliation evidence;
- all dispositions satisfy type cardinality;
- generated sequence plan is deterministic;
- no production writer is active during apply.

Postflight verifies:

- original Fragment IDs still exist except where no approved operation permits otherwise;
- conversions have type/image/marquee relationships required by their disposition;
- splits produced exactly the journalled Fragment IDs and count;
- dates and order reconcile;
- unapproved HTML is unchanged;
- every 0022 candidate has one recorded disposition;
- DB and retained entity/topic counts reconcile;
- both applications display representative converted, split and unresolved cases.

## Detailed Implementation Steps

- [ ] Freeze and checksum the 0022 and 0024 input inventories.
- [ ] Build a combined candidate report with exact Image matches and anomalies.
- [ ] Define and review the 0028 disposition manifest schema.
- [ ] Review every candidate manually and record a disposition.
- [ ] Implement HTML parsing/extraction tests for known legacy forms.
- [ ] Implement dry-run and manifest validation.
- [ ] Implement durable idempotency/journal recording.
- [ ] Implement transactional `CONVERT_TO_IMAGE`.
- [ ] Implement transactional `SPLIT_MARQUEE_AND_IMAGE` with deterministic ordering.
- [ ] Implement no-op evidence for KEEP_LEGACY and DEFER.
- [ ] Generate preflight/postflight SQL and reconciliation reports.
- [ ] Test missing, external, duplicate, ambiguous and multi-image cases.
- [ ] Test failure/rollback between every database mutation in a candidate conversion.
- [ ] Rehearse using a restored production backup and copied Files root.
- [ ] Perform client and web visual smoke tests.
- [ ] Preserve the reviewed manifest, journal and reports with change-control evidence.

## Acceptance Criteria

- [ ] Every 0022 candidate has exactly one reviewed disposition.
- [ ] No disposition is inferred automatically from `<img>` presence alone.
- [ ] Every resulting IMAGE Fragment references zero or one Image; a preserved optional Marquee must remain the same-Page original with unchanged ID/geometry/version (and no new unreviewed Marquee is invented).
- [ ] Every resulting MARQUEE Fragment has no Image reference.
- [ ] Multi-image legacy content creates separate ordered IMAGE Fragments when approved.
- [ ] Fragment identity, date, sequence and non-image text are preserved according to the reviewed plan.
- [ ] Missing or ambiguous files cause no speculative mutation.
- [ ] Apply is idempotent and detects stale input versions.
- [ ] Database and retained state reconcile after replay.
- [ ] Current client and web render all migrated categories without losing chronology.

## Dependencies

The 0022–0027 capability dependencies have feature-completion records, including the 0027 production rollout. Execution also requires fresh and reconciled live 0022/0024 evidence, full manual dispositions, restored rehearsal and independent production backup verification. Supplies the evidence needed by 0029 final constraint and cleanup decisions.

## Deployment and Rollback

Stop writers, take a fresh verified database backup and Files-root snapshot, validate the signed-off manifest, run dry-run, compare it with rehearsal output, then apply. Any candidate transaction failure must roll back that candidate completely and stop or clearly quarantine the batch according to the runbook.

Application rollback alone does not undo converted rows. Before destructive cleanup in 0029, database rollback is the pre-migration restore or a separately tested journal-based reverse migration. Preserve original HTML and relationship evidence regardless.
