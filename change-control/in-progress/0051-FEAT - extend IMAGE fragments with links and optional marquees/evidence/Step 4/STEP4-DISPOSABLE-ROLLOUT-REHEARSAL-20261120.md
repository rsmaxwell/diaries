# 0051 Step 4 — coordinated disposable rollout and rollback rehearsal

**Prepared:** 20 November 2026. **Execution status:** NOT RUN. Step 4 remains OPEN.
No production deployment, Docker publication, backup change, NAS access or 0028 migration is authorised.

## Scope and preconditions

The accepted 0051 Steps 1–3 already establish the new feature’s database/MQTT and
browser functionality. This focused Step 4 test verifies the **deployment
boundary** rather than rerunning the entire accepted browser suite:

1. Record current Windows parent/submodule Git status and all six Docker image
   IDs/digests. Build uniquely tagged, local candidate responder, web and
   Angular client images from the current working checkout. Record the Java JAR SHA-256 hashes **inside the built candidate images**
   (not from a second, separate Gradle build). Do not push images.
2. Require exact matching IDs for the three previously deployed production
   images, recorded in Step 1 on 20 November:

   | Component | Historic tag | Measured production image ID |
   |---|---|---|
   | Responder | `0.0.9-build-84` | `sha256:ba88249cd7d64d651f98738d6dec6cee3c8a34bdae58351d5a145dc8db3169c3` |
   | Web reader | `0.0.9-build-8` | `sha256:9dfcd29d85e09f6613f973aab5bde93604147db569db88e049ee35c3cce377f9` |
   | Angular client | `0.0.9-build-77` | `sha256:8d49e621f83f145b98b86cdc25978bb50398c2cb7779203f04299dd92487d0bc` |

3. Restore the approved immutable `diaries-development-20260912-203528.dump`
   (SHA-256 `fe0e187eda4fe4c7923590f7ec5e36871ced87e2ba8fa6d3f882e0b0992d6b86`)
   into a **new disposable PostgreSQL container**. Apply the existing 0024/0025
   and additive 0051 schema as required. Broker and all containers use a random
   network/name and localhost-only published ports. The only file mounts contain
   newly generated, synthetic Pages and Images beneath this run’s evidence directory.
4. With `imageFragmentWritesEnabled=true` and
   `imageFragmentExtensionsWritesEnabled=false`, prove that plain IMAGE and
   existing MARQUEE authoring work, while link creation, link update and IMAGE
   Marquee attachment reject with HTTP-style 403 without changing the saved
   link or Marquee relationship. Confirm current web-reader HTTP/retained replay
   and client static entry point.
5. **Before any extension write**, swap to the three measured legacy images.
   Verify old responder sign-in and plain IMAGE creation, reader HTTP/retained
   presentation and old client HTTP. Check the previously created IMAGE and
   nullable schema are preserved. No overlapping responder writers.
6. Re-upgrade to the three candidate images while the extension gate remains
   false; verify old data and denied extension writes. Only **after legacy
   containers are removed**, activate the extension gate on the candidate
   responder and write one synthetic URL-bearing IMAGE. Verify PostgreSQL,
   MQTT retained state and candidate web rendering. **NEVER** restart old
   binaries after that write; this is an explicitly unsafe rollback target.
7. Capture every Docker image identity, JAR hash, request/result, source
   revision, container health/log excerpt, evidence hashes and container
   cleanup receipt. A PASS requires all checks and no cleanup failures.

An HTTP-only client-entry-point probe is **not** an old Angular authoring-session
compatibility test. Full signed-in modern Angular editor checks were separately
accepted in Step 3. This rehearsal proves old-version startup only on
**pre-activation old-format state**; it deliberately does not test old readers
or writers against link/IMAGE-Marquee state.

## Run (Windows PowerShell 7)

After applying this feature-specific change package with Beyond Compare 4:

```powershell
$repo = 'C:\Users\Richard\git\github.com\rsmaxwell\diaries-application\diaries'
Set-Location $repo
$feature = 'change-control/in-progress/0051-FEAT - extend IMAGE fragments with links and optional marquees'
$script = Join-Path $repo "$feature/tools/verify-step4-disposable-rollout.ps1"
$backup = Join-Path $repo 'data/database-backups/development-infrastructure/diaries-development-20260912-203528.dump'
& $script -BackupFile $backup
```

The runner builds three new local Docker images and may pull the three historic
published images if they are not cached; it **does not push or deploy**. It does
not invoke the existing `compose.local-docker-build.yaml` or
`compose.local-published-smoke.yaml`, because both currently mount NAS Files
with write access. Their use against existing data is not a safe substitute for
this isolated rehearsal. The reporter preserves any failed run for analysis.

## Evidence and remaining gates

Results go under `evidence/Step 4/private/rollout-<UTC>-<id>/`, including
`result.json`, `image-identities.json`, `jar-hashes.json`,
`disposable/evidence/step4-rollout-receipt.json`, native build logs,
MQTT snapshots, container cleanup and `SHA256SUMS.txt`.

A local candidate Docker **image ID** proves which image ran. A registry
**RepoDigest** might legitimately be absent for an image built locally and not
pushed; the runner records the actual field rather than inventing a digest.

This PASS would not alone satisfy Step 4’s production gate: the actual
`mango` role rendering, published candidate release images, a fresh approved
production DB/Files recovery point, live service baseline and explicit separate
approvals for production deployment and extension activation remain outstanding.
Production extensions should remain disabled until all writers/readers are
compatible. Feature 0028 stays PAUSED.
