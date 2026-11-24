# 0028 — Implementation steps and acceptance gates

**Status: ACTIVE as of 21 November 2026; all acceptance steps remain OPEN.**
The owner approved formal closure of
[0051](../../complete/0051-FEAT%20-%20extend%20IMAGE%20fragments%20with%20links%20and%20optional%20marquees/README.md)
following production verification (responder `0.0.9-build-86`). 0028 Step 1
has collected evidence and partial reviews but has not passed its gate.
Resume with the read-only collection and v2 review script under `tools/`.

The planned no-Marquee IMAGE contract must be revised for supported link and
Marquee preservation before continuing these steps. No existing draft is
automatically approved by completing 0051.

This package is a **planning change**, not evidence
that a test, restore, deployment or migration has run. Prioritise one coherent
implementation and one consolidated rehearsal/test cycle; correct affected
regressions without repeating accepted expensive restores.

All artifacts, receipts and raw logs are kept **inside this feature directory**
under `reports/` and `evidence/Step N/`; one-off scripts under `tools/` or
`tests/`. Application code belongs in its own `diaries-responder` submodule;
commit that submodule separately before pinning it in the Diaries parent.

**0051 Step 4 handoff update (20 November):** The v2 private compatibility reviewer
and updated read-only inventory capture are now available for the later 0028
Step 1 review. They do **not** replace the planned Java migration engine in
Step 2, grant reviewer approval, or approve a mutation. V1 drafts are hints
only. Fresh geometry/version readback and explicit lossless link decisions
are required before any conversion can be considered.

## Step 1 — Freeze inputs, assess data, approve per-fragment decisions (OPEN)

- Verify Windows parent and each submodule branch/HEAD/status; ensure the newer
  Windows checkout and mango are not assumed synchronized. Record production
  client/responder/web build identities and authoring gate; no writes.
- Locate the historic 0022 candidate CSV and 0024 Image reconciliation output
  outside this upload if preserved. **Do not claim they were found** merely
  because utilities and design documents exist. Hash all recovered historical
  evidence. Run an updated **read-only current-schema** inventory of production
  Fragments, explicit Page/type/Marquee/Image state, locks and `<img>` sources;
  exclude ordinary pre-existing IMAGE authoring rows from legacy candidates.
- Reconcile current candidates against 0022 historic IDs; report removed,
  changed, newly discovered and duplicate/ambiguous candidates, not guess.
- Run read-only 0024 catalogue/path/checksum reconciliation, freeze expected
  Image IDs and checksums; treat suffix fallback as proposed only. Produce
  full source-to-Image exception report.
- Create and manually review *every* Fragment-level disposition and every
  embedded-image occurrence decision using the schema/contract templates.
  Approve caption/text allocation for split candidates and every null Image,
  retained HTML or deferral. Hash/sign off the final manifest. No automatic
  conversion based on `img` presence.

**Acceptance gate:** all candidates have uniquely attributable, reviewed
records and full occurrence coverage; every would-be mutation has a valid
Image/text/identity decision; no assumptions about absent inventories. Any
unreviewed row blocks `apply` (it may remain an explicit `DEFER`).

**Evidence:** `evidence/Step 1/` (input hashes, fresh inventory/reconciliation,
review ledger, decision report, approval). Retain private text in controlled
storage and commit only appropriately sanitised evidence to Git.

## Step 2 — Implement whole migration workflow and regression coverage (OPEN)

- In `diaries-responder`, implement one explicit Java CLI/task with `analyse`,
  `validate-manifest`, `dry-run`, `apply` and `postflight`. Add a strict CSV
  parser, documented schema version, row/occurrence grouping, Unicode/HTML
  source-span verification, image resolver using the existing path policy,
  and deterministic date-level sequence planner.
- Add versioned PostgreSQL journal/schema with uniqueness constraints and
  immutable review identity. Ensure rollback-safe transaction per date,
  advisory locking, checked row versions, generated ID mapping, crash-safe
  restart/idempotence and a clear failure outcome. Preserve full original
  HTML hashes/receipts; never silently rewrite unrelated text.
- Implement `CONVERT_TO_IMAGE` and `SPLIT_MARQUEE_AND_IMAGE` as authorised.
  Implement `KEEP_LEGACY` and `DEFER` as auditable no-ops. Restrict all image
  files to read-only checks; do not alter the catalogue or media bytes.
- Add preflight/postflight SQL and machine-readable per-date plan/journal and
  retained-topic reconciliation report. Do not publish MQTT inside the CLI;
  use startup/replay after commit, with explicit tombstone checks.
