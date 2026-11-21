# 0051 Step 3 — Signed-in Angular editor acceptance (2026-11-20)

Status: **OPEN — execution required on Windows PowerShell 7**. No acceptance or production deployment is claimed by this package.

## Proven prerequisite

The separate public-reader integrated smoke `20261120T140504Z-fe13662e` passed, with candidate builds, retained topic replay and disposable-container cleanup. The 240 Angular unit tests, targeted web HTTP tests and production Angular build have also passed in earlier accepted evidence. This increment does **not** rerun those acceptance suites.

## Design and isolation

`tools/verify-step3-angular-editor.ps1` builds the Angular development candidate under its normal ignored `dist` directory and sets `STEP3_EDITOR_ONLY=1` for the previously successful disposable runner. In editor-only mode the runner prepares the same approved frozen backup in temporary PostgreSQL, a separate Mosquitto broker (with an additional loopback-only WebSocket port), an isolated responder and web reader, and generated source/catalogue images. It then **skips the already accepted four-variant public-reader suite** and uses `tests/step3-angular-editor-checks.cjs` to serve the Angular candidate on a loopback-only temporary HTTP port.

The editor runtime config is generated in memory for that server only. All file/media requests proxy to the isolated responder; MQTT WebSockets use the loopback-only Docker mapping. No NAS mounting or persistent local development stack is used. All Docker objects created by the runner are removed in its `finally` cleanup. A failed check must be reported as a failure, not accepted as a passed smoke.

## Browser acceptance assertions

1. Sign in through the Angular form with the synthetic test account and navigate to the selected IMAGE Fragment.
2. Confirm unsafe URL input cannot be saved; save a valid URL via the Angular editor and verify PostgreSQL persistence and image anchor.
3. Attach a Marquee via the toolbar while preserving the IMAGE type, Image reference, Page ownership and URL.
4. Use source navigation and verify the source viewer enables Fit selection, independently of external-link navigation.
5. Toggle Marquee edit mode, drag the visible selection and verify persisted geometry.
6. Open the Day reader tab and verify the `Image ID: N` label.
7. Sign in on a 390-pixel mobile viewport and capture the responsive layout.
8. Remove the Marquee and clear the URL through the editor; verify the original IMAGE reference remains intact.
9. Reject uncaught browser page exceptions and capture desktop/mobile screenshots, logs, Git state, JSON results, and SHA-256 evidence checksums.

## Execute

Terminal **Windows PowerShell 7**:

```powershell
$repo = 'C:\Users\Richard\git\github.com\rsmaxwell\diaries-application\diaries'
Set-Location $repo
$feature = 'change-control/in-progress/0051-FEAT - extend IMAGE fragments with links and optional marquees'
$script = Join-Path $repo "$feature/tools/verify-step3-angular-editor.ps1"
$backup = Join-Path $repo 'data/database-backups/development-infrastructure/diaries-development-20260912-203528.dump'
& $script -BackupFile $backup
```

Check for `PASS: 0051 Step 3 Angular editor acceptance runner` and an `integrated-*` evidence receipt whose `acceptanceMode` is `angular-editor`, status `PASSED`, and empty `cleanupFailures`. Inspect the PNGs and browser log before requesting Step 3 closure. Preserve any failure run. Do not modify the original frozen dump.

### Boundaries

This is an acceptance **test package**, not an application implementation change. Execution has not been verified here: Docker Desktop, Chrome, Angular CLI and PowerShell 7 run only on the Windows host. If any assertion fails, leave Step 3 OPEN and correct the affected test or application code based on the logged evidence. Production is not deployed.
