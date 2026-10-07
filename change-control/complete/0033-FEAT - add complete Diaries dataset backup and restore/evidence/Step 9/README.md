# 0033-FEAT Step 9 evidence — full disposable backup/restore rehearsal

## Status

**Complete — destructive disposable runtime rehearsal passed 2026-10-07.**

Step 9 must prove the complete-dataset recovery path by destroying and restoring a **disposable** database + Files pair. It must not restore over production and must not reuse the normal shared local `common` pair as the destructive target.

The feature-only rehearsal tooling for this step lives only under this evidence directory, in accordance with 0032. Nothing in `scripts/windows` or the Playbooks live script directory is added solely for Step 9.

## Disposable target

The default rehearsal target is:

```text
logical dataset: 0033-step9-rehearsal
PostgreSQL data: ./data/database/0033-step9-rehearsal
Files selector:  files-0033-step9-rehearsal
mode:            local-docker-build
```

The harness refuses `common`, `files-development-common`, `files`, an already-existing rehearsal database/backup/restore namespace, an already-existing target Files directory, or an active normal `local-docker-build` stack. A retry may use `-ResetDisposable`, but that switch is hard-guarded so it can delete only the exact default `0033-step9-rehearsal` / `files-0033-step9-rehearsal` disposable pair.

The Docker CIFS mount and Windows host access use different credential mechanisms. Before creating the disposable Files root, the harness probes the configured NAS host through Windows SMB. If an FQDN such as `nas.localdomain` is not authenticated but its short alias `nas` is reachable with the operator's existing Windows SMB session, the harness exports the short alias only as the process-level `DIARIES_WINDOWS_NAS_HOST`. The permanent Windows backup/restore resolver uses that optional host-side alias for UNC access, while Docker Compose continues to use the committed `DIARIES_NAS_HOST=nas.localdomain`. This preserves the normal `local-docker-build` / `local-published-smoke` Compose identities and prevents writer-state collisions.

The operator's ignored `config/environments/local.env` is saved as bytes, temporarily rewritten only for the disposable database/Files selector pair, and restored byte-for-byte in `finally` after the disposable Compose stack is stopped. The process-level Windows NAS alias is also restored to its caller value. The original `local.env` SHA-256 is recorded in runtime evidence.

## Seed state

The harness takes one already-verified **complete local backup directory** as a seed source. It uses the source custom dump and Files snapshot directly to initialise the disposable target; it does not restore over the source dataset.

The seeded disposable target must contain representative state before the real rehearsal backup is accepted:

```text
at least one MARQUEE Fragment
at least one IMAGE Fragment
at least one Image referenced by multiple Fragments
multiple durable Files
at least one nested durable Files path
```

For the current workstation, the natural seed is the already-proven local complete backup:

```text
data/dataset-backups/common/20261007-105033Z
```

The harness validates the seed's schema-2 media before using it.

## Positive rehearsal

`tooling/run-disposable-rehearsal.ps1` performs the following sequence:

1. require the normal local-docker-build stack to be stopped;
2. preserve `local.env` byte-for-byte and select the dedicated disposable pair;
3. create the disposable Files root and start disposable PostgreSQL + MQTT;
4. seed PostgreSQL from the source `database/diaries.dump` and seed Files from the matching source `files/` snapshot;
5. start the full local-docker-build stack and prove representative MARQUEE/IMAGE/reuse/nested-Files state;
6. write `FINGERPRINT-BEFORE.json`, containing database counts/selected row identities plus a complete durable Files path/size/SHA-256 inventory;
7. create a **new** complete backup using the permanent `backup-dataset.ps1` engine and independently validate the completed schema-2 directory;
8. deliberately mutate both durable halves:
   - change a database Fragment version;
   - change one durable file;
   - delete a second durable file;
   - add one new durable file;
