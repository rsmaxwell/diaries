# Diaries Windows validation tooling

This directory contains supported validation and diagnostic entry points. Completed-feature-only verification harnesses are preserved with the corresponding records under `change-control/complete/`; they are not normal live commands.

## Live script anti-accumulation guard

Run the permanent source-layout guard from the Diaries project root:

```text
python scripts/windows/validation/verify-live-script-policy.py
```

It permits only the explicitly supported top-level `scripts/windows` areas and rejects feature/step-shaped helpers such as `NNNN-step*`, `verify-NNNN-*`, `stepN-*` and `migrationNNNN*` unless the exact path has been deliberately classified as permanent in the guard. The guard is also executed by `verify-dataset-pair-guard.py`, so it participates in the normal local safety regression path.

The guard's synthetic positive/negative cases can be exercised without modifying the live tree:

```text
python scripts/windows/validation/verify-live-script-policy.py --self-test
```

## Dataset and Files isolation regressions

Run these from the Diaries project root. The Python checks are static/portable and do not modify PostgreSQL, mutable Files content, MQTT retained state or Docker services.

```text
python scripts/windows/validation/verify-local-dataset-layout.py
python scripts/windows/validation/verify-direct-development-files-config.py
python scripts/windows/validation/verify-dataset-pair-guard.py
python scripts/windows/validation/verify-local-backup-restore-semantics.py
python scripts/windows/validation/verify-complete-dataset-manifest.py
python scripts/windows/validation/verify-local-complete-dataset-backup-engine.py
python scripts/windows/validation/verify-local-complete-dataset-finalisation.py
python scripts/windows/validation/verify-local-complete-dataset-restore-preparation.py
python scripts/windows/validation/verify-effective-dataset-diagnostics.py
```

`verify-local-dataset-layout.py` checks the committed per-mode database/Files defaults, the paired common override in `local.env.example`, and the `/data/files` Compose selector.

`verify-direct-development-files-config.py` checks the generated direct-development responder configuration, the stable public `/files` contract and integration with the supported direct responder launch path.

