# 0051 Step 4 — Jenkins-published, protected rollout rehearsal review

**Date:** 20 November 2026 (UTC)
**Status:** PROTECTED PRE-PRODUCTION REHEARSAL PASSED; STEP 4 OPEN
**Evidence:** Windows terminal log `note(20261120-210437).txt`; retained private runtime artifacts under `evidence/Step 4/private/published-20261120T210259Z-de695753/` in the user's Windows working repository. The private runtime artifacts were not uploaded for independent examination; assertions below are the result reported by the runner, not a separate replay of that evidence.

## Released source and build identity

The Windows parent `rsmaxwell/diaries` was committed/pushed as `476b625ecfd7ee6c1a5033dbe53248c97823700d`, pinning `diaries-responder=0aa08bd2851c9615f65aabd329b8858399742d27`, `diaries-client=26ad007a5d40fcc041f610ae11e68642db16222c`, `diaries-web=f6142567d856d4c1110be93673497938276190d5`.

| Component | Jenkins image | Repository digest |
| --- | --- | --- |
| Responder | `rsmaxwell/diaries-responder:0.0.9-build-85` | `sha256:07432f88b5ae412c9c2954944144e009e3fcf004a79e915dae0324a3bd3b3686` |
| Client | `rsmaxwell/diaries-client:0.0.9-build-78` | `sha256:9109d13aff3ae48295d40bf57d02483532bddb37fac4e8d2ce7f6f92121a4a58` |
| Reader | `rsmaxwell/diaries-web:0.0.9-build-9` | `sha256:8e80e05affce6e80c3b7a2222364ca7f327ad3248d7f182f7ea3d621981fe932` |

All three Jenkins pipelines reported success; the normal Windows `local-published-smoke` subsequently reported all five containers healthy. Published-smoke currently uses shared `data/database/common` and a writable NAS Files mount, so feature-specific mutating/rollback checks ran *separately* against a protected fixture.

## Corrective history (retained, not overwritten)

Previous private rehearsal runs were blocked by (1) a Docker image ID versus repository-digest comparison; (2) a JavaScript assertion retaining the old image-ID comparison; (3) responder arguments not forwarded by `responder.sh` (required `CONFIG_FILE`); and (4) Windows bind-mounted Files failing required Linux storage capability checks. These are test-runner defects, not proven application defects. Earlier failed run receipts are historical evidence and must remain separate.

The final correction reused a fresh Docker-managed Linux Files volume for legacy and new responders, while retaining disposable PostgreSQL and MQTT. Its regression test `step4-published-files-volume.test.cjs` reported **6 passed, 0 failed** in the uploaded terminal log.

## Successful protected rehearsal

**Run ID:** `20261120T210259Z-de695753`.

The terminal log reports:

- `PASS: Existing local-published-smoke Compose resolves the three selected tags (config only; no Compose up)`
- Exact immutable published digests for all three candidate images, as in the table above
- `PASS: Published-image rollback before extension writes; re-upgrade and forward-only activation`

The feature-specific test source exercises ordinary IMAGE creation with extension writes disabled; rejection of link/IMAGE-Marquee writes without mutation; candidate and legacy client/reader entry points; old responder/reader rollback **before** the first extension write; re-upgrade; controlled extension gate activation; URL persistence and MQTT retained publication; reader link display; and owned Docker resource cleanup. The console summary reports a pass for that suite, but the underlying private JSON receipts and checksums should be retained with this run for formal review.

The rollback boundary is critical: **after the first extension write, older responder/reader binaries are not validated or approved rollback targets**. A recovery plan must not assume that older binaries can safely process the new states.

## Remaining Step 4 acceptance work

This is pre-production evidence only. The implementation plan explicitly requires supported behaviour deployed in production, migration handoff compatibility and verified production behaviour before Step 4 can be CLOSED. The following remain OPEN:

1. Read-only production baseline: actual container image references and digests, current production schema, effective extension-write gate configuration, healthy services and a verified current backup/recovery point.
2. Confirm Playbooks changes and deployment target revisions before applying configuration or migrations. Ensure the column is created by the reviewed repeatable SQL migration before launching a component that relies on it.
3. Obtain explicit owner authorisation for the controlled production rollout. Start with extension writes **disabled**; verify old-state compatibility, MQTT replay and reader/editor health. Only enable new writes after coordinated components and rollback boundary have been accepted.
4. Record production deployment, smoke, rollback/recovery decision, actual image identities and owner acceptance under this feature. Do not auto-resume 0028, delete legacy fields, or close Step 4/0051 based on this rehearsal alone.

**Conclusion:** Protected published-image pre-production gate **PASSED**. Step 4 **OPEN** pending controlled production rollout and acceptance. Steps 1–3 remain CLOSED; 0028 paused and 0029 unapproved modifications preserved.
