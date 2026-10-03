# 0031-FEAT — Step 11 close-out

**Decision:** COMPLETE — 2026-10-02

Step 11 — **Repoint local modes and verify resolved runtime paths after overrides** — is closed.

The normal local override intentionally makes all three local execution modes consume one durable non-production dataset pair:

```text
./data/database/common
    -> files-development-common
```

Step 11 has now proved that this pair is what each runtime actually resolves after environment-file overrides, while preserving the stable application-visible paths.

## Authoritative successful captures

The successful runtime captures retained on the Windows working copy are:

```text
runtime/development-infrastructure-20261002-170911/
runtime/local-docker-build-20261002-172734/
runtime/local-published-smoke-20261002-172947/
```

The final cross-mode comparison generated:

```text
STEP11-RUNTIME-SUMMARY.json
```

and reported:

```text
PASS: all three local modes resolve the common database + files-development-common pair.
PASS: every runtime report retains /files and includes responder startup/runtime logs.
PASS: Step 11 cross-mode summary written ...\evidence\Step 11\STEP11-RUNTIME-SUMMARY.json
```

Any earlier failed/trial capture directories under `runtime/` are diagnostic history only. The three timestamped passing captures above are the authoritative Step 11 mode evidence.

## Development-infrastructure result

The direct Windows development capture proved:

```text
Effective database data: ./data/database/common
Effective Files selector: files-development-common
Generated responder config: diaries.files -> files-development-common
Direct Files root: exists
Shared diary root: exists
Responder startup log: captured
Catalogue Image path: exists beneath effective Files root
/files route: HTTP 200
/diaries route: HTTP 200
Mutation performed by capture: none
```

This proves that the direct-responder path honours the same effective database/Files pair selected by the local override even though it reaches the physical Files root through generated responder configuration rather than a Docker mount.

## Local-docker-build result

After ensuring no other local mode occupied the shared development ports, the stack started with PostgreSQL, MQTT and responder healthy. The passing capture proved:

```text
Effective database data: ./data/database/common
Effective Files selector: files-development-common
Rendered database mount: matches effective database data directory
Selected NAS Files subpath: bound to /data/files
Shared /data/diaries: read-only
Runtime mount inspection: PASS
Read-only /data/files listing: PASS
Responder startup/runtime log: captured
Catalogue Image path: exists beneath /data/files
/files route: HTTP 200
/diaries route: HTTP 200
Mutation performed by capture: none
```

## Local-published-smoke result

The published-image stack started with PostgreSQL, MQTT, responder, web and client healthy. The passing capture proved the same runtime contract as local-docker-build:

```text
Effective database data: ./data/database/common
Effective Files selector: files-development-common
Rendered database mount: matches effective database data directory
Selected NAS Files subpath: bound to /data/files
Shared /data/diaries: read-only
Runtime mount inspection: PASS
Read-only /data/files listing: PASS
Responder startup/runtime log: captured
Catalogue Image path: exists beneath /data/files
/files route: HTTP 200
/diaries route: HTTP 200
Mutation performed by capture: none
```

## Issues resolved before closure

Step 11 verification usefully exposed and resolved two implementation defects before the step was closed:

1. **Windows PowerShell 5.1 parser failure.** A UTF-8 em dash in the BOM-less `capture-local-mode.ps1` was decoded incorrectly on Windows and caused a parser error. The output separator was replaced with ASCII and the Step 11 verifier now guards the BOM-less PowerShell scripts against non-ASCII content.
2. **Published-smoke PostgreSQL defaults.** `compose.local-published-smoke.yaml` did not use the same local `diaries` defaults for PostgreSQL database/user/password as the other local modes. The Compose file and regression guard were corrected.

A later `local-docker-build` startup initially failed because host port 5433 was still occupied by the preceding local mode. That was an operational concurrency conflict, not a data/configuration defect; the modes were then run one at a time and the authoritative capture passed.

## Completion decision

Step 11 is complete because:

- every supported local execution mode resolves the intended `common` database + `files-development-common` durable pair after overrides;
- the direct Windows responder and both Docker responders agree on the selected Files dataset;
- both Docker modes preserve the stable `/data/files` runtime path while selecting the new physical NAS root;
- the shared original diary tree remains read-only at `/data/diaries`;
- startup/status diagnostics expose the effective database and Files selectors;
- the stable public `/files/...` route remains functional in all three modes;
- the shared `/diaries/...` route remains functional in all three modes;
- no successful capture falls back to production `files`;
- responder startup/runtime evidence exists for every mode;
- the final cross-mode comparison passes; and
- all verification was non-destructive, with no upload/delete/rename operation performed.

## Checksum note

The close-out overlay does not contain the runtime evidence bytes generated on the Windows workstation, so `SHA256SUMS.txt` intentionally covers the Step 11 implementation/source, the closure-aware verifier and refreshed static verification outputs, and the close-out documents available to this package. The runtime directories and `STEP11-RUNTIME-SUMMARY.json` remain the authoritative workstation-generated runtime evidence and are referenced by exact path above; no checksum values for files not present in this overlay have been invented.

## Operational hand-off

Step 11 does **not** unfreeze destructive Image lifecycle testing. Keep the production write freeze and the existing Step 8/9 rollback/reconciliation evidence intact.

**Next implementation step:** Step 12 — reconcile every new effective database + Files-root pair against the Step 9 pre-split baseline before beginning the controlled cross-dataset lifecycle tests in Step 13.
