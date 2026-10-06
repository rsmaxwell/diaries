# Step 9 — Type-neutral text/date/sequence editing and locking

## Ordinary IMAGE text/date editing

`TextPanelComponent` deliberately remains a generic Fragment editor. An explicit IMAGE Fragment uses the same text/date UI and the same Fragment lock as a MARQUEE Fragment.

The save path remains:

```text
edit body/date
  -> acquire normal Fragment lock
  -> build full Fragment payload using current version/date/text
  -> RpcService.updateFragment$()
  -> UpdateFragmentRequest.fromFragment()
  -> imageId omitted from MQTT args
  -> responder preserves existing Image reference
  -> responder clears lock on success
  -> retained Fragment state becomes authoritative
```

The explicit `updateImageFragment$()` API introduced in Step 6 is not called by `TextPanelComponent`.

Focused regression coverage now checks both body and date changes on `type: IMAGE`, including positive `imageId` preservation and the absence of `imageId` from the ordinary wire request.

## Lock acquisition, cancellation and navigation

The existing body/date lock lifecycle applies to both Fragment types:

- body editing acquires the normal Fragment lock;
- opening the date picker acquires the same lock;
- closing the date picker without a change releases it;
- a failed save invokes the failed-edit unlock path;
- a lock which completes after selection has moved to another Fragment is immediately released.

Step 9 adds a destruction guard as well. If the editor is destroyed while a body/date lock RPC is still in flight, a successful late lock is released rather than applied to an editor which no longer exists.

## Save completion race fix

Verification found an existing cross-selection race independent of Fragment type.

Before Step 9:

```text
save Fragment A
  -> user selects Fragment B before A's update returns
  -> A success callback called markFragmentUnlocked() on current Fragment B
     OR
  -> A error callback restored prevFragment A into the editor
```

The save is now bound to `savedFragmentId`:

```text
save Fragment A
  -> remember saveFragmentIdInFlight = A
  -> selection/destroy does not race A's update with a separate unlock
  -> success:
       responder clears A's lock atomically
       local unlock mirror runs only if A is still selected
  -> failure:
       rollback UI only if A is still selected
       unlockFragmentAfterFailedEdit(A) regardless of current selection
```

This prevents a late A completion from modifying or unlocking B.

## Mixed sequence ordering

`DayviewComponent.drop()` remains type-neutral. It clones the moved Fragment, acquires the same Fragment lock, sends the ordinary `updateFragment$()` request and leaves responder normalisation authoritative.

Step 9 regression coverage now exercises a mixed chronology containing:

```text
MARQUEE
IMAGE imageId=101
IMAGE imageId=202
```

After an IMAGE reorder, the test injects the retained normalised result and verifies that the day view consumes the authoritative sequence/version values while both Image references remain unchanged. The temporary reorder wire request still omits `imageId`.

## MARQUEE-only operations

The existing page-header regression remains in force: explicit IMAGE selection disables all MARQUEE editing controls. Step 9 does not weaken that boundary.

## Responder authoring gate

The responder already contains two relevant regression layers:

1. `UpdateFragmentImageTest.disabledGateAllowsPreservationButRejectsAttachReplaceAndClear` proves omitted/same `imageId` preservation is allowed while attach/replace/clear mutations are rejected with 403 when the gate is disabled.
2. `ImageWiringIntegrationTest.authoringGateRejectsMutationsButPreservesLifecycle` runs the live RPC lifecycle with `imageFragmentWritesEnabled=false`, performs an ordinary IMAGE `updateFragment` with `imageId` omitted, and verifies the existing Image reference is retained.

The normal UpdateFragment handler copies the persisted Image ID into the incoming row before applying optional Image-selection semantics, normalises affected dates in the same transaction, reloads committed state, and publishes the normalised Fragments. Existing integration assertions compare retained version/Image fields with the persisted DTO.

## Step 9 scope boundary

Step 9 does not add new Image-reference authoring controls or responder behaviour. Image attach/replace/clear remains Step 8's explicit path. Day-view type presentation and complete mixed navigation/deletion UX remain Step 10 work.
