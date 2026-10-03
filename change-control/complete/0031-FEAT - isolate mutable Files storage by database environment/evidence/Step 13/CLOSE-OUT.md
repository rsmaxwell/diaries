# 0031-FEAT — Step 13 close-out

**Decision:** COMPLETE — 2026-10-03

Step 13 — **Prove cross-dataset isolation with controlled Image lifecycle tests** — is closed.

The controlled lifecycle run has now proved both sides of the 0031 storage invariant that matter for this step:

```text
same effective database dataset
    -> same mutable Files root is intentionally shared

different effective database dataset
    -> production database + Files state is unchanged
```

The successful run used the normal local common pair:

```text
Database data: ./data/database/common
Files root:     files-development-common
```

and bracketed that mutation with immutable production BEFORE/AFTER controls while the production responder remained stopped.

## Authoritative successful evidence

The successful evidence identities are:

```text
production BEFORE
  /home/richard/projects/diaries/data/0031-step13/production-before-20261002-203216

local lifecycle
  evidence/Step 13/runtime/local-20261003-080333-8f26d1bc

production AFTER
  /home/richard/projects/diaries/data/0031-step13/production-after-20261003-083327

production comparison
  /home/richard/projects/diaries/data/0031-step13/production-after-20261003-083327/COMPARISON.txt
```

The successful local disposable Image was **Image 88** with relative path:

```text
0031-step13/0031-step13-20261003-080333-8f26d1bc.png
```

An earlier committed disposable Image, **Image 87**, belonged to a failed verifier attempt and was removed through the guarded supported-RPC recovery path. Its recovery proof is:

```text
evidence/Step 13/runtime/recovery/CLEANUP-IMAGE-87.json
```

That recovery run reported that Image 87 was already absent and that its retained state and Step-13 physical-file candidates were also absent.

## Production BEFORE control

The corrected production helper captured the BEFORE control with production writes frozen and reported:

```text
PASS: Step 13 production BEFORE control captured with responder writes frozen.
Evidence: /home/richard/projects/diaries/data/0031-step13/production-before-20261002-203216
```

The production responder remained stopped for the complete controlled local lifecycle.

## Local upload proof — development-infrastructure

The authoritative upload was performed in `development-infrastructure` against the approved common pair and reported:

```text
PASS: uploaded disposable Image in development-infrastructure, proved DB row, retained topic, physical file and stable /files URL.
Evidence: .../runtime/local-20261003-080333-8f26d1bc
```

The upload phase proved the Image simultaneously through:

- the local common PostgreSQL `image` row;
- retained `diaries/images/88` state;
- the physical PNG under `files-development-common`;
- matching physical/static-served bytes and checksum;
- the stable public `/files/...` URL; and
- a 409 conflict for a same-path `overwrite=true` attempt, confirming that the supported catalogue workflow did not silently replace the catalogued Image.

## Cross-mode sharing proof — local-docker-build

`development-infrastructure` was stopped completely before the second mode was started, so two PostgreSQL containers never addressed `./data/database/common` concurrently.

`local-docker-build` then resolved the same pair:

```text
Database data: ./data/database/common
Files dir:     files-development-common
```

and reported:

```text
PASS: local-docker-build sees the same Image row, bytes, retained Image and /files URL created by development-infrastructure.
```

This is the positive sharing proof required by 0031: two modes that intentionally select the same effective durable database dataset also select and observe the same mutable Files root.

## Supported deletion proof

With `local-docker-build` still active, the same lifecycle run then reported:

```text
PASS: deleteImage removed the common-dataset row, retained topic and physical file in local-docker-build.
```

The delete phase therefore proved removal through the supported application path rather than direct SQL/filesystem manipulation. The evidence checks the database row, retained MQTT state/tombstone, physical file and former static URL.

## Production AFTER control

After the local mode was stopped, the production responder was still stopped and the AFTER helper compared production with the exact BEFORE directory. It reported:

```text
PASS: Step 13 production controls are unchanged.
Comparison: /home/richard/projects/diaries/data/0031-step13/production-after-20261003-083327/COMPARISON.txt
Evidence: /home/richard/projects/diaries/data/0031-step13/production-after-20261003-083327
```

The helper compares both the deterministic production `image` table capture and the SHA-256 inventory of the production mutable `/data/files` tree byte-for-byte. This is the negative isolation proof: the controlled local upload/delete cycle did not mutate the production Image catalogue or production Files tree.

## Runtime defects exposed and resolved during Step 13

Step 13 deliberately exercised the real runtime paths and exposed several defects before closure. The successful final run includes the corrections for all of the following:

