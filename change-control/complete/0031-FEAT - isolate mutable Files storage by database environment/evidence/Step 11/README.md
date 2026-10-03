# 0031-FEAT — Step 11 evidence

## Status

**COMPLETE — 2026-10-02.**

Step 11 — **Repoint local modes and verify resolved runtime paths after overrides** — is closed.

The normal `local.env` common override was verified end-to-end for all three supported local execution modes:

```text
DIARIES_DB_DATA_DIR=./data/database/common
DIARIES_FILES_DIR=files-development-common
```

See [`CLOSE-OUT.md`](CLOSE-OUT.md) for the completion decision.

## Authoritative successful runtime evidence

The passing workstation captures are:

```text
runtime/development-infrastructure-20261002-170911/
runtime/local-docker-build-20261002-172734/
runtime/local-published-smoke-20261002-172947/
STEP11-RUNTIME-SUMMARY.json
```

Earlier trial capture directories may also remain under `runtime/`. They are retained as diagnostic history but are superseded by the three successful captures listed above.

The final cross-mode comparison reported:

```text
PASS: all three local modes resolve the common database + files-development-common pair.
PASS: every runtime report retains /files and includes responder startup/runtime logs.
PASS: Step 11 cross-mode summary written ...\evidence\Step 11\STEP11-RUNTIME-SUMMARY.json
```

## Verified runtime contract

Across the three modes the evidence proves:

- the effective database dataset is `./data/database/common`;
- the effective mutable Files selector is `files-development-common`;
- neither local Docker mode falls back to the production `files` selector;
- both local Docker modes render the expected PostgreSQL host-data mount;
- both local Docker responders bind the selected NAS subpath to stable `/data/files`;
- the shared original diary scan tree remains available at `/data/diaries` read-only;
- direct Windows development generates an effective responder configuration whose `diaries.files` resolves to `files-development-common`;
- a catalogued Image exists beneath the selected runtime Files root;
- the public `/files/...` route returns HTTP 200;
- the shared `/diaries/...` route returns HTTP 200; and
- every successful capture completed without upload/delete/rename operations.

## Corrections made during verification

Runtime verification identified two issues before Step 11 was closed:

1. `capture-local-mode.ps1` originally contained a UTF-8 em dash in a BOM-less script. Windows PowerShell 5.1 decoded it using the local ANSI code page, producing a parser error. The report separator was changed to ASCII and the static verifier now guards the Step 11 PowerShell scripts against non-ASCII content while they remain BOM-less.
2. `compose.local-published-smoke.yaml` did not provide the same local PostgreSQL defaults used by the other local modes. It now defaults the local database/user/password consistently to `diaries`, and the Step 11 verifier covers that contract.

An intermediate `local-docker-build` startup also encountered host port 5433 already in use while another local mode was still active. Stopping the previous mode resolved the environmental conflict; the authoritative `local-docker-build` capture then passed.

## Safety

The Step 11 collector is non-destructive. Its database work is read-only, filesystem checks are existence/listing only, and HTTP checks use `HEAD`. The passing reports explicitly record that no upload/delete/rename operation was performed.

Production remained under the existing Step 8 write freeze during these local checks. Destructive Image lifecycle validation remains deferred until after Step 12 reconciliation.

## Source/tooling

The Step 11 operating and capture tooling remains under:

```text
scripts/windows/0031-step11/
scripts/windows/common/report-effective-dataset.bat
scripts/windows/validation/verify-0031-step11.py
```

The three local `start.bat` / `status.bat` paths continue to expose the effective database + Files selection and enforce the paired-selector guard.

The original execution procedure remains in [`RUNBOOK.md`](RUNBOOK.md). The closure-aware static verifier now requires the implementation plan to record the reviewed runtime completion; refreshed outputs are retained in `verification-output.txt` and `regression-output.txt`.

## Hand-off

Step 11 is complete. Keep destructive Image lifecycle testing deferred.

**Next implementation step:** Step 12 — reconcile every new effective database + Files-root pair against the Step 9 baseline.
