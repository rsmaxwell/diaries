# Step 2 — Design Decisions and Rationale

## D1 — Separate IMAGE creation from the existing MARQUEE `+`

**Decision:** Keep **Add fragment with default marquee** unchanged and introduce a distinctly labelled **Add Image Fragment** action.

**Reason:** The two Fragment types have mutually exclusive relationships and different creation RPCs. A single overloaded `+` would make the resulting type and side effects less obvious and risks regressing the established MARQUEE workflow.

## D2 — Choose the Image before normal IMAGE creation

**Decision:** The ordinary editor creation path selects one catalogued Image before sending `addImageFragment`.

**Reason:** It makes normal creation complete from the user's perspective and avoids routinely creating unattached IMAGE Fragments. The responder's optional/null creation contract is retained for compatibility and controlled uses.

## D3 — Keep “Clear Image” as a supported deliberate state

**Decision:** An existing IMAGE Fragment may be cleared to `imageId=null` after confirmation.

**Reason:** The responder explicitly supports this state. It is useful for repair/replacement workflows and is semantically different from deleting either the Fragment or the Image.

## D4 — Never lock while the chooser is open

**Decision:** Open/browse/cancel the catalogue without a Fragment lock; revalidate context and acquire the lock only immediately before an Image-reference mutation.

**Reason:** Human browsing may take an arbitrary time. Holding an edit lock across the chooser would unnecessarily block another editor and increases stale-lock risk.

## D5 — Revalidate after asynchronous chooser/confirmation

**Decision:** Before creating/updating, confirm that the Page/Fragment context relevant to the operation is still the one the user started from.

**Reason:** Retained MQTT state and navigation can change while a dialog is open. Silent mutation of a newly selected Fragment would be surprising and unsafe.

## D6 — Catalogue Image ID is identity; path/URL is presentation

**Decision:** Selection returns and persists an Image ID plus useful metadata. Absolute URLs/paths are never Fragment identity.

**Reason:** This preserves the reusable Image catalogue model and keeps deployment-specific Files roots out of persisted Fragment state.

## D7 — Fragment and Image deletion remain independent

**Decision:** Deleting/clearing an IMAGE Fragment never deletes the Image. Image deletion stays in the catalogue workflow and relies on responder reference guards.

**Reason:** Images are reusable and may be referenced by multiple Fragments. Coupling deletion would violate catalogue semantics.
