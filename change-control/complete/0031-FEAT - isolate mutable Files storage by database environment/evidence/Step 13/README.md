# 0031-FEAT — Step 13 evidence

## Status

**COMPLETE — 2026-10-03.**

Step 13 — **Prove cross-dataset isolation with controlled Image lifecycle tests** — is closed. The real workstation/pluto run completed the production BEFORE -> local upload -> second-mode observe -> supported delete -> production AFTER chain successfully. See [`CLOSE-OUT.md`](CLOSE-OUT.md) for the closure decision and authoritative evidence identities.

## Authoritative completed run

The successful evidence identities are:

```text
production BEFORE:
  /home/richard/projects/diaries/data/0031-step13/production-before-20261002-203216

local lifecycle:
  runtime/local-20261003-080333-8f26d1bc/

production AFTER:
  /home/richard/projects/diaries/data/0031-step13/production-after-20261003-083327
```

The local lifecycle uploaded Image 88 in `development-infrastructure`, proved the same row/bytes/retained state and `/files/...` URL from `local-docker-build`, then removed the row, retained topic and physical file through `deleteImage`. The production AFTER helper reported `PASS: Step 13 production controls are unchanged.`

The successful retained-tree startup also proved 10,657 retained topics can be captured completely with the Step 13 queue/segmentation correction.

## Implemented proof

The Step 13 procedure brackets all local mutation with an immutable production control:

```text
production BEFORE control while diaries-responder is stopped
    -> local upload in one common-pair mode
    -> second local mode observes the same durable row/file
    -> supported deleteImage lifecycle removes the disposable Image
    -> production AFTER control compared byte-for-byte with BEFORE
```

The local harness creates a uniquely named 1x1 PNG under `0031-step13/` and uses the real authenticated responder RPC surface. It records:

- `uploadFile` request/result evidence without credentials;
- the Image database row from the active local PostgreSQL container;
- the retained `diaries/images/<id>` publication;
- the physical file and SHA-256 in the selected effective Files root;
- the returned `/files/...` URL and HTTP-served byte checksum;
- a safe `overwrite=true` retry proving the current catalogued-Image workflow rejects replacement with 409;
- a second-mode observation proving intentional sharing of `./data/database/common` + `files-development-common`;
- the supported `deleteImage` result;
- the live MQTT tombstone and subsequent absence of retained Image state;
- database row and physical-file absence after deletion; and
- loss of HTTP 200 serving for the deleted URL.

The harness refuses concurrent local database modes and refuses the second-mode proof when the upload mode is still the active mode.

## Production control

The Playbooks role adds:

```text
roles/diaries/files/sync/scripts/step13-capture-production-control.sh
```

The helper requires the production responder to remain stopped, requires `DIARIES_FILES_DIR=files`, captures the complete production `image` table in deterministic id order, and builds a SHA-256 inventory of every file under production `/data/files`, including `.image-staging` if present.

The `after` phase requires the exact `before` directory and fails unless both the Image-row capture and Files inventory are byte-for-byte unchanged.

## Implementation correction — production hash capture

The first production `before` attempt exposed a shell portability bug in the new helper: the original SHA-256 extraction used an `awk` program containing `$1` while the disposable shell was running with `set -u`. `/bin/sh` therefore treated that token as an unset shell positional parameter before `awk` could consume it. The helper now captures the full `sha256sum` output and removes the filename suffix using POSIX shell parameter expansion, so no positional parameter is involved. The failed attempt is diagnostic history only; the corrected production BEFORE capture later passed and is the authoritative control.

## Implementation correction — Windows PowerShell parser

The first local `upload` attempt exposed a PowerShell interpolation error in the new lifecycle harness. A diagnostic string used `$rc:` inside a double-quoted string; PowerShell parses a colon immediately after an unbraced variable name as part of the variable reference. The diagnostic now uses `${rc}:`. The Step 13 source verifier now explicitly guards this form so the parser defect cannot recur unnoticed. The failed upload attempt made no lifecycle mutation because PowerShell rejected the script at parse time.

## Implementation correction — responder HTTP readiness semantics

The next local `upload` attempt reached a healthy direct responder, but the Step 13 harness rejected the responder because it treated `GET /diaries` returning HTTP 404 as a readiness failure. That assumption contradicted the existing `development-infrastructure/test-responder-api.bat` contract: the responder owns the static `/diaries` context, and requesting the context itself normally returns 404 when no concrete file is named. The responder log for the failed attempt completed synchronization and connected the MQTT RPC listener; no lifecycle mutation had started because the harness failed before credential prompting and `uploadFile`.

The harness now performs `GET /diaries`, explicitly accepts **HTTP 404** as the required reachability result, and then lets the real MQTT RPC operation prove application readiness. The portable Step 13 verifier guards this contract. The existing successful production BEFORE control remains valid and must not be recaptured for this correction.

