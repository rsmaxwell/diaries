# 0053-DEF — Implementation steps

**Status:** IN PROGRESS / development correction built and GUI-verified 25 November 2026. Created 24 November 2026. No step is formally CLOSED; direct DB/retained-topic evidence, final Git review and deployment/closure disposition are outstanding.

Proceed with a single coherent fix and consolidated validation rather than repeating intermediate gates unnecessarily.

## Step 1 — Confirm baseline and reproduce the ordinary logic defect (and races)

- On **Windows PC, Cygwin**, record parent repository branch/revision/status, `.gitmodules`, submodule status, and `diaries-client` working changes. Compare against the 23 November source bundle; do not overwrite later local work.
- In a disposable Editor/responder/MQTT environment, reproduce Ctrl+Z and manual delete back to saved text on a safe transcription Fragment with two independent sessions.
- Capture timestamped console, outgoing `lockFragment`/`unlockFragment` RPC and response correlation, retained Fragment lock messages, responder logs and read-only PostgreSQL lock values. Avoid real credentials, tokens and private diary text in versioned evidence.
- First investigate **normal-speed** edit/undo: compare current and baseline serialized HTML, Quill Delta operations, `hasEdits`, Save enabled state and lock RPC counts without recording private transcription text. Then vary RPC ordering so a lock acknowledgment arrives **after** the undo; distinguish normal logic gap from a race.
- Compare authenticated session IDs between windows, especially a browser-duplicated tab versus two independent sign-ins. Confirm the second window is read-only and labeled as another window.
- **Acceptance:** root cause demonstrated in code and repeatable test. Document any limits rather than assuming the earlier hypothesis was proven.

## Step 2 — Implement the complete lock-state correction

- Treat the saved transcription **and date** as the edit baseline; release only when neither has unsaved changes.
- Reconcile lock request, successful/failed reply, unlock request and new editing epochs per Fragment. A late lock success after returning to baseline should release the newly acquired lock; an older pending unlock must not defeat a newer edit.
- Preserve Fragment identity and session ownership; do not unlock an unrelated Fragment when navigation or destruction races an RPC.
- Ensure error handling and retry/feedback cannot silently strand the lock. Avoid changing responder contract unless evidence requires it.
- Preserve existing behaviour on Save, failed Save, fragment-switch, Cancel/destroy and date picker.
- **Acceptance:** change is minimal but handles normal undo/delete, rapid undo and re-edit races as one integrated workflow.

## Step 3 — Consolidated regression and integration verification

- Add focused Angular tests for slow lock ACK, undo before ACK, undo after ACK, manual deletion, date edits, re-edit during pending unlock, concurrent session conflict and fragment change/destroy.
- Run `diaries-client` test and production build using the repository-supported commands. Run impacted responder tests only if responder code/contract changes.
- Validate with a disposable PostgreSQL/MQTT/responder setup using two independently authenticated sessions; check no unintended persistence, lock owner/session, retained-topic publication and cross-session unlock visibility.
- Recheck representative ordinary MARQUEE and optional-Marquee IMAGE Fragments; do not modify 0028's 71 reviewed source Fragments in production.
- Verify full application regression once rather than rerunning the already accepted 0028 migration rehearsal.
- **Acceptance:** all relevant tests, manual GUI checks, and datastore/topic-tree consistency PASS; record build/log identities and any failures.

## Step 4 — Handoff, deployment and closure

- Produce a small `diaries-client` submodule change ZIP plus separate Diaries parent change-control docs ZIP as needed, preserving unrelated Git work.
- Record version/image tags, rollback instructions, and deployment proof only when deployment actually happens. Production deployment is separately controlled.
- Update feature reports and user documentation only if behaviour/instructions change.
- Mark a step CLOSED only when its criteria and evidence are accepted. Move `0053-DEF` to `change-control/complete/` **only after formal defect closure**.

## Execution and gate record — 25 November 2026

- **Step 1 — substantial evidence collected, not formally closed.** Normal-speed manual reproduction was reported on Fragment 85 (diary 1, page 692). The exact raw Quill representation and RPC timing were not captured; the HTML-comparison gap and copied session ID were identified by code investigation, supported by successful corrective GUI testing. Windows Git/submodule status is archived in the handoff report.
- **Step 2 — implementation complete, awaiting formal acceptance.** Client changes cover canonical Quill comparisons, lock/unlock sequencing, per-window session distinction, button state; no responder change. Test-fixture correction is a separate one-file ZIP.
- **Step 3 — principal checks PASS, remaining evidence gaps.** `npm run build` PASS; ChromeHeadless 248/248 PASS; six-window-scenario checks 6/6 PASS (owner-reported). Direct PostgreSQL version/no-op validation, raw MQTT retained-topic capture and responder-log checks have not been supplied. Do not misrepresent these as passed.
- **Step 4 — documentation handoff prepared, NOT CLOSED.** The client has not been committed/deployed to production in the evidence available. Record commit hashes/image tag, production smoke checks, rollback option and any required formal approval before closure.

Evidence: `reports/LOCAL-VERIFICATION-HANDOFF-20261125.md` and `evidence/windows-verification/`. Original failed run is retained alongside the corrected passing run.