`verify-dataset-pair-guard.py` checks the committed dataset topology, guard integration, Compose mounts and stable public Files contract. On Windows, run the exact guard-case suite as well:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\validation\verify-dataset-pair-guard.ps1
```

`verify-local-backup-restore-semantics.py` protects the database-only backup/restore contract, dataset sidecar identity and matched database/Files selection across all three local modes. It is also the permanent 0033 Step 1 freeze: it protects mode-then-`local.env` precedence, the shared `common` pairing, effective-dataset backup naming, PostgreSQL custom/plain formats, current manual local writer-quiescence warning, destructive confirmation and the rule that these sidecars remain explicitly database-only.

`verify-complete-dataset-manifest.py` protects the 0033 complete-backup directory and schema-2 manifest contract. It creates only synthetic temporary fixtures: it proves candidate generation/validation, partial-workspace rejection, final promotion semantics, relative component paths, supported schema/completion markers, required hashes/components and exact Files inventory validation. It does not access a real PostgreSQL database or mutable Files root.

`verify-local-complete-dataset-backup-engine.py` protects the 0033 Step 3 local capture engine. It statically proves that the three mode wrappers remain thin, the common engine preserves mode-then-`local.env` precedence, derives the backup namespace from the effective dataset, refuses unavailable/staged Files, identifies/quiesces local writers while retaining PostgreSQL, captures both dump formats plus durable Files into one `.partial` workspace, preserves prior writer state for Step 4, and leaves failures incomplete with writers stopped. It also models both isolated committed defaults and the shared `common` override without touching live data.

`verify-local-complete-dataset-finalisation.py` protects the 0033 Step 4 local finalisation path. It exercises the permanent hash/inventory helper on synthetic source/captured Files, proves source drift and malformed SQL are rejected, drives the schema-2 manifest through partial-candidate validation and promotion, verifies final media independently, deliberately corrupts/restores a completed fixture, and statically protects the verify-before-promote-before-writer-restart orchestration order.

`verify-local-complete-dataset-restore-preparation.py` protects the 0033 Step 5 local restore-preparation path. It statically protects complete-media/target identity validation, database-only input rejection, `pg_restore --list`, explicit confirmation, writer quiescence, the mandatory verified complete safety backup, and the non-destructive Step-5 boundary. Its synthetic staged-Files fixture proves exact path/size/SHA-256 verification and rejection of changed, extra, missing or transient `.image-staging` content.

`verify-local-complete-dataset-restore-apply.py` protects the 0033 Step 6 destructive apply/rollback path. It freezes custom-dump-only drop/recreate/`pg_restore --exit-on-error` semantics, same-parent Files replacement with an explicit pre-restore rollback sibling, fresh/benign-only runtime staging, changed-half failure state and executable safety-backup rollback. Its synthetic filesystem rehearsal proves pre-restore extra durable files disappear after exact replacement, rollback restores the old tree, and the immediate post-rename promotion-failure point remains recoverable.

`verify-local-complete-dataset-restore-postflight.py` protects the 0033 Step 7 acceptance path. It freezes the writers-stopped failure state, rollback availability after failed postflight, database/Files/catalogue verification before service restoration, responder health + retained replay checks, representative MARQUEE/IMAGE MQTT and `/files` verification, prior-writer restoration only after successful postflight, and rollback closure only after `restore-complete`. Its synthetic catalogue fixture accepts only catalogued matches plus the previously reviewed legacy `Thumbs.db` exception and rejects changed checksums or unexplained untracked Files.

`verify-effective-dataset-diagnostics.py` protects the effective-dataset diagnostics printed by normal start/status commands and the stable runtime paths used after local overrides.

The direct-development runtime check is also non-destructive; it generates the ignored effective responder configuration and runs the focused responder URL/path unit test:

```text
scripts\windows\validation\verify-direct-development-files-runtime.bat
```

## ImageFragment reader regression

The permanent helper regressions are feature-neutral and can be run without Docker:

```text
node --test scripts/windows/validation/imagefragment-retained-snapshot.test.cjs
node --test scripts/windows/validation/imagefragment-image-http.test.cjs
node --test scripts/windows/validation/imagefragment-proxy-routing.test.cjs
```

`smoke-imagefragment-reader.cjs` is the disposable cross-component ImageFragment reader runner. `verify-imagefragment-reader.ps1` is its Windows wrapper: it runs the three helper suites, builds the current responder/web candidates, starts only disposable PostgreSQL/Mosquitto/responder/web fixtures, and writes evidence to a new caller-supplied directory.

Because that full runner deliberately creates and deletes fixture Images and Fragments, it is not part of routine storage-tooling cleanup verification. Use it when ImageFragment reader behaviour itself needs end-to-end verification.

## Image catalogue regression

The existing catalogue validation remains available through:

```text
test-image-catalogue.ps1
smoke-image-catalogue.cjs
```

These commands use disposable fixtures and have their own backup/evidence arguments. `test-image-catalogue.ps1` is also the supported full client/responder/web regression gate: it provisions disposable PostgreSQL plus MQTT/TCP/WebSocket fixtures, enables the responder's opt-in database/MQTT/browser integration tests, runs the Java suites/builds and Angular suite/production build, and rejects failed or skipped tests. Its broker fixture is the permanent `image-catalogue-test-mosquitto.conf`; it must not depend on historical completed-feature evidence. The fixture is functional/test-only, loopback-published and deliberately accepts anonymous clients because the browser integration fixture has no broker credentials; production Mosquitto authentication/ACL configuration remains separate. They are not required merely to verify script-directory cleanup.

## Production image inspection helpers

`prepare-image-production-bundle.ps1` and `inspect-image-production.py` are read/inspection-oriented production evidence helpers. They are not normal start/stop/backup/restore commands.

## Historical tooling

Historical feature-step scripts and structural validators are retained under completed change-control evidence, including the 0031 storage-isolation tooling and the 0026 reader close-out tooling. Do not copy those files back into this live validation directory merely to rerun an old close-out sequence; use the archived copies in the historical feature record when historical reproduction is required.
