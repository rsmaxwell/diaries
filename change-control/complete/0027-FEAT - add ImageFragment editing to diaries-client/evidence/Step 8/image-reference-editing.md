# Step 8 — ImageFragment Image-reference editing

## Implemented workspace behaviour

A selected valid IMAGE Fragment now displays a dedicated Image-reference panel above the existing GoldenLayout editor. The panel is absent for MARQUEE/legacy-MARQUEE Fragments.

For a resolved Image the panel shows:

- Image database ID;
- catalogue `relativePath`;
- original filename;
- caption and alt text when present;
- a preview URL derived from runtime responder base URL + configured Files root + retained `relativePath`.

If the Fragment has a positive `imageId` but retained `diaries/images/<id>` metadata is absent/tombstoned, the panel deliberately shows **Image reference unresolved**. The Fragment reference is not silently cleared and **Select/replace Image** remains available for repair.

## Select/replace workflow

```text
Select/replace Image
  -> snapshot selected IMAGE Fragment/Page/Diary
  -> open Files dialog in catalogue-image mode
  -> NO Fragment lock while browsing
  -> cancel: stop, no lock, no RPC
  -> reject non-positive/non-catalogued Image ID
  -> revalidate same Fragment/Page/Diary
  -> same imageId: stop, no lock, no RPC
  -> lockFragment
  -> wait for newly retained locked Fragment state
  -> recheck selected Fragment identity/type
  -> if retained imageId already equals requested imageId:
       release otherwise-unused lock; no update RPC
  -> updateImageFragment$(latestFragment, positive imageId)
  -> success: no extra unlock; wait for retained state
  -> failure: unlockFragmentAfterFailedEdit
```

The post-lock retained-state wait requires a lock timestamp different from the pre-lock snapshot and has a five-second timeout. This prevents a stale pre-lock replay from being used as the authoritative update version/field set.

## Clear workflow

```text
Clear Image
  -> require selected IMAGE Fragment with positive imageId
  -> confirmation explains Fragment remains and Image remains catalogued
  -> NO Fragment lock while confirmation is open
  -> cancel: stop, no lock, no RPC
  -> revalidate same Fragment and same current imageId
  -> lockFragment
  -> same post-lock retained-state refresh as replacement
  -> updateImageFragment$(latestFragment, null)
  -> success: no extra unlock; retained state shows unattached IMAGE
  -> failure: unlockFragmentAfterFailedEdit
```

Clear does not call `deleteImage` and does not remove the catalogue row or physical file.

## Concurrency and authority

The client does not optimistically write `Fragment.imageId` or Image metadata after a successful update. The responder remains authoritative for lock ownership, optimistic version validation, authoring gate state and Image existence, and retained Fragment/Image topics drive the visible result.

The responder contract inspected for this step confirms:

- `requireLockedByCaller` runs before update;
- incoming version is checked/incremented before Image selection is applied;
- omitted `imageId` still means preserve;
- successful update clears the lock before save/publication;
- stale/invalid/wrong-owner mutations are rejected rather than overwriting state.
