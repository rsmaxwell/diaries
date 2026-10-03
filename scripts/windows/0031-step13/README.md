# 0031-FEAT Step 13 local lifecycle harness

This directory contains the controlled local Image lifecycle proof for Step 13.
It is intentionally split into three commands because all three local modes
normally point at the same durable pair and must never run PostgreSQL against
`./data/database/common` concurrently.

Use:

```bat
scripts\windows\0031-step13\run-local-lifecycle.bat -Action upload
scripts\windows\0031-step13\run-local-lifecycle.bat -Action observe -RunDirectory "<run-directory>"
scripts\windows\0031-step13\run-local-lifecycle.bat -Action delete -RunDirectory "<run-directory>"
```

A narrowly scoped recovery action is also available for a prior Step 13 upload
that committed before evidence capture failed:

```bat
scripts\windows\0031-step13\run-local-lifecycle.bat -Action cleanup -ImageId <id>
```

`cleanup` refuses any Image whose database `relative_path` is not a generated
`0031-step13/0031-step13-YYYYMMDD-HHMMSS-<token>.png` path. It uses the normal
authenticated `deleteImage` RPC and verifies row, file, retained-topic and HTTP
removal; it never repairs the state with direct SQL or filesystem deletion.

Before any lifecycle phase, the harness confirms that the responder HTTP server
is reachable using the established static-context contract: `GET /diaries` must
return **HTTP 404** when the context itself has no file to serve. In this responder,
that 404 is the expected reachability result rather than a readiness failure; the
actual lifecycle operations are then exercised over MQTT RPC.

The upload command creates a uniquely named 1x1 PNG below `0031-step13/`, calls
the real authenticated `uploadFile` RPC, proves the local database row,
retained `diaries/images/<id>` state, physical byte checksum and returned
`/files/...` URL, and verifies that a same-path `overwrite=true` request is
still rejected with 409 because catalogued Images are not replaceable through
the current supported upload workflow.

The observe command refuses to run in the same local mode that performed the
upload. Start a different local mode first. It proves that the second mode sees
the same row and physical bytes because both modes deliberately consume the
same `./data/database/common` + `files-development-common` durable pair.

The delete command is blocked until an `OBSERVE-*.json` proof exists. It calls
the supported `deleteImage` RPC and proves row removal, the live MQTT tombstone,
absence of retained Image state, disappearance of the physical file and loss of
HTTP 200 serving for the disposable URL.

Application credentials are prompted and are not written to evidence. MQTT RPC
traffic uses the normal `diaries-client` broker identity from
`diaries-client/public/assets/config.json`. Retained Image verification is
deliberately performed with the responder MQTT identity from the effective
responder configuration, because the client ACL does not grant read access to
`diaries/images/+`. The wrapper passes those observer credentials to the Node
process only through temporary environment variables and restores them afterward;
they are never written to runtime evidence.

Broker connection settings can still be overridden for the current process using
`DIARIES_STEP13_BROKER_URL`, `DIARIES_STEP13_BROKER_USERNAME` and
`DIARIES_STEP13_BROKER_PASSWORD`.

`diaries-client/node_modules/mqtt` must exist. Run `npm install` in
`diaries-client` if dependencies are not already installed.


The embedded 1x1 PNG fixture is CRC-valid and is source-verified chunk-by-chunk.
This matters because `uploadFile` performs strict PNG container/CRC inspection before
committing the Image catalogue row; a malformed test fixture must fail before any
lifecycle state is created.


## V9 recovery hardening

PowerShell pipeline output is scalarised when a command returns exactly one item and becomes `$null` when it returns no items. Under `Set-StrictMode -Version Latest`, accessing `.Count` on that `$null` value raises `PropertyNotFoundStrict`. All Image-query call sites now wrap `Get-ImageRows` in `@(...)` so zero, one and many rows have stable array semantics.

`cleanup` is also idempotent. If the requested Step 13 Image id is already absent (for example because `deleteImage` completed and the previous harness crashed during the post-delete row check), cleanup verifies that the canonical retained topic is absent and that there are no generated Step 13 PNG candidates left in the active Files root, then records an `alreadyAbsent` recovery proof instead of attempting a second delete.

Local Docker modes must mount the mutable Files root with `dir_mode=0700,file_mode=0600`; otherwise the responder correctly refuses `.image-staging` because its POSIX view is not owner-only. The harness checks this before lifecycle mutation. Docker volume driver options are immutable for an existing named volume, so recreate only the mode-specific `nas-photo` volume after applying a mount-option change.
The container permission probe intentionally passes its `sh -c` program as a PowerShell single-quoted string. This keeps shell-local variables such as `$p` out of PowerShell interpolation under StrictMode.



## V12 container permission probe

The local Docker permission preflight deliberately avoids `sh -c`. Windows PowerShell 5.1 can alter native-command quoting before Docker receives the argument, so the harness executes `stat` and `test -d` directly inside the responder container. This verifies `/data/files` and, when present, `/data/files/.image-staging` as mode `700` without nested shell quoting.
