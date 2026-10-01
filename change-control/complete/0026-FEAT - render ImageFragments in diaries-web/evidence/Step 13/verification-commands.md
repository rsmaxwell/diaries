# Step 13 verification commands

Run from the top-level `diaries` directory in PowerShell 7.

Choose a recent development database backup and a new output directory. The backup may be a
custom-format pg_dump or plain SQL dump; it is copied into a disposable PostgreSQL container
and never restored over the live development database.

Example:

```powershell
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'

.\scripts\windows\validation\verify-0026-step13.ps1 `
  -BackupFile .\data\database-backups\development-infrastructure\diaries-development-20260929.dump `
  -EvidenceDirectory ".\diaries-web\build\step13-$stamp"
```

If Chrome/Edge or Python need explicit selection (`CHROME_BIN` is also honoured):

```powershell
.\scripts\windows\validation\verify-0026-step13.ps1 `
  -BackupFile <backup> `
  -EvidenceDirectory <new-directory> `
  -ChromeBin 'C:\Program Files\Google\Chrome\Application\chrome.exe' `
  -Python python
```

The default Java 25 fixture image is `diaries-responder:local`. To use another image only as
the Java runtime:

```powershell
$env:STEP13_JAVA_IMAGE = '<java-25-image>'
```

The runner mounts the freshly built responder/web JARs and records their hashes; the
application JAR inside `STEP13_JAVA_IMAGE` is not used.

## Pass criteria

The command must end with:

```text
0026 Step 13: PASSED; evidence: ...
Step 13 PASSED. Evidence: ...
```

Then inspect:

```powershell
Get-Content <evidence-directory>\evidence\summary.json
```

Required fields:

```text
status = PASSED
liveDevelopmentDatabaseModified = false
productionDatabaseModified = false
liveNasModified = false
cleanupFailures = []
```

Also review the browser screenshots (including missing-metadata/missing-file), `browser-image-verification.json`, `cleanup.json`, and the DeleteImage conflict/success evidence.

Do not mark Step 13 complete merely because the scripts compile. Completion requires a real
successful Docker/MQTT/responder/web/browser run and its captured evidence.
