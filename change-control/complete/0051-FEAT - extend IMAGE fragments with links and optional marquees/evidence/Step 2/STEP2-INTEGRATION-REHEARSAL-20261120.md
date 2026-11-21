# 0051 Step 2 — disposable PostgreSQL/MQTT integration rehearsal

**Prepared 20 November 2026; acceptance OPEN until owner-run fixture results are reviewed.**

## Regression result received

The owner's third Windows Cygwin responder run reported `BUILD SUCCESSFUL in 11s` for `:diaries-responder:test`. It resolved the two test compilation errors and the obsolete IMAGE/Marquee assertion. The accompanying Gradle 10 deprecation warning is non-blocking. The provided terminal excerpt does not include JUnit XML totals; retain its existing full log `evidence/Step 2/private/step2-responder-tests-third-run.log`.

## New isolated acceptance check

The feature-specific `tools/run-step2-isolated-integration.ps1` creates only two uniquely named temporary Docker containers: PostgreSQL 18 and anonymous Mosquitto, both bound to host `127.0.0.1` random ports. It restores the previously accepted **0024 frozen custom-format fixture backup** into a newly created database named `image_wiring_test`, applies the historical 0024 and 0025 additive schema migrations, then applies the 0051 migration **twice** and validates the schema.

It compares content hashes for all existing `diary`, `page`, `fragment`, `marquee` and `image` rows before and after 0051 migration (with null values excluded so adding a nullable column does not change the hash). It runs **only two opt-in PostgreSQL/MQTT tests**: the existing ImageFragment RPC/replay test and a new 0051 URL/optional-Marquee RPC integration test. The new test checks the default-disabled extension gate, successful URL creation, unsafe URL rejection without retained mutation, omitted-value preservation, IMAGE/Marquee add/edit/remove with identity preservation and retained topics, duplicate rejection, explicit URL clear and Fragment/Marquee tombstones while preserving the shared Image.

It records the original Docker/Gradle logs, schema checks, data hashes, JUnit XML, result JSON and SHA-256 evidence manifest under a unique ignored `evidence/Step 2/private/isolated-integration-<id>/` directory, then stops **only containers it created**. It does not access `pluto`, existing local environment containers or production volumes. It deliberately does not apply migration to an existing database.

## Run boundary

From **Windows PowerShell 7**, in the Windows Diaries repository, supply the local path of the previously accepted 0024 frozen fixture `.dump`:

```powershell
$feature = 'change-control/in-progress/0051-FEAT - extend IMAGE fragments with links and optional marquees'
& "$feature/tools/run-step2-isolated-integration.ps1" -BackupFile 'C:\path\to\approved-0024-fixture.dump'
```

The backup must be an existing local custom-format PostgreSQL dump, not a database URL. The tool is **not** a replacement for prior 0024 acceptance; using the same accepted fixture avoids requesting another production backup. The host requires Docker Desktop, JDK 25/Gradle build support and PowerShell 7. A missing fixture causes the script to fail before starting any container.

### Acceptance boundary

The owner-run rehearsal and JUnit XML must show no skipped or failed selected tests. Review any failure in the evidence directory before changing application code or proceeding. This package is preparation only, **not** evidence of actual integration pass; full Step 2 remains OPEN until this rehearsal plus any necessary negative/rollback follow-up has been accepted. Do not enable `imageFragmentExtensionsWritesEnabled` on production.
