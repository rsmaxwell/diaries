# 0025 final design decisions

## `updateFragment.imageId` semantics

The implementation chose a **type-aware extension of `updateFragment`**, not a separate `SetFragmentImage` RPC. Fragment Page and type remain server-authoritative and immutable through this RPC.

For an IMAGE Fragment:

- omitted `imageId` preserves the persisted reference;
- explicit `imageId: null` clears the reference;
- a positive `imageId` attaches/replaces with that existing Image;
- an unknown/non-positive Image ID is rejected;
- when the write gate is disabled, an actual attach/replace/clear is rejected with 403, while an explicitly echoed unchanged value is a no-op and remains allowed.

For a MARQUEE Fragment, a non-null `imageId` is rejected. Omitted or explicit-null `imageId` does not create a relationship. An IMAGE Fragment is also rejected if a Marquee exists for it.

## Attach/delete locking protocol

`UpdateFragment` owns one database transaction, locks the Fragment row `FOR UPDATE`, validates the caller-owned Fragment lock/version, and on an Image attach/replace acquires `PESSIMISTIC_READ` on the target Image row before updating the Fragment and normalising affected dates. The Fragment lock is cleared only on a successful update.

`DeleteImage` ultimately acquires `PESSIMISTIC_WRITE` on that same Image row and **rechecks** Fragment references before deleting the Image row. Because the attachment transaction holds a read lock until commit, attach-vs-delete cannot commit a dangling reference regardless of race order. The indexed `fragment.image_id` FK/check constraints provide an additional database integrity boundary.

The physical-file/database/MQTT deletion protocol remains the recoverable 0030 workflow: stage the file under the catalogue lock, commit database deletion, publish retained tombstone, then clean the staged backup. Failures retain enough state for recovery and never silently report success.

## Other deliberate deviations from the initial proposal

- `ResolvedFragmentState` replaces the former MARQUEE-specific `FragmentAndMarquee` assumption and safely represents both Fragment shapes.
- Existing 0030 recoverable Image deletion was extended with reference protection instead of adding a second deletion implementation.
- Retained Fragment payload adds `imageId`; `marqueeId` remains during compatibility and is null for IMAGE.
- `imageFragmentWritesEnabled` was added as a fail-closed authoring gate. Missing/null/false disables creation and Image-reference mutation; normal reads/replay and non-reference lifecycle operations remain available.

## Production gate state and deferred scope

Step 15 does not modify production. The 0025 responder defaults ImageFragment authoring to disabled, and production must keep the property false or absent until the reader/authoring rollout prerequisites are approved. Deferred work remains:

- 0026 — diaries-web IMAGE rendering;
- 0027 — diaries-client IMAGE creation/editing UI;
- 0028 — reviewed legacy embedded-image conversion;
- 0029 — final destructive constraints / retained-contract cleanup.
