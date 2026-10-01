# Offline authoring verification (not the full Step 14 gate)

The source-only execution environment has Java 21, Node 22 and **no Docker command or daemon**. Java 25, the Windows PowerShell runner, Compose/Testcontainers and live browser-deployment integration cannot be honestly certified here. The Gradle 9.6.1 wrapper also had no cached distribution; its network download failed with `UnknownHostException: services.gradle.org` (`gradle-toolchain-probe.log`). `RESULTS.json` intentionally reports `BLOCKED` because its `--preflight-only` invocation **did not run** the full gate. This evidence must not be used to close Step 14.

Checks actually executed successfully against this bundle:

- Step 14 Python harness: **6 tests passed** (report parsing, skipped/missing Docker cases, inventory drift, credential-free Compose summary).
- Retained snapshot Node regression: **4 passed**, including synthetic 5,376-topic drain and negative cases.
- Catalogue HTTP Node regression: **4 passed** (safe nested path encoding and failure/preflight diagnostics).
- Reverse proxy routing Node regression: **3 passed** (restart-safe routing behavior).
- `py_compile` for Step 14 Python verifier: passed.
- Source SHA-256 inventory: 470 allow-listed source/config/validation files; `sourceInventory.stable=true` at the time of this preflight. This *authoring* inventory is not a substitute for the workstation's fresh candidate inventory.

The initial Compose sanitizer unit test used an overly broad assertion excluding the word `environment`, which also appears in the innocuous key `environmentSource`. The assertion was corrected to reject secret-bearing `PASSWORD` and `driver_opts` fields; all six final tests passed. No production source changed.
