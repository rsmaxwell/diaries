# 0051 Step 4 — Jenkins-published responder startup correction

**Status:** Prepared; Windows runtime rerun required. Step 4 remains OPEN.

## Observed failure and cause

- Normal Windows `scripts/windows/local-published-smoke/start.bat` completed successfully with Jenkins images (responder **0.0.9-build-85**, client **0.0.9-build-78**, web **0.0.9-build-9**); all five containers became healthy. This used the **existing shared/common** local DB and NAS Files and therefore is **not** a protected writer test.
- The separate, opt-in Step 4 **disposable published-image** run checked the same image tags and immutable registry digests, then timed out awaiting the responder MQTT RPC subscription.
- Source inspection found that the Step 4 disposable harness appended `--config /fixture/responder.json` to `docker run` *after* the published responder image name. The published `responder.sh` entrypoint ignores trailing arguments and instead forwards the environment variable `CONFIG_FILE` to Java. The responder therefore attempted to use its default `/config/diaries-responder.json`, which is absent from this disposable test container.
- The same startup issue was present in the later re-upgrade and activation responder launches.

## Correction

- Set `-e CONFIG_FILE=/fixture/responder.json` for the initial Jenkins-published candidate responder and for all subsequent candidate responder restarts.
- Set `-e CONFIG_FILE=/config/responder.json` explicitly for the historical legacy responder during the preactivation rollback segment.
- Remove redundant trailing `--config` arguments only from published responder launches; leave the accepted Step 3 direct Java/JAR harness unchanged.
- Add a focused source contract test. No application code, Jenkinsfiles, image tags, Compose modes, normal published-smoke configuration, or Playbooks have changed.

## Rehearsal scope

The published-image verification runner from `0051-step4-jenkins-published-smoke-20261120.zip` remains the supported launcher. It first validates how the normal `compose.local-published-smoke.yaml` selects the images, then starts its **disposable** fixture-based PostgreSQL/MQTT, protected synthetic Files and source pages for automated gate-disabled, old-version rollback, re-upgrade and activation checks. It does not write to `data/database/common`, does not mount NAS Files, does not redeploy `pluto`, and does not call `start.bat`/`stop.bat` on the healthy shared local stack.

**Do not** run new-feature write tests against the existing shared/common database or mutable NAS Files just because normal `start.bat` succeeded.

## Run on Windows PowerShell 7

```powershell
$repo = 'C:\Users\Richard\git\github.com\rsmaxwell\diaries-application\diaries'
Set-Location $repo
$feature = 'change-control/in-progress/0051-FEAT - extend IMAGE fragments with links and optional marquees'
$backup = Join-Path $repo 'data/database-backups/development-infrastructure/diaries-development-20260912-203528.dump'
node (Join-Path $feature 'tests/step4-published-responder-launch.test.cjs')
if ($LASTEXITCODE -ne 0) { throw 'Launch regression failed' }
& (Join-Path $feature 'tools/verify-step4-jenkins-published.ps1') `
  -ResponderTag '0.0.9-build-85' `
  -ClientTag '0.0.9-build-78' `
  -WebTag '0.0.9-build-9' `
  -BackupFile $backup `
  -RunRehearsal
```

Examine the new `evidence/Step 4/private/published-*` run. A PASS requires the actual gate-disabled, preactivation rollback, re-upgrade, extension activation, retained-state and browser checks, plus disposal/cleanup receipt. Do not equate successful image pulls or container health alone with Step 4 acceptance.

**Previous failed evidence remains valid historical evidence and is not overwritten.**
