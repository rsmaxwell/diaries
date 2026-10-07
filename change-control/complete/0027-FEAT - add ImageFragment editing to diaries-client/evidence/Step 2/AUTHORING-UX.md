# Step 2 — Frozen ImageFragment Authoring UX

## Purpose

This record freezes the first-release `diaries-client` authoring behaviour for IMAGE Fragments before implementation starts. It is a design contract for later 0027 steps, not an implementation of the controls.

The existing MARQUEE editor must remain recognisable and unchanged while IMAGE authoring is introduced as a separate workflow.

## Existing action boundaries retained

The current page header already exposes distinct operations:

- **Add fragment with default marquee** — existing MARQUEE creation.
- **Delete selected fragment** — Fragment lifecycle operation.
- **Upload file** / **List files** — Files/Image catalogue workflow.
- Marquee create/edit/delete controls — MARQUEE-specific geometry operations.

The Files dialog also has its own **Delete Image** operation. IMAGE authoring must not redefine any of these existing actions.

## Frozen first-release actions

### 1. Add Image Fragment

**Label:** `Add Image Fragment`

**Availability:**

- client IMAGE authoring is enabled for the deployment;
- an authoritative Page is selected;
- a current Fragment/day context is selected;
- the selected Fragment belongs to the active Page/workspace context.

**Workflow:**

1. User invokes **Add Image Fragment**.
2. The client opens the existing Files dialog in a dedicated Image-selection mode rooted at the diary's Image directory.
3. Only catalogued Image entries with a positive Image ID are selectable. Directories and uncatalogued files are not valid Fragment references.
4. Browsing the chooser does **not** acquire a Fragment edit lock.
5. If the user cancels, the dialog closes and **no RPC is sent**.
6. After selection, the client revalidates the active Page and source Fragment/day context. If the context changed, creation is aborted rather than silently creating against a different context.
7. The client sends `addImageFragment` using:
   - active `pageId`;
   - source Fragment year/month/day;
   - a sequence immediately after the source Fragment in the common Fragment chronology;
   - initial text (empty string for the first release unless a later step explicitly changes this);
   - the selected positive `imageId`.
8. On success, the returned Fragment becomes selected; Marquee selection is cleared; normal retained state remains authoritative.

**Normal creation invariant:** the ordinary production creation path selects the Image *before* the create RPC, so it creates a complete IMAGE Fragment from the user's perspective.

The responder contract still allows `imageId` to be omitted/null at creation. This remains useful for compatibility/testing, but the normal first-release UI does not intentionally create an unattached IMAGE Fragment.

### 2. Select/replace Image

**Label:** `Select/replace Image`

**Availability:**

- client IMAGE authoring is enabled;
- the selected Fragment's effective type is `IMAGE`;
- the selected Fragment has an authoritative Page.

**Workflow:**

1. Open the Files dialog in the same catalogue-selection mode.
2. Do not acquire a Fragment lock while the user browses.
3. Cancellation performs no mutation and sends no update RPC.
4. If the selected catalogue Image is already attached, treat the result as a no-op.
5. Revalidate that the same IMAGE Fragment is still selected.
6. Acquire the existing Fragment edit lock.
7. Read/use the current live Fragment/version associated with that lock.
8. Send the explicit Image-reference update with a positive `imageId`.
9. Do not change Fragment text, date or sequence merely because the Image changed.
10. A successful responder update owns normal lock release semantics; failure uses the existing failed-edit unlock recovery.

### 3. Clear Image

**Label:** `Clear Image`

**Availability:**

- client IMAGE authoring is enabled;
- the selected Fragment is `IMAGE`;
- `imageId` is non-null.

**Workflow:**

1. Require an explicit confirmation explaining that the Fragment will remain but will have no selected Image.
2. Confirmation is obtained before taking the edit lock.
3. Revalidate that the same IMAGE Fragment is still selected and still has an Image reference.
4. Acquire the existing Fragment edit lock.
5. Send the explicit `updateFragment` Image mutation with `imageId: null`.
6. Do **not** delete the Image catalogue row or physical file.
7. On success, retained Fragment state displays the deliberate unattached IMAGE state.

### 4. Delete selected Fragment

The existing **Delete selected fragment** action remains the Fragment lifecycle operation for both MARQUEE and IMAGE.

For an IMAGE Fragment it deletes the Fragment only. It must not invoke Image deletion. Any Image previously referenced by the Fragment remains in the catalogue and Files tree, subject to the separate Image lifecycle rules.

### 5. Delete Image

Image deletion remains a separate catalogue operation in the Files dialog. The client does not infer that an Image should be deleted because an IMAGE Fragment was cleared or deleted.

The responder remains authoritative and rejects deletion while any Fragment still references the Image.

## Workspace presentation

For a selected IMAGE Fragment:

- keep the Page as the workspace/navigation context;
- do not synthesize or select a Marquee;
- hide/disable Marquee create/edit/delete/geometry operations as appropriate;
- retain the normal Fragment date and text editor;
- present the selected Image (when any), useful catalogue metadata, and a clear missing/unattached state;
- provide **Select/replace Image** and, when applicable, **Clear Image**.

For a selected MARQUEE Fragment, the existing workflow remains unchanged and no Image-selection action may attach an Image.

## Authoring gate behaviour

The client-side rollout control determines whether IMAGE authoring controls are made available, but it is not a security boundary. The responder's `imageFragmentWritesEnabled` gate remains authoritative.

If the client believes authoring is enabled but the responder returns 403, the client must surface that error and must not reinterpret it as a retryable transport failure.

## No implicit cross-operation side effects

The first release must not make these implicit transitions:

- Add MARQUEE -> IMAGE;
- IMAGE -> MARQUEE;
- replace/clear Image -> delete Image;
- delete IMAGE Fragment -> delete Image;
- choose Image -> alter Fragment date/text/sequence;
- browse chooser -> hold Fragment lock;
- select a raw file URL/path -> attach it as Fragment identity.
