# 0024-FEAT Phase 12 Closure Summary

**Feature:** 0024-FEAT - introduce reusable persistent Image catalogue  
**Phase:** phase-12-closure  
**Date:** 2026-09-25

## Purpose

This phase records the final production evidence needed to close 0024
after resolving the production NAS/CIFS staging problem and exercising
the real image-upload/catalogue workflow.

## Evidence recorded in this directory

| File | Purpose | Result |
|---|---|---|
| `001-upload-small-image.txt` | Small-image end-to-end upload control test | PASS |
| `002-upload-large-image-timeout.txt` | Large-image upload and timeout finding | PASS server-side; client timeout observed |
| `003-image-database-verification.txt` | PostgreSQL `public.image` verification | PASS |
| `004-image-mqtt-verification.txt` | Retained `diaries/images/<id>` verification | PASS |
| `005-filesystem-verification.txt` | Production CIFS/staging filesystem verification | PASS |

## Final production state

Two images were used for the final upload verification.

### Small image

`Screenshot 2026-09-25 121352.png`

The operation completed within the client's RPC timeout.

Verified:

- physical image file present under `diary-1830/images/`
- PostgreSQL `public.image` row created as image id 86
- retained MQTT catalogue entry present under `diaries/images/86`
- client received the successful RPC response

### Large image

`img2221.jpg`

The Angular client reported:

```text
Upload failed: RpcError: Status undefined: Timeout
```

However, independent verification showed that the responder completed the
operation successfully.

Verified:

- physical image file present under `diary-1830/images/img2221.jpg`
- PostgreSQL `public.image` row created as image id 85
- retained MQTT catalogue entry present under `diaries/images/85`
- image metadata, dimensions and checksum populated

The timeout is therefore a **false client-side failure indication**, not
an image-upload or catalogue-integrity failure.

## Final significant 0024 finding

A large image upload can take longer than the Angular client's ordinary
MQTT RPC timeout.

The existing implementation sends the binary image through the MQTT RPC
request. For a large image the complete operation includes transport,
staging/persistence to the NAS-backed filesystem, image inspection and
catalogue registration before the operation can return.

In the observed production test the client stopped waiting, but the
responder continued and completed the operation correctly.

This residual issue should **not** be addressed by further expanding
0024.

It should be handled as a separate follow-on feature using the preferred
transport split:

- **HTTP** for streaming/bulk image bytes
- **MQTT** for commands, control messages and retained catalogue/state

This preserves MQTT for the work it is well suited to while avoiding
large base64/binary payloads in the RPC path.

## Filesystem closure

The production `diaries_nas-photo` Docker volume was recreated with CIFS
options including:

```text
dir_mode=0700,file_mode=0600
```

The responder sees `/data/files` and `.image-staging` through the SMB
filesystem with the required modes.

Synthetic production tests verified:

- hard links
- same-directory rename
- cross-directory rename from `.image-staging`
- deletion and cleanup

The real application uploads then confirmed that files can be promoted
into their final diary image directory.

The production CIFS/staging problem is therefore considered resolved.

## Closure conclusion

The final evidence demonstrates consistency across the three relevant
representations of uploaded Images:

1. **NAS filesystem**
2. **PostgreSQL `public.image`**
3. **retained MQTT `diaries/images/<id>` state**

The small upload succeeds completely from the client's perspective.

The large upload also completes correctly at the responder, filesystem,
database and retained-MQTT layers; only the client RPC wait expires.

On this basis, the remaining large-image transport/timing limitation is a
separate architectural follow-on rather than an unresolved 0024 data
integrity defect.

**0024 is closed. Administrative close-out completed on 2026-09-26 at the
user's request; the complete feature record is now under `change-control/complete`.**

The supported catalogue deletion operation and client UI are tracked in
[0030](../../../../todo/0030-FEAT%20-%20allow%20deletion%20of%20catalogued%20Images/README.md).
Generic `DeleteFile` remains protected. Feature 0025 must add reference-aware
deletion before ImageFragment authoring is enabled. Neither that work nor the
large-image transport follow-up is claimed as implemented by this closure.

This administrative update preserves the production observations above; it did
not rerun uploads, migrations or production checks.