## Source verification

Portable source verifiers are provided in both repositories:

```text
python scripts/windows/validation/verify-0031-step13.py
python roles/diaries/tests/verify-0031-step13.py
```

The local Node helper can also be syntax checked with:

```text
node --check scripts/windows/0031-step13/step13-rpc.cjs
```

## Runtime evidence location

The Windows harness writes each lifecycle run below:

```text
evidence/Step 13/runtime/local-YYYYMMDD-HHMMSS-<token>/
```

The production helper writes controls on pluto below:

```text
/home/richard/projects/diaries/data/0031-step13/production-before-YYYYMMDD-HHMMSS/
/home/richard/projects/diaries/data/0031-step13/production-after-YYYYMMDD-HHMMSS/
```

Preserve/copy the complete successful production directories into the Step 13 evidence before close-out rather than recreating summaries by hand.

## Completion gate — satisfied

The authoritative controlled run has proved all of the following:

- production BEFORE control captured with responder writes frozen;
- one local mode uploaded the disposable Image into the common pair;
- a different local mode observed the same database row and physical bytes;
- the supported deletion path removed the local row, retained state and physical file;
- the production AFTER Image capture is identical to BEFORE; and
- the production AFTER Files SHA-256 inventory is identical to BEFORE.

See [`RUNBOOK.md`](RUNBOOK.md) for the execution sequence and [`CLOSE-OUT.md`](CLOSE-OUT.md) for the closure decision.

## Runtime blocker discovered during local upload — retained snapshot queue exhaustion

A later local upload attempt proved that the Step 13 RPC timeout was only a symptom: the direct responder exited during startup before the MQTT RPC listener was created. The failure was `Retained snapshot drain marker was not received` from `Synchronise.perform()`.

The investigation distinguished two different backlog paths:

1. **database -> initially empty Mosquitto** — the responder controls publication and can pace/batch that work; and
2. **already-populated Mosquitto -> newly attached snapshot subscriber** — once the subscription is accepted, retained replay is broker-driven and the application cannot directly pace individual retained deliveries.

The previous local broker configuration used `max_inflight_messages 20` together with `max_queued_messages 10000`. An aggregate retained tree larger than that finite per-client QoS queue could therefore lose later queued messages, including the non-retained drain marker used to prove the replay had completed.

Step 13 now applies two complementary safeguards in the Diaries repository:

- the responder snapshots non-overlapping top-level retained branches sequentially: `diaries/diaries/#`, `diaries/pages/#`, `diaries/fragments/#`, `diaries/marquees/#`, `diaries/images/#`, `diaries/dates/#`, `diaries/people/#`, and `diaries/roles/#`; and
- both the normal local broker and the disposable large-tree test broker use `max_queued_messages 0` while retaining `max_inflight_messages 20`.

The branch split reduces peak backlog and gives deterministic progress/drain points. The unlimited message-count queue is the current correctness safeguard for the broker-driven retained replay: it removes the arbitrary 10,000-message ceiling while MQTT QoS acknowledgements and `max_inflight_messages 20` continue to bound messages simultaneously in flight.

This is explicitly an **interim design decision**. After the current TODO features are complete, revisit retained-tree recovery and consider finer segmentation of the subscription space with paced successive subscriptions, or another bounded protocol that proves a complete snapshot before reintroducing a finite queue limit.

The Diaries-only Step 13 package changes the local/test Mosquitto configuration. The production Ansible/Playbooks Mosquitto configuration still has its own finite queue setting and must be reviewed/aligned before the production responder is deliberately resumed with this startup path. Production remains frozen for the current Step 13 evidence run.

The large-retained-tree integration fixture remains above the historical 10,000-message threshold and exercises branch-by-branch snapshot recovery using the unlimited test-broker queue. The queue/startup correction has now been runtime validated against the real common dataset: the responder drained all configured branches, captured **10,657** retained topics, reported `sizeof(topicTreeMap) = 10657` and `sizeof(databaseMap) = 10657`, completed `synchronise: ok`, and started the `diaries/rpc/request` listener. That startup correction was subsequently included in the successful controlled lifecycle run and final production AFTER comparison.



## Implementation correction — invalid Step 13 PNG fixture

After retained-tree startup was proven against 10,657 topics, the authenticated Step 13 upload reached the real `uploadFile` handler but returned HTTP-equivalent RPC status 400. The embedded 1x1 PNG fixture itself was invalid: the `IDAT` chunk CRC did not match its chunk bytes. The responder's strict `ImageMetadataInspector` correctly rejected the malformed image before catalogue commit.

The fixture has been replaced with a complete CRC-valid 1x1 PNG that also decodes through Java `ImageIO`. The portable Step 13 verifier now extracts the embedded base64 fixture and validates the PNG signature, every chunk boundary and CRC, and the terminal `IEND`, preventing another malformed lifecycle fixture from reaching runtime. The failed upload created no Image catalogue row or file and requires no cleanup.


