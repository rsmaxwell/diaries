# 0028 Step 1 — Improved 0051-compatible private review portal

**Status:** implementation and local synthetic tests complete; **Step 1 remains OPEN**. This is a reviewer convenience enhancement only, not an approval or migration utility.

## Scope

- `tools/step4_0051_compatibility_review.py`: retains the original `prepare`/`check` and fail-closed validator; adds an improved offline HTML reviewer.
- `tools/step1_refresh_0051_portal_offline.py`: makes a **new** HTML portal using the original sealed, checksum-verified post-0051 v2 draft. Neither existing draft nor `SHA256SUMS.txt` is modified. No network or database connection.
- `tests/test_step4_0051_portal_suggestions.py` and `tests/test_step4_0051_portal_refresh.py`: new standard-library regression tests.

## Reviewer behaviour

- Source-fact suggestions (optional, explicit click) use only verified original link/Marquee evidence. An unlinked image suggests `NOT_PRESENT`; an unambiguous safe linked image suggests `PRESERVE` with **exact decoded URL**; absent Marquee suggests `NOT_APPLICABLE`; a complete same-Page Marquee suggests `PRESERVE`. Unknown, incomplete and unsafe cases are left for human review. The *fill all* button touches **only blank** link/Marquee fields; it never fills dispositions, suffix, Page, text allocation, reviewer identity, timestamp, confirmation or deletion approvals.
- Separate *Copy historical decision and note* button fills blank disposition, matching non-operative occurrence action, and prior review note from the v1 import. Existing choices are never overwritten. These are not approvals; user must inspect each row.
- Reviewer name is reused in the current browser session only when *Record review time* is clicked. Clicking this button requires an explicit disposition, action, reviewer and reason. Timestamp is UTC ISO8601. A subsequent material decision edit clears the timestamp and v2 confirmation, requiring fresh sign-off.
- The private draft can be exported and re-imported in the enhanced portal. Import checks schema, both fingerprints, all occurrence identities, and **all immutable source evidence fields**. A mismatch is rejected. The browser does not use persistent browser storage or contact a server.
- No conversion is automatically confirmed; the server-side compatibility validator and production-apply prohibition are unchanged.

## Windows Cygwin — apply and run

Apply this ZIP **relative to the Windows Diaries repository root** using Beyond Compare 4. Before replacing the existing `step4_0051_compatibility_review.py`, inspect its diff against the new file: the supplied baseline is from `diaries-sources-20261121-111041.zip` (SHA256 `0c630a90c38016e53dc6adc60a82e39b961b823e195e4309ab555b04f2d40115`). If the working copy contains newer independent edits, **merge rather than overwrite** them. No private evidence is bundled.

Then in the **Windows PC — Cygwin** terminal:

```bash
cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries
feature='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'

python3 -m unittest discover -s "$feature/tests" -p 'test_step4_0051*.py' -v

v2="$feature/evidence/Step 1/private/20261121T122838Z-post0051-v2"
python3 "$feature/tools/step1_refresh_0051_portal_offline.py" \
    "$v2/0028-0051-review-v2.DRAFT.PRIVATE.json"

cygstart "$v2/0028-0051-review-v2.IMPROVED.PRIVATE.html"
```

The refresh helper deliberately refuses to overwrite an existing improved portal, so repeating it reports that the output exists. To keep a separate reviewed draft, use **Export PRIVATE v2 draft** in the browser; do not put the exported JSON in Git.

Do **not** rerun the read-only production inventory solely to refresh the portal. For existing work from an older v2 portal, export its draft and choose the enhanced portal's **Resume from exported PRIVATE JSON** input; the old draft must belong to exactly the same frozen evidence to import successfully.

## Local validation of the patch

- Existing 0051 compatibility tests: **12 passed**.
- New suggestion and sealed-refresh tests: **7 passed**.
- Chromium synthetic end-to-end browser test: **passed** (source suggestions, full draft export/re-import, tamper rejection, reviewer carry, timestamp invalidation, history copy, bulk suggestions; no JavaScript errors).
- No live database, MQTT, filesystem migration, production deployment or user review performed in this package.
