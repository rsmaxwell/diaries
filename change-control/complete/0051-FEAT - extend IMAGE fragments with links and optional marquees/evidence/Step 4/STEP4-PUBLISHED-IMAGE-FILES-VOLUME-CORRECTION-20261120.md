# 0051 Step 4 — Protected published-image upload volume correction

**Status:** Corrective package prepared. Full Windows runtime rehearsal NOT yet passed. Step 4 remains OPEN.

## Evidence and cause

The published-image Step 4 run `published-20261120T205752Z-9ec96191` verified all three Jenkins image repository digests and passed responder MQTT readiness after the preceding `CONFIG_FILE` correction. It then failed the first upload RPC with status 500 and the sanitised responder message `Upload storage capabilities or permissions unavailable.`

In `UploadFile.handleRequest`, the responder calls `ImageCatalogueService.verifyStorageCapabilities()` before staging any bytes. That capability probe requires an owner-only `.image-staging` directory, filesystem locks, hard links and atomic rename. The published-image disposable harness had switched from the Step 3 container-local Linux filesystem to `type=bind` from the Windows host for `/data/files`. That bind mount can lack required POSIX permissions/capabilities and is not an acceptable equivalence for the intended Linux upload filesystem. The outward RPC error is deliberately generic; the precise failing sub-check was not logged, so the Windows bind mount is diagnosed as the *likely* root cause rather than a proved specific primitive failure.

## Change

- Run Step 4 with a **unique Docker-managed local Linux volume** for `/data/files`, created only for that run. This volume is never a NAS mount or shared local dataset.
- Run a disposable preflight in the exact Jenkins responder image to make `.image-staging` owner-only (`0700`) and check local filesystem hard links and a move before the first RPC.
- Reuse that volume across candidate → legacy → candidate responder changes, keeping the uploaded synthetic image available during pre-activation rollback.
- Remove the volume **after** removing owned containers, even when the rehearsal fails; record cleanup status and fail if volume removal fails.
- The accepted Step 3 direct-JAR path, normal Windows `local-published-smoke`, three published Docker images, Playbooks and production remain untouched. No new database restore or new client/responder/web build is required.

## Rerun on Windows PowerShell 7

```powershell
$repo = 'C:\Users\Richard\git\github.com\rsmaxwell\diaries-application\diaries'
Set-Location $repo
$feature = 'change-control/in-progress/0051-FEAT - extend IMAGE fragments with links and optional marquees'
$backup = Join-Path $repo 'data/database-backups/development-infrastructure/diaries-development-20260912-203528.dump'
node (Join-Path $feature 'tests/step4-published-files-volume.test.cjs')
if ($LASTEXITCODE -ne 0) { throw 'Step 4 Linux Files volume regression failed' }
& (Join-Path $feature 'tools/verify-step4-jenkins-published.ps1') `
  -ResponderTag '0.0.9-build-85' `
  -ClientTag '0.0.9-build-78' `
  -WebTag '0.0.9-build-9' `
  -BackupFile $backup `
  -RunRehearsal
```

Retain prior failed receipts unchanged under `evidence/Step 4/private/`. The new receipt should include `step4-files-volume.json`, `step4-files-preflight.txt`, `cleanup.json` (`filesVolumeRemoved: true`), and final `step4-rollout-receipt.json` showing no old binary started after extension activation. Until that passes, the gate is OPEN and no production deployment is authorised.