9. record `FINGERPRINT-MUTATED.json` and prove it differs from the baseline;
10. execute complete restore `preflight -> prepare -> apply -> postflight` using the permanent Step 5–7 commands;
11. inject one deliberate live Files fault before the first postflight, prove postflight fails and the responder remains stopped, then remove the fault and retry postflight successfully;
12. write `FINGERPRINT-AFTER.json` and require it to be **exactly identical** to the pre-backup fingerprint;
13. re-run restore preflight against the automatically-created safety backup to prove that backup remains valid and structurally usable;
14. verify the restored local client (`/diaries/`) and reader/web readiness endpoint return HTTP 200; Step 7 itself verifies representative retained MARQUEE + IMAGE payloads and representative `/files/...` bytes;
15. stop the disposable stack and restore the original `local.env` byte-for-byte.

`prepare` and `apply` retain their normal explicit confirmations. During the run the operator must type:

```text
RESTORE
APPLY
```

The rehearsal tooling does not bypass those safety prompts.

## Negative cases

`tooling/verify-negative-backup-cases.py` operates only on temporary copies of the completed rehearsal backup and proves rejection of:

```text
missing dump
modified dump
missing Files item
modified Files item
extra item inside backup snapshot
invalid manifest
interrupted .partial backup
```

The PowerShell harness additionally proves runtime rejection/failure semantics for:

```text
mismatched target dataset
unexpected .image-staging payload
failed postflight with writers kept stopped
```

This is the full Step 9 negative-case list from `IMPLEMENTATION-STEPS.md`.

## First runtime attempt — Windows SMB hostname mismatch

`RUNTIME-FIRST-ATTEMPT.txt` records the 2026-10-07 first rehearsal attempt. The seed database restore succeeded, but the Files seed failed before the disposable application stack was started because Windows returned error 1326 for `\\nas.localdomain\photo\...`. The harness then stopped the disposable foundation and restored the original `local.env` byte-for-byte. No normal/shared dataset was modified.

The tooling was corrected so Windows host-side access probes the configured NAS hostname and then its short alias, while the selected host is written only to the temporary rehearsal `local.env`. The guarded `-ResetDisposable` option permits cleanup of the exact incomplete Step 9 disposable pair before retry.

## Second runtime attempt — PowerShell retry-cleanup parser error

`RUNTIME-SECOND-ATTEMPT.txt` records the 2026-10-07 retry after the Windows SMB correction. PowerShell rejected the harness at parse time because the retry-cleanup message used `"$Label: $Path"`; in a double-quoted PowerShell string the colon immediately after an unbraced variable name is parsed as a scoped/drive-style variable reference. No rehearsal action ran, no disposable path was removed, and no normal/shared dataset was touched.

The harness now uses braced interpolation (`${Label}: ${Path}`), and the Step 9 static regression explicitly requires the safe form and rejects the invalid unbraced form.

## Third runtime attempt — Windows PowerShell fingerprint aggregation

`RUNTIME-THIRD-ATTEMPT.txt` records the 2026-10-07 rehearsal after the parser correction. The Windows NAS short-host fallback worked, the disposable database and all 89 Files were seeded, and the complete local-docker-build stack reached healthy state. The run then failed before creating the rehearsal backup while writing `FINGERPRINT-BEFORE.json`: Windows PowerShell 5.1 does not expose keys of `[ordered]` dictionary entries as normal properties to `Measure-Object -Property sizeBytes`, so the fingerprint byte-total expression failed. The harness cleanup stopped the disposable stack and restored `local.env` byte-for-byte.

That same run also exposed a Docker isolation concern: temporarily changing `DIARIES_NAS_HOST` caused Compose to see the normal `nas-photo` volume as having a different CIFS configuration. The corrected harness now uses a dedicated `COMPOSE_PROJECT_NAME=diaries-step9-rehearsal`, removes its rehearsal-only named volumes during cleanup, and restores the caller's original Compose project setting. The fingerprint implementation now stores file entries as `PSCustomObject` values and accumulates `totalBytes` explicitly rather than relying on `Measure-Object` over ordered dictionaries.

## Fourth runtime attempt — Docker log stderr interpreted as PowerShell failure

