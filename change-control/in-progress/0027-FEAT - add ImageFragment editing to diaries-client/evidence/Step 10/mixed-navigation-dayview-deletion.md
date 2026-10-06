# Step 10 — mixed Fragment navigation, day-view presentation and deletion

## One chronology, two visible Fragment types

The day reader still renders one ordered list and still sorts only by `Fragment.sequence`. It does not create separate MARQUEE and IMAGE sections.

Each row now exposes a compact type badge:

```text
MARQUEE  Fragment 33  Position 1
IMAGE    Fragment 84  Position 2  Image 101
IMAGE    Fragment 85  Position 3  No Image selected
```

The type label uses `effectiveFragmentType()`, so legacy/null `type` remains the documented MARQUEE fallback. IMAGE rows also show whether they currently reference a positive Image ID. This indicator is metadata only; Image bytes are not moved over MQTT.

The empty day-reader guidance has also been made type-neutral: users are now asked to select a Fragment rather than a Marquee.

## Navigation invariant

`DayviewComponent.goToFragment()` remains deliberately type-neutral:

1. set the selected Fragment ID;
2. clear Marquee selection;
3. require the Fragment's authoritative `pageId`;
4. resolve that retained Page;
5. navigate to `/diary/<diaryId>/<pageId>/<fragmentId>`.

The focused IMAGE regression uses an IMAGE Fragment with `pageId=99`, verifies `setMarqueeId(null)`, resolves Page 99, and navigates using Page 99. No Marquee is guessed for IMAGE.

## Delete Fragment is not Delete Image

The existing Delete Fragment path in `ImageViewerComponent` remains the only path used by the toolbar and Ctrl+Delete shortcut. It:

```text
lock Fragment
  -> deleteFragment(fragment.id)
  -> responder deletes Fragment/chronology aliases
  -> responder transaction clears the Fragment lock
  -> client clears Fragment + Marquee selection
  -> navigate back to owning Page
```

For an IMAGE Fragment, this path does **not** call `deleteImage` and does not delete the Image catalogue row or file. Step 10 makes that distinction explicit in two places:

- the IMAGE-reference panel visibly states that deleting the IMAGE Fragment keeps the catalogued Image and file;
- successful IMAGE Fragment deletion raises an informational message confirming that the Image/file were kept.

The generic Ctrl+Delete Fragment shortcut is no longer incorrectly gated on a selected Marquee, so it works for IMAGE Fragments too.

## Reference-aware Image deletion remains separate

`FilesListDialogComponent` continues to call the dedicated `deleteImage` RPC. A 409 conflict is now explained more precisely when the responder payload says the Image is referenced:

```text
This Image is still referenced by one or more Fragments.
Clear or delete every Fragment reference before deleting the Image.
```

The separate missing-file 409 condition keeps a different message, so the two conflict causes are not conflated in the UI.

No responder production change is needed. Existing responder code/tests already enforce the end-to-end invariant:

- `DeleteImage` maps `ImageReferencedException` to HTTP/MQTT RPC status 409;
- `ImageWiringIntegrationTest.authoringGateRejectsMutationsButPreservesLifecycle` sees 409 while an IMAGE Fragment references the Image, deletes the Fragment, verifies the Image row/file remain, then successfully deletes the now-unreferenced Image;
- the larger mixed lifecycle integration deletes two IMAGE Fragments sharing one Image and verifies deleteImage stays 409 until the final reference is removed, then succeeds and tombstones the retained Image topic.

## Step 10 scope boundary

Step 10 changes no responder production code, database schema, retained topic shape, Fragment ordering algorithm, or Image-authoring gate. It completes presentation/navigation/deletion behaviour and adds client regression coverage around the already-enforced responder reference guard.