1. **Production SHA capture shell portability.** Removed the `awk "$1"`/`set -u` positional-parameter collision from the production control helper.
2. **PowerShell parser/interpolation defects.** Corrected `${rc}:`, deterministic array handling for zero-row database results, and the local-Docker permission preflight so Windows PowerShell 5.1 no longer corrupts nested shell arguments.
3. **HTTP readiness semantics.** `GET /diaries` returning 404 is now treated as the responder's established static-context reachability result; MQTT RPC proves application readiness.
4. **Retained snapshot queue exhaustion.** The local/test broker now uses `max_queued_messages 0` with `max_inflight_messages 20`, and responder startup snapshots the non-overlapping retained branches sequentially.
5. **Real retained-tree validation.** The common dataset successfully drained **10,657 retained topics**, reached `sizeof(topicTreeMap) = 10657`, `sizeof(databaseMap) = 10657`, `synchronise: ok`, and started the RPC listener.
6. **Invalid test PNG.** The embedded fixture was replaced with a CRC-valid 1x1 PNG and the verifier now checks PNG chunk CRCs.
7. **Retained observer ACL mismatch.** RPC traffic continues to use the client MQTT identity, while retained Image observation uses the effective responder MQTT identity without recording its credentials in evidence.
8. **Guarded cleanup recovery.** A narrowly scoped `cleanup` action uses supported `deleteImage` to recover an unrecorded generated Step-13 Image and is idempotent when the Image is already absent.
9. **Local Docker CIFS permission mismatch.** Both local Docker Compose modes now mount the mutable NAS tree with `dir_mode=0700,file_mode=0600`, matching the responder's owner-only `.image-staging` requirement and the existing production mount convention.

## Interim retained-snapshot decision and deferred redesign

`max_queued_messages 0` is an intentional **interim correctness safeguard**, not the final retained-snapshot architecture.

The runtime investigation distinguished two flow-control cases:

- database -> initially empty broker can be application-paced; and
- populated broker -> newly subscribed retained-snapshot client is broker-driven and cannot be paced message-by-message by the application.

The branch-by-branch subscriptions reduce individual replay bursts, while the unlimited queued-message count prevents an arbitrary finite queue from silently truncating a complete retained snapshot. MQTT QoS acknowledgements plus `max_inflight_messages 20` still limit messages simultaneously in flight.

After the current TODO features are complete, revisit this design. In particular, consider finer segmentation of the subscription space with paced successive subscriptions, or another bounded complete-snapshot protocol, before reintroducing a finite queued-message limit.

The Diaries-only Step 13 implementation changed the local/test Mosquitto configuration. The production Playbooks broker configuration still requires explicit review/alignment before the production responder is restarted.

## Security follow-up discovered during evidence capture

Responder MQTT-RPC diagnostic logging currently records sensitive `signin` request/response content, including credentials/tokens. No secret value is copied into this close-out.

Raise/fix a follow-up defect to redact authentication secrets and tokens from responder/MQTT-RPC logs. Treat any captured unredacted log as sensitive and rotate credentials/tokens as appropriate.

This logging issue does not invalidate the Step 13 isolation proof, but it must not be normalised as acceptable operating behaviour.

## Completion decision

Step 13 is complete because:

- a production BEFORE control was captured with responder writes frozen;
- the approved local common database/Files pair was used for the controlled mutation;
- `development-infrastructure` uploaded a real disposable Image through authenticated `uploadFile`;
- the Image was proved in the database, retained MQTT state, physical Files root and stable `/files/...` URL;
- a different local mode, `local-docker-build`, observed the same row and bytes only because it intentionally consumes the same durable pair;
- the supported `deleteImage` path removed the local row, retained state and physical file;
- the production AFTER Image capture matched BEFORE;
- the production AFTER Files SHA-256 inventory matched BEFORE; and
- no production Image/File mutation was required to make the proof pass.

## Evidence packaging note

The timestamped Windows runtime directory and the two production directories are generated operational evidence. This close-out overlay references them by exact identity and does not fabricate copies/checksums for evidence bytes that are not part of the overlay.

`SHA256SUMS.txt` covers the Step 13 close-out files present in this package. `SOURCE-SHA256SUMS-DIARIES.txt` and `SOURCE-SHA256SUMS-PLAYBOOKS.txt` retain the source checksums for the already-applied Step 13 implementation.

## Operational hand-off

Keep the production responder stopped until Step 14 deliberately deploys/reviews the explicit production configuration. Before restarting it, align/review the production Mosquitto retained-snapshot queue policy so the local Step 13 correctness fix is not lost in production.

**Next implementation step:** Step 14 — deploy the explicit production configuration non-destructively.