`RUNTIME-FOURTH-ATTEMPT.txt` records the 2026-10-07 rehearsal after the fingerprint/Compose-isolation correction. The run successfully exercised the isolated disposable environment, complete backup, all media/mismatched-target/staging negative cases, mandatory safety backup, Step-5 preparation and Step-6 database+Files apply. The deliberately injected first Step-7 postflight fault was rejected and the responder remained stopped, as required.

After removing that fault, the corrected postflight progressed through exact Files verification and Image catalogue/Files reconciliation, then started the Docker responder probe. The responder emitted a harmless `SLF4J(I)` informational startup line on container stderr. `Get-PostflightProbeLogs` captures `docker logs` output, and the existing `Invoke-Docker -CaptureOutput` path redirected native stderr with `2>&1` while `$ErrorActionPreference='Stop'`. Windows PowerShell 5.1 therefore converted the informational stderr line into a terminating `NativeCommandError` before Docker's successful exit code could be inspected.

The permanent restore helper now routes captured Docker commands through the existing `Invoke-NativeCapture` helper. Native stdout/stderr are still captured for evidence, but the Docker process exit code is authoritative. Non-zero Docker exits still fail exactly as before; harmless responder stderr no longer aborts a valid postflight. The Step 9 static regression protects this behaviour.

## Runtime evidence produced

A successful run creates a timestamped directory under this Step 9 evidence directory containing at least:

```text
REHEARSAL-TRANSCRIPT.txt
SUMMARY.json
FINGERPRINT-BEFORE.json
FINGERPRINT-MUTATED.json
FINGERPRINT-AFTER.json
local.env.original
local.env.original.sha256
negative-media/NEGATIVE-CASES.txt
```

The permanent restore state under `data/dataset-restores/0033-step9-rehearsal/` additionally records the selected rehearsal backup, mandatory safety backup, apply state, failed-postflight attempt and final accepted postflight.

The disposable database directory, Files root, completed rehearsal backup, safety backup and rollback evidence are intentionally retained after the first successful run until the evidence has been reviewed. They can be removed only after Step 9 close-out is captured.

## Static regression

`REGRESSION.txt` records the source-side checks which prove:

- the harness and negative-case helper exist only under change-control evidence/tooling;
- the required positive and negative rehearsal phases are present;
- exact before/after fingerprint equality is mandatory;
- failed postflight checks writer-stopped behaviour;
- client/reader HTTP checks and safety-backup revalidation are present;
- the existing Step 6/7 contracts remain green;
- 0032 live-script hygiene still passes.

These checks do **not** replace the destructive disposable runtime rehearsal.

## Operator command

From the Diaries repository root on Windows, after applying the Step 9 implementation ZIP and with the normal local-docker-build stack stopped:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File `
  ".\change-control\in-progress\0033-FEAT - add complete Diaries dataset backup and restore\evidence\Step 9\tooling\run-disposable-rehearsal.ps1" `
  -SourceBackup ".\data\dataset-backups\common\20261007-105033Z"
```

If a different verified complete local backup is the desired representative seed, pass that completed backup directory instead.

### Retry after an incomplete disposable attempt

If an earlier rehearsal failed before completion and left only the dedicated disposable dataset behind, rerun with the guarded cleanup switch:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File `
  ".\change-control\in-progress\0033-FEAT - add complete Diaries dataset backup and restore\evidence\Step 9\tooling\run-disposable-rehearsal.ps1" `
  -SourceBackup ".\data\dataset-backups\common\20261007-105033Z" `
  -ResetDisposable
