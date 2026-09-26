# 0024 baseline file RPC response capture

The current responder was exercised over MQTT 5 on 2026-09-12. All 33 cases have
real request/reply evidence in `capture-20260912/`. This completes the Phase 1
response-capture item. It does not implement the 0024 Image catalogue.

## Execution boundary and provenance

This is an isolated Windows integration harness using the freshly built
`diaries-responder-0.0.9-SNAPSHOT-fat.jar`, the production MQTT RPC 0.0.8
`MessageHandler`, the real UploadFile/ListFiles/DeleteFile handlers, and the
real Authorization code. It uses a separate Docker Mosquitto broker bound only
to `127.0.0.1:18884`, with persistence disabled, and a new disposable Files root
under `diaries/build/`. The normal development broker and database were not
changed. The capture broker was stopped after use.

The file handlers do not use repositories. Full Responder startup, database
reconciliation, retained-state replay and account sign-in are deliberately not
part of this harness. Authentication uses synthetic ACTIVE EDITOR/READER claims
signed with an ephemeral random key in memory; invalid and absent tokens are
also sent. No real account, password or token is included in the evidence.

This follows the development-infrastructure execution pattern (Windows Java,
Docker MQTT), with a dedicated broker and filesystem for isolation. It is not
a production/Linux deployment capture. Exact component revisions, JAR and
source hashes, build metadata and broker image identity are in `provenance.json`.
The parent repository already had uncommitted Phase 1 evidence changes. The
responder source and client source were clean before capture/test additions.

## Files and recording format

- `capture-20260912/raw/*.json`: request function and exact synthetic arguments,
  authentication mode (tokens omitted), request/reply topics, correlation bytes,
  QoS/retain flags, decoded Paho response properties, exact payload bytes as
  base64 and their UTF-8 representation. Paho's properties dump includes SDK
  default/null fields; it is not a network packet trace.
- `capture-20260912/normalized/*.json`: status, payload, QoS/retain, function and
  case ID for portable test use. Only the actual Files-root prefix in payloads
  is replaced with `<FILES_ROOT>`. Windows separators and URL behaviour are
  preserved. Capture time/correlation IDs are absent from normalized fixtures.
- `capture-20260912/cases.json`: the same normalized cases in one array.
- `capture-20260912/fixtures/`: generated 2x3 PNG, 4x5 JPEG with fixed EXIF
  DateTime and a small generic binary file. No diary image content is used.
- `capture-20260912/environment.json`: Java/OS/timezone/root and capture time.
- `scripts/`: capture, replay, fixture export and compatibility verification.
- `validation.json`: actual checks and results, including the repeat capture.
- `SHA256SUMS.txt`: all files in this evidence directory except itself.

Filesystem mtimes are deliberately fixed in the synthetic fixture setup; JPEG
date extraction runs in UTC. Captured payload values are not altered to hide
ordering or date discrepancies. Raw payload JSON is not reserialized: its
base64 retains exact bytes. The outer capture record is a structured JSON log.

The existing Phase 1 `upload-response.json`, `list-files-response.json` and
`delete-file-response.json` now contain representative raw capture records.
Their filenames and hashes are recorded in `provenance.json`; they are aliases,
not the complete scenario set.

## Observed success contract

RPC status is the MQTT user property `status`, containing JSON such as
`{"code":200,"message":"ok"}`. Payloads are separate JSON values; there is no
JSON `{status,result}` wrapper. Replies use QoS 1, are not retained, and echo
the request correlation data to its response topic.

| Operation/item | Existing payload fields |
| --- | --- |
| uploadFile | `name:string`, `subdir:string`, `size:number`, `path:string`, `url:string` |
| listFiles | `subdir:string`, `items:array` |
| Image list item | `name:string`, `url:string`, `size:number`, `mtime:number`, `dir:false`; optional numeric `dateTaken` |
| Directory list item | `name:string`, `size:0`, `mtime:number`, `dir:true`; `url` and `dateTaken` omitted |
| deleteFile | `name:string`, `subdir:string`, `path:string` |

Root subdir is the empty string. Nested subdir and absolute path have Windows
separators in this capture. Date values are epoch milliseconds. ListFiles
returns directories alphabetically first, then recognized image extensions by
descending mtime; the generic `.bin` file is not listed. A missing `dateTaken`
is omitted, not null. The list includes the synthetic JPEG's EXIF date.
Deleting an absent file returns the same successful payload as deleting it.

