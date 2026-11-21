# 0051 Step 3 — Browser-fixture generator correction (20 November 2026)

## Observed failure

The Windows Cygwin command successfully found the 0051 test script and frozen backup.
PowerShell 7 aborted during the preflight dependency check, trying to execute
`C:\tools\cygwin\bin\python` as a native Windows program:

`No application is associated with the specified file for this operation.`

No 0051 PostgreSQL/MQTT/browser assertions were executed. The earlier
responder and client regression evidence remains valid. This is a harness
compatibility failure, not an application defect.

## Correction

- Remove the PowerShell preflight invocation of Cygwin Python/Pillow and the
  unneeded `-Python` argument and `STEP13_PYTHON` environment setting.
- Create the same disposable Page and catalogue test image files using the
  existing Playwright Chromium/Edge executable and Canvas 2D API.
- Preserve image dimensions, JPEG/PNG encoding, label/outline and disposable
  fixture locality, and reject unsupported Page extensions explicitly.
- Continue to require the same frozen database backup checksum, Docker
  isolation and unchanged application build/test gates.

## Evidence and execution

The failed console log is the user-supplied `note(20261120-132951).txt`.
The fix is source-reviewed and JS syntax-checked; **no Windows execution has
been claimed**. The runner will create a new uniquely named evidence directory.
The previous integrated preflight failure needs no deletion or reproduction.

Step 3 remains OPEN until the public reader integrated smoke and the separate
Angular editor visual smoke meet their acceptance criteria.
