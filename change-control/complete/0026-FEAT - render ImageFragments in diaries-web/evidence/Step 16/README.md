# Step 16 — Close out the feature and hand off to 0027/0028

## Status

**COMPLETE — 2026-10-01.**

0026 has satisfied its implementation, regression and production-deployment gates and is moved from `change-control/in-progress` to `change-control/complete`. Step 16 changes documentation/change-control state only; it does not change application runtime code, database state, retained MQTT state or production authoring configuration.

## Close-out basis

The final regression gate is Step 14. It passed the full `diaries-web` and `diaries-responder` builds/tests, all 132 Angular client tests plus production build, source-stability checks, and a fresh exact-candidate Step 13 cross-component run.

The production gate is Step 15. The exact candidate was deployed to `pluto` and verified with all five services healthy, `content.filesPath=files`, read-only `diaries/images/+` access, RPC denied for the web reader, `imageFragmentWritesEnabled=false`, the 0025 Fragment/Image schema present, zero production IMAGE Fragment rows, successful reader readiness/MARQUEE smoke checks and a successful catalogue Files-route fetch.

## Release identity

```text
Git commit: e5aa410bcf83e73f83bf81cb5aee9571ccba2755

rsmaxwell/diaries-client:0.0.9-build-74
  image ID: sha256:efe5e8b7c0a969ba0821d04a3b31cc0c83b079fd2d11a5e3c86cda2aa94ef45d
rsmaxwell/diaries-web:0.0.9-build-7
  image ID: sha256:fac8a20418d26a86bbb49bea359fbd3fba271c8aa95f0510147da382f12a6e9f
rsmaxwell/diaries-responder:0.0.9-build-82
  image ID: sha256:27d58edf958a95c7c7dcca4688bb0203fc96f23f7bda5b82fde154acb79607ba
```

Production runtime hashes after deployment are preserved in Step 15. In particular the deployed `diaries-web.json` hash is `79b6e7fe8d1b3e42f98216f639ab9291353566aac1b3a5a371df36d5b2b35460`.

## Final reader policies

### Unknown Fragment types

An absent/null type retains legacy MARQUEE compatibility. An unknown explicit non-null type is preserved as unsupported diagnostic state; it is not silently coerced to MARQUEE or IMAGE. Otherwise valid Page-owned chronology remains stable and no catalogue/Marquee relationship is invented.

### Degraded media

A Page-owned IMAGE Fragment remains in chronology when it has no Image selection, missing/rejected Image metadata, or a browser file-load failure. `NO_SELECTION`, `MISSING_METADATA`, `INVALID_METADATA` and browser-only `FILE_LOAD_FAILED` remain distinct. A file-load failure does not mutate/tombstone retained Image metadata.

### Files configuration and URL validation

`content.filesPath` defaults to `files`; production explicitly deploys `files`. Catalogue URLs are derived from browser-visible `content.publicResponderBaseUrl`, `content.filesPath`, and validated `Image.relativePath`. Real path separators are preserved and path segments are encoded exactly once. Traversal, absolute/URI-style and otherwise unsafe retained paths are rejected. Persisted absolute deployment URLs are not trusted or stored as the catalogue relationship.

### Caption and alt semantics

Caption and alt text are metadata text, never trusted HTML. Absent values are compatible as empty strings; explicit JSON null is rejected by the retained contract. `altText` is used directly as `<img alt>` and is not synthesized from caption, filename or Fragment text. Caption is escaped and rendered separately.

### Diagnostics compatibility

The final projection keeps distinct diagnostics for missing Page, unknown Fragment type, MARQUEE without Marquee, MARQUEE carrying Image state, IMAGE carrying Marquee state, IMAGE without Image selection and referenced Image metadata missing/invalid. New diagnostics did not remove the existing projection invalid-message/readiness behavior.

### Canonical-topic guardrail

The read-only web projection consumes exactly the five single-level canonical lookup families: diaries, pages, fragments, marquees and images. Image permission is `diaries/images/+`, not `diaries/images/#` or broad `diaries/#`; the web identity has no publish permission and RPC is explicitly denied.

## Deviations and deliberate boundaries

No blocking deviation from `IMAGE-READER-CONTRACT.md` remains. Production verification deliberately did not fabricate an IMAGE Fragment while authoring was disabled. Mixed IMAGE behavior was demonstrated in the controlled exact-candidate Step 13/14 environment; Step 15 verified the same published reader artifact/configuration on production using safe MARQUEE and catalogue-Files smoke paths.

0026 did not enable ImageFragment authoring and did not run legacy conversion. Those remain downstream work.

## Handoff

0027 may now treat **reader deployment/readiness** as satisfied. It must still implement and verify Angular ImageFragment editing, retain an explicit production creation gate, and make its own approved decision to enable `imageFragmentWritesEnabled`. The first production IMAGE row ends the old-reader rollback option.

0028 may now treat **reader deployment/readiness** as satisfied, but must wait for 0027/editor readiness and its own reviewed migration prerequisites. 0028 owns all reviewed legacy conversion. 0029 remains separate and owns destructive cleanup/final relationship constraints; 0026 performs none of that work.

## Evidence index

- `acceptance-matrix.md` maps every final acceptance criterion to the implementation/deployment evidence.
- `handoff.md` records the concrete 0027/0028 operational prerequisites.
- `changed-files.txt` records the Step 16 documentation/state changes.
- `source-sha256.csv` fingerprints the final close-out documents and relevant live documentation/configuration surfaces.
- `verification.txt` records the static close-out checks and preserved Step 15 checksum verification.
- `closeout.json` records the final release/deployment/handoff state in machine-readable form.
- `SHA256SUMS.txt` covers the Step 16 evidence files (except the checksum file itself).
- Steps 1–15 remain preserved unchanged beneath the feature `evidence/` directory.

## Completion decision

Another implementer/operator can reproduce the validation trail and determine the authoring state unambiguously: the 0026 reader is deployed and verified; production ImageFragment authoring remains disabled; 0027 owns authoring enablement; 0028 owns reviewed conversion. **Step 16 and feature 0026 are complete.**