- Build focused JUnit and database integration fixtures, including the failure
  and negative cases in `tests/ACCEPTANCE-TEST-MATRIX.md`; run complete
  responder tests/build and relevant client/web regressions in one consolidated
  pass. Fix and rerun only affected tests as necessary.

**Acceptance gate:** full workflow compiles, plans are deterministic, all
negative scenarios fail closed, date transactions and idempotency are proven,
no image bytes/text are lost, and no writes occur during dry-run. Preserve
actual executed command/test outputs; planned commands are not evidence.

**Evidence:** `evidence/Step 2/` (code revision/diff, schema/contract results,
unit/integration logs, test fixtures and failure-injection readback).

## Step 3 — Restored-production rehearsal and controlled production apply (OPEN)

- Create a disposable isolated PostgreSQL + Files-root + MQTT environment.
  Obtain and **verify a recent production DB backup and matching Files-root
  snapshot** through the existing approved backup process; restore them and
  compare counts/file checksums. Do not restore production or prune any Btrfs
  snapshots. Rehearse exactly the reviewed manifest and tool revision.
- Run `validate-manifest` and `dry-run`; compare expected source/current rows,
  Image metadata and precise HTML/chronology/Marquee/MQTT deltas. Apply once,
  postflight, and rerun apply to prove `ALREADY_APPLIED` and zero duplicate IDs.
  Restart/replay a disposable responder and verify DB/retained topic equality;
  view converted, split, retained and deferred examples in editor and reader.
- Rehearse failure/recovery including one date failing after earlier date(s)
  committed, plus stopping between commit and MQTT replay. Record before/after
  snapshots and a tested restore/recovery procedure. Obtain explicit owner
  approval for the exact production run/manifest after rehearsal acceptance.
- For production: confirm deployment compatibility; block editing/RPC writers,
  verify no active editors, session locks or stale revisions; take **fresh**
  verified production DB + Files recovery points, record identities/hashes and
  rollback deadline. Run final strict read-only preflight. Apply **only on
  approval** using the exact reviewed plan and collect durable DB journal.
- Restart compatible responder, allow DB-to-retained replay and verify both
  new/changed topics and Marquee tombstones. After full postflight, allow
  editor/reader checks and only then reopen writers. Stop on any mismatch; do
  not report partial application as success.

**Acceptance gate:** restored rehearsal and replay pass, actual production
apply/postflight/replay passes, full reviewed coverage reconciles, two UIs
preserve all chronology and content, backups/rollback proved, and all errors
are explained. If production execution is not approved, Step 3 stays OPEN.

**Evidence:** `evidence/Step 3/` (full restore/runbook outputs, checksums,
transaction receipts, broker verification, production deployment identities,
UI smoke, rollback/recovery readback). Place private raw content in controlled
non-public evidence; use redacted summaries in portable ZIPs.

## Step 4 — Final acceptance, publication and formal closure (OPEN)

- Reconcile every 0022/0024/0028 source/decision/journal/postflight result.
  Clearly enumerate any `KEEP_LEGACY` or `DEFER` cases and document 0029
  implications. Check no original Fragment ID or unrelated chronology changed.
- Update durable responder/client/reader operating docs where behaviour was
  affected, plus an explicit migration report, final acceptance matrix,
  restoration instructions and any remaining compatibility exceptions.
- Commit/publish responder submodule implementation, pin it in parent, then
  commit parent feature evidence. Record real revisions, local modified files,
  exact deployed versions, hashes and received Git checks. Do not modify
  Playbooks or inventory unless a real, separately reviewed need appears.
- Mark a step **CLOSED only after its acceptance evidence is accepted**.
  Move `0028` from `in-progress` to `complete` **only after explicit owner
  approval of formal feature closure**. Do not close it as a side effect of
  creating this planning ZIP.

**Acceptance gate:** complete, traceable evidence and explicit closure decision;
no unresolved unacknowledged exceptions, rollback instructions remain usable.

**Evidence:** `evidence/Step 4/` (release/revision record, approval and closure
receipt) and `reports/FINAL-ACCEPTANCE-*.md` created after execution.

## Execution note: source control and test commands

Use commands in the **Windows Cygwin terminal** at the actual Windows Diaries
working copy, never in the extracted read-only bundle:

```bash
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
git branch --show-current
git rev-parse HEAD
git status --short
git submodule status
git -C diaries-responder status --short
```

After reviewing/applying this documentation ZIP via Beyond Compare 4, check:

```bash
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
git status --short
git diff --check
git diff -- 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
```

The planned `migration0028ReviewedFragments` task does **not yet exist**.
Do not run an invented migration command or any production restore/apply from
this planning document.
