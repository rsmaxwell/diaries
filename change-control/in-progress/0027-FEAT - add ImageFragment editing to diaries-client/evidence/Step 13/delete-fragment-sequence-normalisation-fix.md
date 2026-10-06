# Step 13 integration correction — normalise Fragment sequence after delete

## Live finding

Phase A deleted disposable IMAGE Fragment `2332` after exercising mixed MARQUEE/IMAGE drag-and-drop ordering. The delete itself correctly removed only the Fragment and preserved the reusable Image catalogue entry/file. When the responder was subsequently restarted for the gate-enabled phase, startup normalisation adjusted the sequence numbers of the surviving Fragments after the deleted position. That showed that `deleteFragment` had committed a chronology gap and startup synchronisation was repairing it later.

The defect is type-neutral: deleting any Fragment from the middle of one date can leave later Fragments with non-contiguous sequence numbers.

## Root cause

`UpdateFragment` already calls `FragmentSequenceNormaliser.normaliseAffectedDates(...)` in the same transaction as date/sequence updates. `DeleteFragment` deleted the Marquee (when present) and Fragment, committed immediately, then only tombstoned the deleted retained topics. It did not normalise the surviving date or republish any survivors whose sequence/version changed.

## Correction

`DeleteFragment` now:

1. deletes the Marquee (if present) and Fragment inside its existing owned transaction;
2. calls `FragmentSequenceNormaliser.normaliseDate(...)` for the deleted Fragment's date before commit;
3. rolls the whole transaction back if normalisation detects a version conflict;
4. after commit, tombstones the deleted Marquee/Fragment retained topics as before; and
5. republishes every surviving Fragment whose sequence/version was changed by normalisation, using the existing `FragmentSequenceNormaliser.publish(...)` helper so canonical and date retained topics stay aligned.

The reusable Image lifecycle remains separate: deleting an IMAGE Fragment still does not write or delete the Image catalogue row or file.

## Regression coverage

`FragmentLifecycleContractTest.deletingMiddleImageFragmentNormalisesAndPublishesSurvivingChronology()` models the live shape directly:

- MARQUEE `4` sequence 1
- MARQUEE `5` sequence 2
- IMAGE `2332` sequence 3
- MARQUEE `1` sequence 4
- MARQUEE `2` sequence 5
- MARQUEE `3` sequence 6

After deleting `2332`, the test requires survivors `1`, `2`, `3` to become sequences `3`, `4`, `5`, with their versions incremented and both canonical/date retained topics republished. Fragments `4` and `5` remain unchanged, the deleted Fragment topics are tombstoned, and the Image retained object is untouched.

## Validation status

The package environment could not run Gradle because its wrapper distribution was unavailable, so validation was completed on the development workstation. The focused command:

```powershell
.\gradlew.bat :diaries-responder:test `
  --tests com.rsmaxwell.diaries.responder.handlers.FragmentLifecycleContractTest `
  --no-daemon
```

completed `BUILD SUCCESSFUL in 5s`. The broader create/delete focused suite was also green. Live deletion of Fragment `2334`, followed later by Phase B Fragment `2333`, left the affected day immediately contiguous without responder restart while preserving Image lifecycle separation. Final status: **PASS**.
