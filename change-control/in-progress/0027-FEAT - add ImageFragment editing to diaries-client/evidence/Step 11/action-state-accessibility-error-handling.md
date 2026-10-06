# Step 11 — action state, accessibility and error handling

## Shared ImageFragment action state

`ImageFragmentActionStateService` is provided at the Fragment workspace so the header, Image-reference panel and workflow handlers consume one state source.

It derives and exposes:

```text
selectedFragmentIsImage$
selectedImageHasAttachedImage$
validAddImageFragmentContext$
addInFlight$
imageMutationInFlight$
imageAuthoringBusy$
canAddImageFragment$
canSelectOrReplaceImage$
canClearImage$
```

The two `tryBegin...()` guards are synchronous and mutually exclusive. Once Add Image Fragment, Select/replace Image or Clear Image starts, another Image authoring action is ignored until the original workflow reaches its `finally` block. This suppresses duplicate dialogs as well as duplicate MQTT RPCs.

## Deterministic controls

The Add Image Fragment toolbar control consumes `canAddImageFragment$` and `addInFlight$`. It is disabled whenever the diary/page/day context is invalid or any Image authoring workflow is active, and exposes `aria-busy` while Add is running.

The Image-reference panel consumes `canSelectOrReplaceImage$`, `canClearImage$` and `imageMutationInFlight$`. Select/replace and Clear therefore use the same state as the parent handlers and cannot drift from the mutation guards.

All new ImageFragment actions have explicit screen-reader labels and explanatory titles. A polite live status reports an Image-reference edit in progress.

## Files chooser keyboard and focus behaviour

Catalogue Image selection now makes the distinction between selectable and visible-only entries explicit:

- a catalogued Image receives an explicit `Select catalogued Image <name>` accessible label;
- an uncatalogued file remains visible but gets `aria-disabled=true` and `tabindex=-1`;
- valid selectable files support Space activation in addition to ordinary Enter/link behaviour;
- the Image chooser is opened with `autoFocus: 'first-tabbable'` and `restoreFocus: true`;
- both creation and replacement dialogs have an explicit accessible dialog label;
- Clear Image confirmation also restores focus to the invoking control.

No Fragment lock is held while the chooser or confirmation dialog is open.

## Status-specific authoring errors

`imageFragmentAuthoringErrorMessage()` centralises the new ImageFragment authoring messages.

Creation:

```text
400 -> invalid/stale page/date/sequence/Image; refresh and retry
401 -> sign-in is no longer valid; sign in again
403 -> ImageFragment authoring is disabled in this environment
409 -> conflicting edit/current data; refresh and retry
500/timeout -> creation outcome is unconfirmed; refresh before retrying
```

Image-reference mutation:

```text
400 -> Fragment/Image state stale or invalid
401 -> sign-in is no longer valid
403 -> ImageFragment authoring is disabled in this environment
409 -> Fragment locked or conflicting edit
500/timeout -> mutation outcome is unconfirmed; refresh Fragment before retrying
```

The responder's existing authorised RPC layer may also redirect to sign-in after refresh failure; the client message still distinguishes authentication from the separate 403 deployment gate.

## Retained state remains authoritative

Step 11 does not introduce optimistic Image-reference state. `mutateImageReference()` sends the explicit Step 6 mutation and waits for retained Fragment/Image publication to drive presentation. On failure it performs the existing failed-edit unlock cleanup and reports the status-specific error; it never assigns `fragment.imageId` locally.

This is especially important for 500/timeout responses because the server-side outcome may be ambiguous. The UI tells the user to refresh/reconcile rather than assuming either success or failure and retrying blindly.

## Scope boundary

Step 11 changes client action-state, accessibility, chooser keyboard/focus semantics, tests and error presentation only. It does not change:

- responder production code;
- MQTT request/reply shapes;
- Fragment/Image database schema;
- retained topic names or payloads;
- Fragment locking/version semantics;
- the `imageFragmentWritesEnabled` gate itself;
- MARQUEE creation/edit behaviour.
