# 0052-DEF Step 3 — correct public Reader HTTP check targets (2026-11-23)

## Evidence reviewed

- 20261123T125536Z-consumers: all twelve SQL consumer/identity checks passed in development and production; the next probe returned HTTP 404 for `/diaries-web/diaries/1/1828/03?fragment=84`, so the Hermitage HTTP probe was not reached.
- The `diaries-web` `ProjectionSnapshot` code excludes fragments whose `pageId()` is null; `WebServer.requestedSelection` returns 404 for IDs missing from the resolved projection.
- The earlier Step 3 fingerprints show legacy Fragments 84 and 598 have null page IDs in both environments, so these are invalid public Reader targets even though their underlying content is correct.
- The Playbooks shared Nginx route proxies `/diaries-web` unchanged, and its generated web config uses `basePath: /diaries-web`.

## Correction

Retain every working read-only database assertion. Add SQL metadata-only selections for the canonical production public Reader URL based on page-owned IMAGE Fragment 2334 / Image 3 and, if a page-owned fragment exists, the July 1829 month in the same diary. Probe the Reader index and the Whitley URL with HTTP 200 assertions. Probe the July month only when a page-owned fragment exists; otherwise record NOT_APPLICABLE. Do **not** infer that July month HTTP 200 proves the Hermitage image is shown by the public Reader.

The correction does not touch the database, file store, MQTT, image catalogue, application code, or Playbooks. Browser visual acceptance and final closure remain manual.

## Verification

- `bash -n` validation of corrected script completed in the change package workspace.
- Live production and development checks have **not** been rerun against this correction.
