# 0053-DEF — Editor does not release Fragment lock when transcription is restored

## Type and status

- **Type:** Defect — Angular Editor Fragment locking.
- **Status:** OPEN / registered 24 November 2026; **implementation deferred until 0028-FEAT is completed**. No source change, deployment, or acceptance is claimed under 0053.
- **Priority:** Medium — blocks editing in another session until the owner navigates away; workaround confirmed.
- **Repository:** Diaries parent, `change-control/in-progress/0053-DEF - editor does not release fragment lock when transcription restored/`.
- **Discovered during:** `0028-FEAT` isolated Angular Editor GUI acceptance on 24 November 2026.

## Summary

When a transcription is changed, the Angular Editor obtains an exclusive Fragment lock. If the user restores the transcription to its original saved content by Ctrl+Z or by deleting the newly entered character, the lock **remains held** while the user stays on the Fragment. A second browser session still displays the Fragment as **locked by another window** and cannot edit it.

Navigating away from the Fragment and back, after restoring the original text, releases the lock. That workaround was confirmed by the owner during the same test.

This defect is **separate from 0028's legacy-image migration**. It should not block acceptance of the reviewed image conversions; do not alter 0028's migration manifest or migrated Fragment records to work around it.

## Observed behaviour — confirmed 24 November 2026

- **Environment:** Isolated Angular Editor backed by a restored-production PostgreSQL database and isolated MQTT broker/responder, used for 0028 Step 2 rehearsal. No production mutation was performed.
- **Example:** Existing **Fragment 1252** (MARQUEE/transcription), diary 3, Page ID **893**. The tested Fragment was *not* one of 0028's 71 reviewed IMAGE conversions.
- First session edits transcription; lock is acquired.
- A second independent browser session shows the Fragment as locked by another window and prevents editing.
- First session restores the exact original transcription by Ctrl+Z or deleting the inserted character; the lock is **not** promptly released while remaining on that Fragment.
- Once the first session switches to another Fragment (without saving changed text), the lock is released; returning to Fragment 1252 works normally.
- This observation does **not** establish a responder defect or an exact race sequence; the root cause still requires implementation-level tests and logs.

## Expected behaviour

- An unsaved transcription that has been returned to the last persisted content, with no other unsaved changes (including date), causes the owning Editor session to release the Fragment lock once any outstanding lock acquisition is resolved.
- The second session receives the unlocked state through retained MQTT publication and can edit the Fragment; it must not require the first session to navigate away.
- No changes to the saved transcription, date, Fragment version, Marquee, Image, or ordering are persisted simply because the user typed and undid a character.
- Locks remain held while genuine unsaved changes exist. An in-flight unlock must not clear a newer lock needed for a fresh edit.
- Unlock may be delayed by RPC latency, but must complete automatically when healthy; failures should be observable rather than silently represented as success.
- Existing Save, navigation, Cancel, date editing, session ownership, stale-lock TTL and lock-conflict protection must continue to work.

## Reproduction

1. Start the local isolated Editor (or another controlled test environment) with two **distinct sessions** using an Editor-authorised account. Confirm the same Fragment is initially unlocked. Do not use production to create test edits.
2. In session A select a non-migration transcription Fragment, e.g. **1252**, and insert one character in the text panel **without saving**.
3. Confirm the Fragment becomes locked by session A; in session B confirm it appears locked by another window and editing is blocked.
4. In session A press **Ctrl+Z** (or delete the added character) so the transcription is exactly back to its saved value and no date/other changes remain. Stay on the Fragment.
5. **Actual:** lock remains; session B still cannot edit. **Expected:** lock automatically clears, MQTT retained state updates, and session B can edit.
6. Workaround: in session A select another Fragment; confirm the original Fragment becomes unlocked, then return to it.

Repeat with slow network or artificially delayed lock/unlock RPC responses to expose races. Distinguish two sessions; ordinary tabs may share tokens/session IDs depending on how authentication was established.

## Initial technical analysis — hypotheses, not accepted root cause

Source bundle examined: `diaries-sources-20261123-082352.zip` (dated **23 November 2026**, potentially older than the authoritative Windows working copy). Reinspect actual checkout and Git status before changing code.

