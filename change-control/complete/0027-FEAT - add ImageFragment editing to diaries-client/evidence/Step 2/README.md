# 0027 Step 2 Evidence — Freeze ImageFragment authoring UX and invariants

## Outcome

**COMPLETE.** Step 2 freezes the first-release authoring UX and invariants without changing production behaviour.

## Frozen workflow

- Existing **Add fragment with default marquee** remains the MARQUEE creation action.
- New **Add Image Fragment** is a separate action.
- Normal IMAGE creation selects one reusable catalogued Image before `addImageFragment` is sent.
- **Select/replace Image** is available only for IMAGE Fragments.
- **Clear Image** is available only for IMAGE Fragments with an Image reference and requires confirmation.
- **Delete selected fragment** remains a Fragment-only operation for both types.
- **Delete Image** remains a separate catalogue operation guarded by the responder.

## Frozen lock boundary

Opening and browsing the Image chooser never holds a Fragment edit lock. For reference replacement/clear, the client revalidates the selected Fragment after the chooser/confirmation and acquires the normal Fragment lock only immediately before the explicit update.

## Evidence inventory

- `AUTHORING-UX.md` — complete action/workspace workflow.
- `INVARIANTS.md` — mandatory cross-type and persistence invariants.
- `ACTION-MATRIX.md` — state/action availability and RPC ownership.
- `DESIGN-DECISIONS.md` — rationale behind the frozen UX.
- `source-design-baseline.txt` — current source behaviours used to anchor the design.
- `input-baselines.sha256` — checksums of the source bundle and Step 1 overlay used.
- `validation.txt` — Step 2 acceptance validation.
- `changed-files.txt` — files delivered by this step.

## Implementation boundary

Step 2 intentionally introduces no Angular/Java runtime changes. Later steps must implement this frozen design rather than reinterpret it opportunistically while adding controls.