## Implementation correction — retained Image observer identity

The first upload using the corrected PNG fixture completed the real `uploadFile`
operation and returned Image id **87**, but the Step 13 helper then reported zero
retained messages on `diaries/images/87`. The upload-side product path was not the
problem: `UploadFile` publishes that canonical topic retained at QoS 1 and waits
for broker completion before returning success.

The verification helper was connecting its retained-state observer with the
Angular `diaries-client` MQTT identity. That identity may write the RPC request
and read its client-specific response, but the current ACL intentionally does
not grant it read access to `diaries/images/+`. The harness therefore could not
observe the retained catalogue message it had just caused the responder to
publish.

Step 13 now separates MQTT identities: RPC traffic continues to use the normal
client identity, while retained Image observation uses the responder MQTT
credentials from the effective responder configuration selected for the active
mode. Those credentials are injected only into the child Node process environment
and are restored immediately afterward; they are not recorded in evidence.

Because Image 87 was committed before the verifier failed, a guarded recovery
action has also been added. `-Action cleanup -ImageId <id>` only accepts database
rows whose path matches the generated Step 13 disposable naming convention and
then removes the Image through the supported authenticated `deleteImage` RPC,
verifying retained-state, physical-file and HTTP removal. This recovery must be
used for Image 87 before starting the successful controlled upload run.


## Implementation correction — PowerShell zero-row scalarisation during recovery cleanup

The first guarded cleanup of Image 87 reached the application credential prompt and then failed with `The property 'Count' cannot be found on this object.` The defect was in the harness post-delete verification: PowerShell emits no pipeline object for an empty query result, so assigning `Get-ImageRows` directly produced `$null`; StrictMode then rejected `$remaining.Count`. Because this check occurs after the supported `deleteImage` RPC returns, the failed harness run may already have completed the actual deletion.

All `Get-ImageRows` callers now use `@(Get-ImageRows ...)`, giving deterministic array semantics for zero, one or many rows. Recovery cleanup is additionally idempotent: when the requested id is already absent it verifies that no retained `diaries/images/<id>` state exists and that no generated Step 13 PNG candidates remain in the active Files root, records an `alreadyAbsent` recovery proof, and exits successfully without attempting a second deletion.

### Implementation correction — local Docker CIFS staging permissions

The Step 13 cross-mode delete exposed a local-mode consistency regression. The direct Windows responder created and used the shared `.image-staging` work directory successfully, but `local-docker-build` mounted the same Files root through CIFS without `dir_mode=0700,file_mode=0600`. Linux therefore exposed the staging directory with permissions that failed the responder's owner-only staging invariant before deletion could stage bytes or mutate the database.

Both local Docker compose files now use `vers=3.0,dir_mode=0700,file_mode=0600`, matching the production Playbooks compose template. The lifecycle harness also checks the effective container-side mode before continuing. Because Docker local-volume driver options are fixed when the named volume is created, an existing mode-specific `nas-photo` volume must be removed and recreated after applying this correction; only that CIFS volume is removed, not the PostgreSQL or MQTT data volumes.
### Implementation correction — PowerShell permission-probe quoting

After the CIFS volume was recreated successfully, runtime verification proved `/data/files` and `/data/files/.image-staging` both appeared as mode `700`. The v10 lifecycle guard nevertheless failed before `deleteImage` because its `sh -c` script was enclosed in a PowerShell double-quoted string. Under `Set-StrictMode -Version Latest`, PowerShell attempted to expand the shell-local `$p` variable and raised `VariableIsUndefined`. v11 encloses the shell script in a PowerShell single-quoted string so `$p` is evaluated only by `/bin/sh`. This failure occurred before the delete RPC was sent, so the Step 13 Image remains intact for the retry.


### Implementation correction — native-command quoting in container permission probe

The v11 pre-delete guard still failed before RPC dispatch on Windows PowerShell 5.1. Although the shell program was protected from PowerShell variable expansion, native-command argument marshalling split/truncated the quoted `sh -c` program before Docker passed it into the container, producing `/bin/sh: syntax error: unexpected end of file`. Runtime had already proved both `/data/files` and `/data/files/.image-staging` were mode `700`, so the CIFS fix itself remained valid and Image 88 was not mutated by this failed attempt.

V12 removes the inline `sh -c` program entirely. The harness now calls `docker exec ... stat` and `docker exec ... test -d` directly for `/data/files` and `.image-staging`, eliminating the PowerShell -> Docker -> shell quoting boundary. The verifier rejects reintroduction of either nested `sh -c` form. No Docker-volume recreation or local-mode restart is required when the v10 volume already reports mode `700`; retry the existing Step 13 delete with the same RunDirectory.