- `diaries-client/src/app/fragment/text-panel/text-panel.component.ts`: body change handling uses `auditTime(0)` to request a lock when `hasEdits` becomes true. Unlock-on-undo observes a `true`→`false` dirty-state transition with `distinctUntilChanged()` and `pairwise()`.
- `lockCurrentFragmentForBodyEdit()` currently checks whether the Fragment selection changed while the RPC is in flight; the frozen source does not check whether the user has already returned the body to its saved state by the time the lock reply arrives.
- `unlockCurrentFragment()` currently returns immediately unless `isLockedByMe` is already true. If an undo arrives before the owning lock is reflected in client state, the unlock may be skipped.
- Relevant paths also include `fragment-lock.service.ts`, `rpc.service.ts` and responder `LockFragment` / `UnlockFragment` handlers. Client-side timing is a **plausible** cause, not conclusively demonstrated solely by manual observations.
- The responder's unlock handler is transactional and publishes the resulting resolved Fragment state; the observed navigation workaround suggests that this path works in at least one sequence.

## Scope

**In scope:** correct lock-request/undo/unlock sequencing in the Angular Editor; preserve existing responder contract unless tests prove it needs adjustment; test MQTT retained-state convergence, two-session conflict handling, and text/date dirty-state semantics; add focused client/regression and controlled integration tests.

**Out of scope:** 0028 image migration, data conversion, new authentication roles, changing lock TTL as a workaround, bulk unlocking, editing/deleting historical diary content, and production deployment before separate verification.

## Acceptance criteria

- [ ] Typing then Ctrl+Z to the exact saved text automatically releases the lock in the same Fragment, without Save or navigation.
- [ ] Typing then manually deleting the added character behaves the same way.
- [ ] Undo **before** the lock RPC response cannot strand a lock (late-ack scenario).
- [ ] Redo/new typing while an unlock RPC is pending does not leave real edits unprotected or release another session's lock.
- [ ] Two genuinely independent sessions see correct locked/unlocked state and the second is able to edit after the first restores text.
- [ ] If body or date remains changed, the lock is retained until the appropriate save/cancel/navigation operation.
- [ ] Save and fragment switch/destroy, date-picker cancellation, failed RPCs, stale locks and lock owner/session validation continue to behave correctly.
- [ ] PostgreSQL persisted Fragment text/date/version and associated Marquee/Image remain unchanged by no-op edit/undo; MQTT retained state matches durable lock status.
- [ ] Client unit tests and build pass; integration tests exercise realistic asynchronous delays and a real isolated responder/broker; browser acceptance recorded.
- [ ] No regression to 0028 migrated IMAGE or optional-Marquee editing; production changes require normal review and deployment approval.
- [ ] Results and any rollback/deployment evidence are filed under this defect; formal closure is separately authorised.

## Evidence and references

- **Observed:** 24 November 2026 user GUI report and confirmation in the 0028 project conversation: Fragment 1252 locked after insert; Ctrl+Z/delete fails to unlock; second session displays “locked by another window”; switching away/back releases lock. This is owner-reported GUI evidence, **not** an archived screenshot or captured MQTT/Java log under 0053.
- **Related feature:** `../0028-FEAT - migrate reviewed legacy embedded-image fragments/` (0028 remains IN PROGRESS; migration testing evidence belongs to 0028).
- **0028 handoff note:** `../0028-FEAT - migrate reviewed legacy embedded-image fragments/reports/STEP2-EDITOR-UNDO-LOCK-DEFECT-HANDOFF-20261124.md`.
- **Review scope:** inspect actual Windows repo and submodule revisions before implementation. Attach console/MQTT/RPC/responder/DB evidence only after it is collected; do not invent logs or declare acceptance in advance.

## Deployment and rollback

No code or database change has been made by opening this defect. Anticipated fix is primarily client-side; validate against the matching responder MQTT contract and deployed image versions. Preserve a straightforward rollback to the preceding `diaries-client` image if a locking regression is discovered. Production deployment is not part of the current defect-registration package.

## Implementation status / closure

**NOT STARTED.** See `IMPLEMENTATION-STEPS.md`. Keep 0053 open until implementation, integrated verification and formal acceptance are complete.
