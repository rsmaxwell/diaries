# 0054-FEAT — Step 3 default-palette toolbar layout correction

Date: 27 November 2026

## Observation

Browser acceptance screenshot shows the original Quill default palette *does* contain blues/purples, but when the colour controls are at the far right of the toolbar the palette extends beyond the available editor pane and becomes visually clipped. Narrowing the window wraps colour controls onto the next row, revealing the remaining swatches.

## Decision

Use Quill's default foreground/background swatches for all DATED, PREAMBLE and POSTAMBLE text fragments. Move the two colour pickers immediately after Bold/Italic/Underline in the shared toolbar, ahead of the font, size, and other wide controls. Do not add CSS overrides or separate per-editor toolbar settings.

## Change

- `diaries-client/src/app/fragment/quill-text-toolbar.ts`: restore `{ color: [] }` and `{ background: [] }` and move the colour controls to toolbar group 2.
- `diaries-client/src/app/fragment/quill-text-toolbar.spec.ts`: assert the shared palette configuration, control order, hyperlink availability and absence of the inline image control.
- Keep the paste/drop inline-image guard unchanged.
- This package supersedes the previous 0054 extended-colour-palette change. It can be applied whether or not that earlier ZIP was applied.

## Verification gate

Pending: Angular component tests, Chrome browser check of colour palette visibility at normal DATED split-pane width, and PREAMBLE/POSTAMBLE toolbar parity. No deployment or acceptance closure claimed.