```

From `cmd.exe`, put the same command on one line rather than using PowerShell backticks. `-ResetDisposable` refuses any dataset or Files selector other than the exact Step 9 defaults.

## Completion condition

Step 9 completion required a real run ending with:

```text
STEP 9 DISPOSABLE BACKUP/RESTORE REHEARSAL PASSED.
```

and the resulting evidence proves:

```text
pre-backup fingerprint recorded
new complete rehearsal backup independently valid
database + Files deliberately changed after backup
restore returned database exactly to baseline
restore returned Files exactly to baseline and removed post-backup extras
retained replay/static file/client-reader checks green
mandatory safety backup valid
all ten negative cases rejected/fail-safe
original local.env restored byte-for-byte
```

## Runtime attempt 5 — writer-identity collision exposed

The rehearsal `runtime-20261007-174032Z` proved the complete backup, negative cases, restore preparation, mandatory safety backup, Step-6 apply, and intentional failed-postflight guard. The corrected postflight then passed database/Files reconciliation but failed while restoring prior writer state.

The cause was the Step-9-only `COMPOSE_PROJECT_NAME=diaries-step9-rehearsal` isolation introduced after attempt 3. Because both `local-docker-build` and `local-published-smoke` expose a Compose service named `diaries-responder`, forcing both compose files into one project made writer discovery falsely report both modes as the same running service. Postflight then attempted to start a `local-published-smoke` writer that had not actually been running before restore.

The correction removes the global Compose-project override. Instead, Windows host-side Files resolution accepts the optional process-only `DIARIES_WINDOWS_NAS_HOST` alias. The rehearsal can therefore use `\\nas\...` for Windows SMB while Docker Compose continues to use the committed `DIARIES_NAS_HOST=nas.localdomain`. Normal Compose project separation and CIFS volume identity are preserved, and cleanup no longer removes normal named volumes.

Step 9 is complete. The successful end-to-end rehearsal is `runtime-20261007-182222Z`; the five preceding failed attempts remain retained as evidence of fail-safe behaviour and the tooling corrections made before acceptance.


## Successful runtime rehearsal — `runtime-20261007-182222Z`

`runtime-20261007-182222Z/REHEARSAL-TRANSCRIPT.txt` records the accepted Windows/Docker/NAS rehearsal. The run used the dedicated `0033-step9-rehearsal` dataset and `files-0033-step9-rehearsal` Files selector. Windows host-side SMB used the tested short-host alias `nas`, while Docker retained the configured `nas.localdomain` identity; writer discovery correctly reported `local-docker-build` running and `local-published-smoke` stopped.

The run proved the full Step 9 contract:

- representative MARQUEE + IMAGE state, reused Image references and nested Files were present before capture;
- complete backup `20261007-182222Z` was independently validated as schema 2 with 89 durable Files / 100032776 bytes, exact path/size/SHA-256 equality, readable SQL and valid custom dump;
- all destructive-media cases plus mismatched target, unexpected staging payload and failed postflight were rejected/fail-safe;
- mandatory safety backup `20261007-182712Z` was created from the deliberately mutated target and independently validated;
- Step 6 replaced PostgreSQL and Files, restored the exact 89-file / 100032776-byte backup state and retained rollback media;
- the injected failed postflight was rejected while the writer remained stopped;
- the corrected postflight reconciled 85 Image rows / 85 catalogue matches / 89 durable physical files with zero unexplained discrepancies, confirmed `synchronise: ok`, read representative retained MARQUEE + IMAGE payloads, verified representative `/files` bytes, and restored only the previously-running `local-docker-build` responder;
- the database+Files fingerprint after accepted restore matched the pre-backup fingerprint exactly;
- the mandatory safety backup then passed restore preflight;
- client and reader-service health returned HTTP 200;
- cleanup restored `DIARIES_WINDOWS_NAS_HOST` and `local.env`, with `local.env` verified byte-for-byte.

The terminal evidence is:

```text
STEP 9 DISPOSABLE BACKUP/RESTORE REHEARSAL PASSED.
  Rehearsal backup: ...\20261007-182222Z
  Safety backup: ...\20261007-182712Z
  Database/Files fingerprint: exact before/after match
  Client + reader-service: HTTP 200
```

## Step 9 close-out

**Step 9 is formally complete as of 2026-10-07.** The completion condition from `IMPLEMENTATION-STEPS.md` is satisfied: destructive recovery from one complete backup directory is repeatable on a disposable environment and returns both PostgreSQL and Files exactly to the captured state, with postflight application-level checks and fail-safe negative cases proven. No production restore was required for this step.
