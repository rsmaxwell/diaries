# Step 14 workstation runbook

Run Step 14 only after the Step 13 live lifecycle is closed and its final state is understood. Step 14 is a regression/release-candidate gate; it does not replace Step 13's client/responder/MQTT/PostgreSQL/Files lifecycle verification.

## 0. Apply the Step 14 drop-in

Extract the package over the Diaries project root. No permanent application runtime script is installed by this step. All Step 14 tooling is under:

```text
change-control\in-progress\0027-FEAT - add ImageFragment editing to diaries-client\evidence\Step 14\tooling
```

## 1. Choose the disposable reader baseline backup

The 0026 browser-level reader verifier restores a PostgreSQL backup into disposable containers. It does not modify the live development or production database.

Use the validated pre-0024/0025 development baseline:

```text
data\database-backups\development-infrastructure\diaries-development-20260912-203528.dump
```

Validated SHA-256:

```text
fe0e187eda4fe4c7923590f7ec5e36871ced87e2ba8fa6d3f882e0b0992d6b86
```

This baseline is deliberately after the 0022 Fragment `page_id`/`type` migration but before the 0024 Image catalogue and 0025 Fragment-to-Image reference migrations. Do not substitute the older `diaries-production-20260908-174443.dump` (too old for the 0022 schema) or the later `diaries-development-20260929-222038.dump` (already contains an evolved Image schema that the frozen 0024 migration contract correctly rejects). Record the chosen filename/SHA in `MANUAL-EVIDENCE.md`.

## 2. Start the evidence run

From PowerShell 7 at the Diaries project root:

```powershell
$step14 = '.\change-control\in-progress\0027-FEAT - add ImageFragment editing to diaries-client\evidence\Step 14\tooling'
& "$step14\step14-begin.ps1"
$backup0024 = '.\data\database-backups\development-infrastructure\diaries-development-20260912-203528.dump'
& "$step14\step14-preflight.ps1" -ReaderBackupFile $backup0024
```

Preflight requires:

- Docker Desktop running;
- Java 25 available;
- `diaries-client/node_modules` installed;
- Chrome or Edge available for Karma/browser verification;
- the permanent integrated regression runner and its broker fixture present;
- the existing 0026 reader verification scripts present;
- `diaries-responder:local` available (or `STEP13_JAVA_IMAGE` set to another existing Java 25 runtime image);
- a real backup file for the disposable reader fixture;
- no direct-development responder process running from `diaries-responder\build\install\diaries-responder`, because the reader verifier performs a clean rebuild of that distribution.

If Playwright is not already available, restore the same browser-verification prerequisite used for 0026 before continuing. Do not weaken the Step 14 acceptance by silently skipping the reader browser run.

## 3. Run the full client/responder/reader regression

```powershell
& "$step14\step14-run-regression.ps1" `
  -ReaderBackupFile $backup0024
```

The runner first invokes the permanent disposable integrated regression gate. That gate provisions temporary PostgreSQL and Mosquitto fixtures, sets the responder integration-test URLs, runs the responder/web suites and builds with the environment-gated JPA/MQTT tests enabled, runs the complete Angular/Karma suite and production build, and performs `git diff --check`. Step 14 then checks required named JUnit contracts and separately reruns the disposable cross-component reader/browser verification against the current source candidate.

The report checker then proves the required ImageFragment/delete-guard/restart/static-URL contracts were present in the generated JUnit reports and were not skipped.

The runner also validates both local Docker Compose configurations with `config --quiet`; it does not start those mutable local stacks.

Each Step 14 evidence run is single-use for the integrated regression directory. If a regression attempt fails, preserve that run as evidence, run `step14-begin.ps1` again, and retry in the new timestamped run rather than deleting or reusing the previous `integrated-regression` directory.

## 4. Rehearse the production deployment order with authoring still disabled

The production Playbooks repository normally lives on the Ansible controller `mango` at `/home/richard/playbooks`. From the Windows Diaries project root, rehearse the **current source on mango** over SSH:

```powershell
& "$step14\step14-rollout-rehearsal.ps1" `
  -PlaybooksHost 'mango' `
  -PlaybooksRoot '/home/richard/playbooks'
```

The remote mode is read-only. It checks `roles/diaries` directly on `mango`, records the remote Playbooks Git commit/dirty state, and reads only the role source needed for the rehearsal. No Playbooks checkout is required on the Windows workstation.

A local checkout remains supported when useful:

```powershell
& "$step14\step14-rollout-rehearsal.ps1" `
  -PlaybooksRoot 'C:\path\to\playbooks'
```

In local mode, pass the directory that contains `roles\diaries`. In remote mode, pass the Unix directory that contains `roles/diaries`.

The rehearsal verifies the actual role/source currently intended for production:

1. responder configuration keeps `imageFragmentWritesEnabled=false`;
2. reader `filesPath` is production-compatible (`files` by default);
3. the production Compose template carries responder/web/client together with the explicit mutable Files mount;
4. `start.sh` validates Compose before pulling/starting;
5. configured images are pulled before `up --detach --remove-orphans --wait`;
6. in shared-frontend mode the Diaries route is activated only after application health;
7. `stop.sh` deactivates the shared route before stopping the application;
8. Step 15's later gate-enable action is not performed by Step 14.

## 5. Inspect the run summary

Print the current evidence directory:

```powershell
Get-Content '.\build\0027-step14\current-run.txt'
```

The active run is beneath:

```text
build\0027-step14\runs\<timestamp>\
```

Review at least:

```text
run-metadata.txt
preflight.txt
integrated-regression\validation-summary.json
integrated-regression\client-test.log
integrated-regression\client-build.log
integrated-regression\java-test-build.log
test-report-check.json
reader-cross-component\evidence\summary.json
compose-local-docker-build.txt
compose-local-published-smoke.txt
source-files.sha256
regression-summary.json
rollout-rehearsal.txt
```

`regression-summary.json` must say `PASSED`. `rollout-rehearsal.txt` must have no `FAIL:` lines.

## 6. Manual browser correlation back to Step 13

Step 14 does not need to repeat the entire Step 13 authoring lifecycle. Instead, record the closed Step 13 run ID and confirm its final created/edited IMAGE Fragment wire/database shape is covered by the Step 14 reader contract:

- `type=IMAGE`;
- authoritative `pageId`;
- `marqueeId` absent/null relationship;
- `imageId` null or one positive catalogue Image ID;
- date/sequence chronology normalised;
- Image relative path remains catalogue-relative, not an editor-origin absolute URL.

Use `MANUAL-EVIDENCE.md` to link the Step 13 run and Step 14 run.

## 7. Closure rule

Do not mark Step 14 complete if any of these are true:

- a required test was skipped;
- Angular production build failed;
- the disposable reader browser verification did not run;
- the reader/restart/static-file/delete-guard assertions are missing from reports;
- the current production Playbooks role was not rehearsed;
- the production responder template is already enabled;
- source changed after the captured regression without rerunning affected validation.

When the regression and rollout rehearsal are green, run the closure guard:

```powershell
& "$step14\step14-finalize.ps1"
```

It writes `step14-final-summary.json` and refuses to pass while Step 13 is still open or any required regression/rehearsal evidence is missing/failed. When that final summary is `PASSED`, update `CHECKLIST.md`, `MANUAL-EVIDENCE.md`, the feature README and `IMPLEMENTATION-STEPS.md` with the actual run ID/counts. Step 15 is then the first step allowed to perform a real production deployment/enablement action.
