# 0051 Step 4 — Jenkins publication and published-image verification

**Status:** Implementation prepared; publication and runtime rehearsal **NOT EXECUTED**. The owner chose the established Jenkins-on-`pluto` publication path and Windows `local-published-smoke` image selection in place of local candidate image builds. Step 4 remains OPEN.

## Baselines and source-control constraints

- Latest supplied Windows source snapshot: `diaries-sources-20261120-152822.zip` (20 November 2026, 15:28); Step 4 packages were subsequently applied in the Windows checkout, so do not assume this historical bundle is a verbatim current checkout.
- The bundled Jenkinsfiles for client and responder check out `https://github.com/rsmaxwell/diaries.git` at `main` with pinned recursive submodules. The user's documented parent checkout is `rsmaxwell/diaries-application`. **Verify the actual Jenkins checkout URL/ref and actual Git remotes before publication.** Do not assume the URLs are equivalent.
- Check that each changed application submodule (responder, client, web) is committed/pushed, and that the parent superproject pins the intended commits and is pushed to the branch Jenkins actually checks out. No script in this package commits, pushes, invokes Jenkins, or changes Playbooks.
- Do not mix unapproved 0028 review decisions into the feature commit. Preserve uncommitted 0028/0029 work. Never use `git add -A` indiscriminately in the parent repo.
- Jenkins image tags and repository digests **do not exist yet for this feature in the supplied evidence**. Do not invent tags or claim images published. Record Jenkins jobs/build numbers, image tags, per-platform digests, Git revisions and DockerHub receipt once available.

## Published image selection and verification

`tools/verify-step4-jenkins-published.ps1` accepts the **actual published image tags** for responder, client and web. It uses the original `compose.local-published-smoke.yaml` plus the mode and local environment files to check the exact three selected image names with `docker compose config --images` (config only), then pulls those same published images. It records both local Docker IDs and immutable repository digests and pins the test run to the digests. The old images are pinned to the measured pre-0051 `pluto` repository digests.

This script never calls `docker compose up/down` for the normal `local-published-smoke` stack because that stack mounts NAS Files writable and uses `data/database/local-published-smoke`. Instead, its opt-in `-RunRehearsal` exercises the *published image artifacts* through the previously accepted **disposable** 0051 PostgreSQL/MQTT/browser harness. The ordinary published-smoke mode is left untouched. This is an isolated, published-image rehearsal, **not** proof that normal Compose was started.

## Test boundary and rollback

1. Candidate images start with `imageFragmentWritesEnabled=true`, `imageFragmentExtensionsWritesEnabled=false` on the disposable fixture. Ordinary IMAGE/MARQUEE operations remain permitted; extension-specific writes reject without mutation.
2. Before any new-format write, restart the pinned old responder/web/client against the compatible fixture and verify old writer and reader operations.
3. Re-upgrade to the pinned published candidate images with extensions still disabled. Then enable extensions and verify URL persistence and retained state.
4. **Do not restart older responders after a new IMAGE URL or IMAGE+Marquee has been committed.** The older binary may not understand the new retained-state semantics. This rehearsal deliberately stops at that boundary.
5. Preserve the PostgreSQL additive schema, published-image identities, cleanup receipts and historical failures. It does not perform an 0028 production migration.

## Production gate (not approved)

- The Jenkins build outputs must be traced to the exact intended Git and submodule revisions. Resolve any Jenkins checkout URL discrepancy before pushing/building.
- After isolated published-image rehearsal passes, review selected tags in the real `local-published-smoke` environment. Starting the *normal* mode is a separate decision because it uses a persistent database and a writable NAS Files mount; do not use it for mutating rollback tests without an isolated override. Preserve the accepted disposable smoke evidence rather than repeating it.
- Verify and separately approve any coordinated production deployment and feature-gate activation. Step 4 is not closed merely by image publication.

## Commands (Windows PowerShell 7)

```powershell
$repo = 'C:\Users\Richard\git\github.com\rsmaxwell\diaries-application\diaries'
Set-Location $repo
$feature = 'change-control/in-progress/0051-FEAT - extend IMAGE fragments with links and optional marquees'
& (Join-Path $repo "$feature/tools/verify-step4-jenkins-source.ps1")

# AFTER Jenkins has published the three new builds (replace placeholders with real tags):
# & (Join-Path $repo "$feature/tools/verify-step4-jenkins-published.ps1") `
#    -ResponderTag 'ACTUAL-RESPONDER-TAG' -ClientTag 'ACTUAL-CLIENT-TAG' -WebTag 'ACTUAL-WEB-TAG'
# Then run again with -RunRehearsal -BackupFile pointing to the approved 0024 fixture.
```

All logs and manifests belong in `evidence/Step 4/private/`. No application image is built locally by this package.
