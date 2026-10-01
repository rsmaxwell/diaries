# Step 12 verification commands and result

Run from the repository root on the normal Windows Java 25/Docker development machine using **PowerShell 7**. The recorded rerun used **PowerShell 7.6.6**.

```powershell
.\gradlew.bat :diaries-web:test `
  --tests "*Step12MqttHttpIntegrationTest" `
  --tests "*MqttReaderAclIntegrationTest" `
  --rerun-tasks --console=plain
```

Recorded result (2026-09-29):

```text
BUILD SUCCESSFUL in 1m 16s
7 actionable tasks: 7 executed
```

Then run the complete gate:

```powershell
.\gradlew.bat :diaries-web:test :diaries-web:build `
  --rerun-tasks --console=plain
```

Recorded result (2026-09-29):

```text
BUILD SUCCESSFUL in 1m 35s
15 actionable tasks: 15 executed
```

The exact PowerShell 7.6.6 console output is preserved as `test-results.txt`.
