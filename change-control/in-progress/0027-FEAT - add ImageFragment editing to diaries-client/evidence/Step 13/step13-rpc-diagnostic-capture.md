# Step 13 redacted RPC diagnostic capture

## Purpose

The live Step 13 lifecycle proved the UI/database/retained-topic/file behaviour, but the normal `RpcService` console log intentionally omits RPC `args`. That made the five representative request/reply pairs in the Step 13 acceptance evidence ambiguous, especially the distinction between an omitted `imageId`, a positive `imageId`, and explicit `imageId:null`.

This diagnostic capture is a temporary, opt-in evidence facility for `0027-FEAT` Step 13. It is deliberately implemented in the client RPC layer so it sees the exact JSON request object before MQTT serialization and the matching MQTT v5 status reply after correlation.

## Safety/redaction rules

The capture is available only in Angular development mode, is **off by default**, and only records these two functions:

- `addImageFragment`
- `updateFragment`

For request args it allow-lists only Fragment/Image identifiers, page/date/sequence/version, `imageId` state/value, `marqueeId` presence state and `textLength`. It never stores transcription text, access tokens, refresh tokens, passwords or MQTT credentials.

For a successful `addImageFragment` reply it stores a redacted committed Fragment summary (id/page/type/image/date/sequence/version/text length), not the raw reply. For `updateFragment` it stores only the numeric success reply when one is present. Error reply payloads are not stored; only status code/message are retained.

Entries are kept in browser `sessionStorage` so a gate-disabled -> gate-enabled responder switch does not lose the evidence. At most 200 entries are retained.

## Browser controls

`RpcService` installs this development diagnostic API on `window`:

```javascript
window.__diariesStep13RpcDiagnostics.enable()
window.__diariesStep13RpcDiagnostics.disable()
window.__diariesStep13RpcDiagnostics.clear()
window.__diariesStep13RpcDiagnostics.status()
window.__diariesStep13RpcDiagnostics.entries()
window.__diariesStep13RpcDiagnostics.exportJson()
window.__diariesStep13RpcDiagnostics.download()
```

Enable and clear before the focused evidence sequence:

```javascript
window.__diariesStep13RpcDiagnostics.enable()
window.__diariesStep13RpcDiagnostics.clear()
window.__diariesStep13RpcDiagnostics.status()
```

No page reload is required. While enabled, each target request emits a one-line console record prefixed `[STEP13-RPC] request`, and each completed pair emits `[STEP13-RPC] pair`.

After the five required pairs have been exercised:

```javascript
window.__diariesStep13RpcDiagnostics.download()
```

This downloads `step13-rpc-diagnostics-<timestamp>.json`.

## Import and acceptance validation

From the Diaries project root, import the downloaded file into the active Step 13 run:

```powershell
$step13 = '.\change-control\in-progress\0027-FEAT - add ImageFragment editing to diaries-client\evidence\Step 13\tooling'
& "$step13\step13-import-rpc-diagnostics.ps1" -Path "$env:USERPROFILE\Downloads\step13-rpc-diagnostics-<timestamp>.json"
```

The importer refuses to copy evidence unless all five representative pairs are present:

1. gate disabled: `addImageFragment` -> 403;
2. gate disabled: Image-reference `updateFragment` (`imageId` positive or null) -> 403;
3. gate enabled: `addImageFragment` -> 200;
4. gate enabled: `updateFragment` with positive `imageId` -> 200;
5. gate enabled: `updateFragment` with explicit `imageId:null` -> 200.

It also rejects JSON containing authentication/password keys or a raw `text` field. On success it copies the JSON to the current run as `rpc-diagnostics.json` and writes `rpc-diagnostics-validation.txt` with the five matched correlation IDs.

## Focused repeat sequence

The whole Phase B lifecycle does not need to be repeated. Use disposable development objects only:

- gate disabled: attempt Add Image Fragment and one attach/replace or Clear Image operation on an existing IMAGE Fragment; both must produce 403;
- switch to gate enabled;
- Add Image Fragment against a disposable/catalogued Image; it must produce 200 and a committed redacted Fragment reply;
- on that disposable Fragment, Clear Image (`imageId:null`) and reattach the same disposable Image (positive `imageId`), both 200;
- delete the disposable Fragment afterwards if desired; Fragment deletion is outside this diagnostic capture.

The order of the positive/null updates is unimportant; the importer validates by function/status/imageId state rather than by position in the JSON array.

When evidence has been imported, disable capture:

```javascript
window.__diariesStep13RpcDiagnostics.disable()
```

Then return the responder to `imageFragmentWritesEnabled=false` as required by the main Step 13 runbook.

## Final live result — 2026-10-05

The focused live capture was completed and imported successfully. The importer validated 5 entries and all required cases passed:

- disabled `addImageFragment` -> 403: `71938f00-c436-446a-96ec-3dbcdf957b41`;
- disabled Image-reference `updateFragment` with `imageId:null` -> 403: `988c5859-f9e8-4e4d-bd4e-599aecf6ccc0`;
- enabled `addImageFragment` -> 200: `c2d1b1b7-36c5-43a2-8142-3a007a591d61`, committed Fragment `2336`;
- enabled positive-`imageId` `updateFragment` -> 200: `4f09c858-165f-423a-adb2-99efc832efc7`;
- enabled explicit-`imageId:null` `updateFragment` -> 200: `dd588fdc-0f74-4e6d-9244-b0add8930371`.

The importer also reported `PASS: no forbidden authentication/password keys or raw text field found`. The JSON and validation summary were copied into run `20261004-002349`, the browser diagnostic was disabled, and disposable diagnostic Fragments `2335` / `2336` were deleted afterwards.
