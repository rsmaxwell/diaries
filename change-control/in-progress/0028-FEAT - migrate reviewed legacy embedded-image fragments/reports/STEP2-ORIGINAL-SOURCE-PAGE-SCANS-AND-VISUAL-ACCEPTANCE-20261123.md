# 0028-FEAT — Original source-page scan and visual acceptance rehearsal

Date: 2026-11-23. Status: **PREPARED; real scan staging and browser acceptance pending**.

## Accepted prior evidence (do not repeat)

- Restored PostgreSQL 18 rehearsal: 71 reviewed conversions and 1 explicit DEFER; correct 71+71 migration journal entries; date-level rollback/restart/idempotence checks passed.
- Disposable MQTT replay: 71/71 converted Fragment topics and 22/22 retained Marquee topics checked.
- Isolated Reader HTTP: HTTP 200 ready; representative catalogue image resources accessible through localhost 58082 (Reader) and 58081 (responder proxy).
- Production Editor screenshot from 23 November shows the three Whitley Park map renderings are independent existing Fragments: 84 (MARQUEE), 2334 (IMAGE, caption `Testing one two three`), and 2332 (IMAGE, caption `hello`). They must **all be retained**; no migration duplicate repair is needed.

## Why the left-hand source scan was missing

The isolated responder had only the independently copied `files-root` (catalogue files). The Reader constructs original page-image URLs from the Page and Diary names, under `/diaries/<diary>/<page>.<extension>` at the responder HTTP base. Those original scans were intentionally not staged. This is an incomplete test fixture, not a failed conversion.

## New non-production acceptance step

Windows PC — **Cygwin** in Diaries parent repo:

```bash
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
export DIARIES_0028_SOURCE_DIARIES_ROOT='/cygdrive/p/nancy-and-ronald-maxwell/documents/sea-captains-chest/diaries-content/diaries'
bash 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tools/verify-0028-step2-source-scans.sh'
```

The script verifies the isolated DB, journal, Docker labels and both bridges, then gathers distinct Page metadata for the 71 converted Fragments and the screenshot example Fragments 65 (img2839) and 84 (img2840). It copies **only** those original scans from the NAS into **ignored private Step 2 evidence**, verifying SHA-256 from the source twice and verifying every independent copy. It does not alter NAS originals. A labelled isolated Nginx sidecar serves these files from a **read-only bind mount**, with no host-published port. The existing labelled localhost HTTP proxy is the **only** disposable container replaced, to add a `/diaries/*` read-only route; existing DB, broker, responder and Reader remain running and untouched.

Automated HTTP checks require success for every staged source page; full-byte HTTP SHA-256 checks are performed for `img2839` and `img2840`. The script also checks Reader readiness and unchanged journal and Marquee DB fingerprints. No fresh production dump, image registry write, new MQTT replay or changes to existing development services occur. An isolated failed step must not be interpreted as a production failure.

If source files cannot be found on the mapped NAS, the script **fails before changing the HTTP proxy**; set `DIARIES_0028_SOURCE_DIARIES_ROOT` to the correct mounted `diaries` directory. If the browser still displays an error after script PASS, capture Edge Network/Console evidence, because the static HTTP checks do not prove SVG image loading or script execution.

## Browser acceptance — user-observed, not automatable from HTTP status alone

Open the isolated Reader on `http://127.0.0.1:58082/diaries/1/1828/03?fragment=84#fragment-84` and inspect:

- Original source panel for `img2839` or `img2840` should show a legible diary scan rather than `The source image could not be loaded`.
- Selecting a Fragment highlights the correct Marquee without shifting its currently improved geometry.
- The Whitley Park historical map and three distinct existing Fragment captions/positions are as in the production Editor reference; the migrated text/image chronology remains intact.
- `Open image directly` and `Show on source page` lead to working content; check a Fragment with an existing hyperlink, and verify no accidental navigation to untrusted links.
- Browse a few days before and after Thursday 20 March 1828, checking image display, text order, pan/zoom and page selection.

Save screenshots/browser diagnostics privately under `evidence/Step 2/private/` and record which checks passed or failed. **Do not declare full visual acceptance without the owner's observation.**

## Editor acceptance remains separate

The production Editor screenshot is strong baseline evidence about the *source data*; it is **not** a test of the Angular Editor against the migrated isolated database. Do not point the normal production or development Editor at the isolated MQTT broker, and do not expose a writable broker/websocket path simply for visual testing. An isolated Editor test requires an independently configured, safely constrained browser MQTT endpoint and authentication; preserve the existing isolated migration journal and production services.

Formal Step 1 owner approval, final Editor GUI evidence, deployment change control and production apply remain **OPEN**. No production migration is authorised.
