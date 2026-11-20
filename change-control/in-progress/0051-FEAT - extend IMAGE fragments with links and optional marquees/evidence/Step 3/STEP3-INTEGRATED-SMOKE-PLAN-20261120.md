# 0051 — Step 3 isolated integrated UI smoke and acceptance matrix

**Prepared:** 20 November 2026. **Status:** executable harness prepared; Windows preflight on 20 November stopped at a Cygwin Python launcher incompatibility; corrected browser-only fixture runner awaits execution. Step 3 remains OPEN.

## Existing accepted evidence (do not repeat)

- Step 2 owner-approved responder test task and disposable database/MQTT integration receipt `c1759df22f5f`.
- Step 3 Angular production build PASS, corrected targeted web HTTP tests PASS and Angular Chrome Headless **240/240 PASS** in `private/correction-20261120T130905Z`.
- Earlier failing logs remain historical evidence. Do not replace them or declare a prior failure successful retroactively.

## Disposable integrated browser smoke

Run `tools/verify-step3-isolated-ui.ps1` **from the Windows Cygwin terminal**, using the frozen 0024 `.dump` backup. The tool validates its SHA-256 before doing anything and does not use the existing development stack, local database volume or NAS. It builds current responder/web fat JARs, runs the proven 0026 disposable reader harness with 0051 additions, and creates a unique container network and PostgreSQL/Mosquitto/responder/web containers. The source Page and Image bytes are generated in the feature-owned evidence directory. All Docker host ports are loopback-only ephemeral ports. The runner deletes only containers and its network that it created. It never invokes any production command.

The runner reuses the proven 0026 fixture setup and checks legacy MARQUEE navigation plus real catalogue Image bytes, but **does not rerun** the already-accepted 0026 shared-image deletion, unavailable metadata/file, extended navigation and fault-injection suites. The 0051 extension applies the **0051 migration only to the disposable restored fixture**, enables the independent extension gate when the responder IMAGE authoring gate is enabled, then exercises these combinations:

| Scenario | PostgreSQL/MQTT checks | Desktop reader | Mobile reader |
|---|---|---|---|
| IMAGE, no link, no Marquee | Type and Image ID preserved; null link/Marquee | Plain image, source-page action, no selection | Covered by earlier 0026 baseline |
| IMAGE, link only | Exact URL persists, retained link, null Marquee | Clickable image distinct from source-page navigation | Existing responsive tests plus combined case |
| IMAGE, Marquee only | Same-page geometry/identity retained | Source highlight and Fit selection | Existing responsive tests plus combined case |
| IMAGE, link and Marquee | Both fields persisted and retained | Link and source highlight separate | 390px screenshots, month and source page |

Additional write checks: ordinary text edit preserves link; unsafe `javascript:` URL rejected; Marquee geometry edit preserves IMAGE identity/link; responder/web restart restores link/Marquee; explicit link clear and Marquee delete remove only intended references and publish proper retained state. The Image catalogue record/file remain intact. Desktop screenshots for all four combinations and mobile screenshots for the combined case are captured automatically.

**Evidence directory:** `evidence/Step 3/private/integrated-<UTC>-<id>/evidence/` with `summary.json`, fixture IDs, anonymised synthetic screenshots, Gradle build log, retained snapshots, container diagnostics, cleanup result and `SHA256SUMS.txt`. This is sensitive test evidence from the frozen fixture, and must stay in `private/`; do not publish it in a ZIP.

## Separate Angular editor visual acceptance (still required)

The above is a **real cross-component browser test of the public reader**, not proof of the signed-in Angular editor. Angular acceptance must be performed with a separate disposable client pointed at the same kind of isolated services, or with equivalent synthetic browser automation. Do not use production `pluto`, the persistent Compose database, or writable NAS mounting for authoring tests.

Capture desktop and narrow-screen screenshots plus a one-line result for each of:

1. Select an IMAGE without a link or Marquee. Confirm `Image ID: N` immediately follows Position in the Day reader and remains visible while catalogue metadata is pending.
2. Save an HTTP(S) link and confirm the displayed image is clickable. Check unsafe protocol rejection, clearing the link and preservation through a normal text edit.
3. Attach, edit and delete an IMAGE Marquee with the existing source-page tools. Confirm source highlight, Version/lock error reporting, and no type conversion to MARQUEE.
4. Repeat with both link and Marquee: image click opens the external destination while **Show on source page** navigates to/highlights the diary source. Ensure drag/reorder and keyboard selection are not activated by clicking the external link.
5. Verify missing image metadata/media fallback, legacy MARQUEE editing, keyboard focus, and a 390px layout.

Record the test system's actual Git/submodule revisions and screenshot names in `evidence/Step 3/private/`, and mark each criterion PASS/FAIL. **Do not close Step 3** until both this visual acceptance and the automated browser smoke have been reviewed. No production change/deployment is part of Step 3.

## Preconditions and execution

- Docker Desktop running, PowerShell 7 (`pwsh.exe`), Java 25/Gradle build support, Node modules already installed in `diaries-client`, Playwright and Chrome or Edge (Python/Pillow no longer required; synthetic images are generated by the browser Canvas API).
- Frozen backup: `data/database-backups/development-infrastructure/diaries-development-20260912-203528.dump`, SHA-256 `fe0e187eda4fe4c7923590f7ec5e36871ced87e2ba8fa6d3f882e0b0992d6b86`.
- Before running, inspect `git status --short` and `git submodule status`; preserve existing dirty changes. The tool does not modify source files.

Use the exact Windows Cygwin command in the accompanying delivery message. On failure preserve the evidence directory and upload the terminal output/summary, then fix only affected checks; don't repeat Step 1/2 acceptance suites.
