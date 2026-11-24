# 0053-DEF — Implementation steps

**Status:** REGISTERED / implementation deferred until 0028-FEAT completes. Created 24 November 2026. None of these steps are CLOSED.

Proceed with a single coherent fix and consolidated validation rather than repeating intermediate gates unnecessarily.

## Step 1 — Confirm baseline and reproduce the race

- On **Windows PC, Cygwin**, record parent repository branch/revision/status, `.gitmodules`, submodule status, and `diaries-client` working changes. Compare against the 23 November source bundle; do not overwrite later local work.
- In a disposable Editor/responder/MQTT environment, reproduce Ctrl+Z and manual delete back to saved text on a safe transcription Fragment with two independent sessions.
- Capture timestamped console, outgoing `lockFragment`/`unlockFragment` RPC and response correlation, retained Fragment lock messages, responder logs and read-only PostgreSQL lock values. Avoid real credentials, tokens and private diary text in versioned evidence.
- Vary RPC ordering so a lock acknowledgment arrives **after** the user has undone the edit; verify whether undo was missed, an unlock was skipped, or retained state was stale.
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
