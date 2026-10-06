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
python scripts/windows/validation/verify-effective-dataset-diagnostics.py
```

`verify-local-dataset-layout.py` checks the committed per-mode database/Files defaults, the paired common override in `local.env.example`, and the `/data/files` Compose selector.

`verify-direct-development-files-config.py` checks the generated direct-development responder configuration, the stable public `/files` contract and integration with the supported direct responder launch path.

`verify-dataset-pair-guard.py` checks the committed dataset topology, guard integration, Compose mounts and stable public Files contract. On Windows, run the exact guard-case suite as well:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\validation\verify-dataset-pair-guard.ps1
```

`verify-local-backup-restore-semantics.py` protects the database-only backup/restore contract, dataset sidecar identity and matched database/Files selection across all three local modes.

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
