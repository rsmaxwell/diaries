# Step 10 browser verification results

Date: 2026-09-29
Environment: synthetic `diaries-web` site at `http://127.0.0.1:18082`

## Month-reader checks

Route used: `/diaries/11/2026/09?fragment=33#fragment-33` (and IMAGE Fragment 35).

Observed by the user:

- Selecting IMAGE Fragment 35 removes the selected Marquee.
- **Fit selection** and **Use highlight style** become unavailable for IMAGE.
- **−**, **+** and **Fit page** remain available; this is expected because they are Page-level controls rather than region-specific controls.
- Selecting a MARQUEE Fragment restores the Marquee and region-specific controls.
- Browser Back and Forward restore the expected MARQUEE/IMAGE selection state.

## Catalogue file-load failure checks

The synthetic catalogue media host is intentionally unavailable.

Browser console observations supplied by the user:

```text
mediaFileState = FILE_LOAD_FAILED
img.hidden     = true
status text    = The image file could not be loaded.
```

This confirms the broken media element is hidden and that browser file failure remains distinct from canonical retained media state.

## Source-page checks

Route used: `/diaries/11/pages/22` with Fragment 33 (MARQUEE) and Fragment 35 (IMAGE).

Observed by the user:

- IMAGE and MARQUEE Fragment selection both work.
- The Marquee is hidden for IMAGE and shown for MARQUEE.
- Browser Back and Forward restore the expected selection.

## Evidence screenshots

- `screenshots/month-file-load-failed-status.png`
- `screenshots/month-image-selection-controls.png`
- `screenshots/source-page-type-aware-selection.png`

## Scope note

This manual smoke check records the core Step 10 completion criteria. It does not claim that every item in the original exploratory checklist (for example every Enter/Space/focus and cross-Page edge permutation) was manually repeated. Step 11 explicitly owns expanded focused projection/rendering/security/browser coverage.