The client's `uploadFile$` return annotation names `FileEntry`, but the actual
upload reply does not include list-only `mtime`, `dateTaken` or `dir` fields.
The tests therefore use the captured wire payload, not that annotation, as the
baseline. There is no current `deleteFile$` client wrapper; deletion is captured
through MQTT and tested with the shared deserializer/status dispatcher.

## Scenario coverage and observed defects

The 33 cases cover empty/root/nested/populated listings; PNG, JPEG and generic
uploads; image upload as octet-stream; spaces in paths; file dates; duplicate
conflict; generic overwrite; invalid names/subdirs; size/hash mismatches;
unsupported type; missing listing directory; existing/missing/nested deletes;
and missing/invalid/insufficient-role authentication for all three operations.

Observed error codes and payloads are recorded, not inferred:

- Duplicate upload: 409; invalid path/name: 400.
- Missing token and READER role: 401 (the current insufficient-role response is
  not 403).
- Malformed JWT: 500, with a JSON string explaining the malformed token.
- Size/hash mismatch and unsupported MIME: 500, with a JSON string reporting
  `ClassNotFoundException: Provider for jakarta.ws.rs.ext.RuntimeDelegate cannot
  be found`. The handlers throw `BadRequestException`; the current fat artifact
  cannot instantiate its required REST provider. This is pre-existing behaviour.
- Missing listing directory: 500 with a JSON string containing the missing path.
- Nested upload URLs have backslashes and unescaped spaces; ListFiles encodes
  the same path with forward slashes and `%20`.

These observations are separate defects/limitations, not new requirements to
preserve forever. They were not fixed as part of evidence capture.

## Compatibility assertions and intentional changes

`verify-compatibility.cjs` verifies raw/normalized agreement and MQTT metadata,
then compares existing fields recursively while allowing new object fields.
It rejects removed/renamed fields, changed types/values, array order/length
changes and null replacing omitted directory/date fields. Seven self-checks
exercise accepted additions and rejected regressions.

The client has ten focused Jasmine tests in
`src/app/mqtt/file-rpc-compatibility.spec.ts` and
`src/app/files-list-dialog/files-list-dialog.compatibility.spec.ts`.
The generated `src/app/testing/file-rpc-baseline.fixture.ts` comes directly from
these captured cases. Tests exercise the public upload/list methods, real
MQTT status/correlation dispatcher, shared deserializer, directory/file
presentation, EXIF date, folder navigation and file selection. The same
success replies are tested with extra `imageId`/`image` fields. No runtime
application code was changed.

The strict comparison command is a drift detector, not an instruction to
preserve every baseline defect. During 0024, review and separately test intended
changes: catalogued-image deletion/overwrite becomes a conflict, and canonical
path/URL handling may change. Do not overwrite this baseline to make tests pass.
Document explicitly scoped new expectations for those cases; continue checking
the unchanged generic-file contract and legacy success field types. Any later
fix to the recorded 500 errors likewise needs an explicit changed expectation.
The baseline capture harness will need Image repository wiring when future
handlers acquire catalogue dependencies.

## Repeat capture and verify

Build the current artifact using the wrapper from the Diaries repository root:

```powershell
.\gradlew.bat :diaries-responder:test :diaries-responder:build --console=plain
```

Set `$rpcEvidence` to this evidence directory, then use new output/work paths
inside the Diaries repository. Port 18884 must be free. The runner starts and
stops only its own disposable broker; it leaves synthetic work files available
for inspection and refuses existing output/work directories.

```powershell
& "$rpcEvidence/scripts/run-capture.ps1" `
  -ResponderJar '.\diaries-responder\build\libs\diaries-responder-0.0.9-SNAPSHOT-fat.jar' `
  -OutputDirectory '.\build\rpc-next-capture' `
  -WorkDirectory '.\build\rpc-next-files'

node "$rpcEvidence/scripts/verify-compatibility.cjs" `
  "$rpcEvidence/capture-20260912" '.\build\rpc-next-capture\cases.json'
```

Run the client checks from `diaries-client`:

```powershell
$env:CHROME_BIN = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
npm.cmd test -- --watch=false --browsers=ChromeHeadless --include=src/app/mqtt/file-rpc-compatibility.spec.ts --include=src/app/files-list-dialog/files-list-dialog.compatibility.spec.ts
npm.cmd run build -- --configuration production
```

The built-in comparator verifies this Windows baseline. A Linux capture must
be recorded separately and reviewed for platform path differences rather than
silently normalizing those differences away. Hash/verify the evidence before
use, and create a new dated capture for future changes.
