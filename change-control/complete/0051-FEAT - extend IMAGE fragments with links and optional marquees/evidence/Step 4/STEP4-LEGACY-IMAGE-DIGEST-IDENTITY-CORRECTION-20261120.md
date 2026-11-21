# 0051 Step 4 — published legacy image identity: failure and correction

**Date:** 20 November 2026. **Status:** corrective package prepared, Windows rehearsal rerun pending. **Step 4 remains OPEN.**

## Evidence and failure

The rehearsal `rollout-20261120T162538Z-eba5f7c1` passed the PowerShell syntax check but stopped before the candidate Docker builds because the local responder image ID differed from the image ID of the running `pluto` container. Read-only inspection showed both images were Linux/AMD64 and shared the same published repository digest and creation timestamp. The two image IDs differ across Docker daemon/image-store representations; equality of image IDs is therefore not a valid cross-host acceptance condition.

The production observation (read-only `docker inspect` + `docker image inspect` on `pluto` at 16:34 UTC) recorded:

| Component | Running production image ID | Repository digest |
|---|---|---|
| Responder `0.0.9-build-84` | `sha256:ba88249cd7d64d651f98738d6dec6cee3c8a34bdae58351d5a145dc8db3169c3` | `rsmaxwell/diaries-responder@sha256:d0f9224d759e06cabf26eb19722b3b417b170f7c6e3919c481acbe64db507695` |
| Client `0.0.9-build-77` | `sha256:8d49e621f83f145b98b86cdc25978bb50398c2cb7779203f04299dd92487d0bc` | `rsmaxwell/diaries-client@sha256:9b510d4611792bb37907ec45c0400f11cdc7baa7e7dfaecd007a8e7ec9427edd` |
| Web `0.0.9-build-8` | `sha256:9dfcd29d85e09f6613f973aab5bde93604147db569db88e049ee35c3cce377f9` | `rsmaxwell/diaries-web@sha256:063e5296f9b49f40f43bf89cc2d5ce4fcdc63a98efe211a57ae884a30981254b` |

## Correction

Keep the exact legacy image tags and recorded production IDs for traceability, but validate each local legacy image against its *full expected repository digest* and **Linux/AMD64** platform. Treat missing, mismatched or incorrectly named repository digests as blocking errors. Write the compared values and verification status into `baseline-image-identities.json` before building candidates. Neither the production database nor the 0028 migration is touched.

The correction changes only the Step 4 PowerShell runner and its read-only static regression test. It preserves the earlier failure log, the successful Step 1–3 acceptance evidence and all application/Playbooks code.

## Required next verification

1. Apply this correction via Beyond Compare to the Windows Diaries working tree, preserving unrelated changes.
2. Run the complete PowerShell parser check (`[System.Management.Automation.Language.Parser]::ParseFile`) and then `verify-step4-disposable-rollout.ps1` against the verified 0024 frozen fixture.
3. Confirm that all three local images match the exact repository digests and Linux/AMD64; inspect the newly captured baseline identity receipt.
4. Verify candidate builds, disabled-gate behaviour, preactivation rollback, re-upgrade, forward-only activation, cleanup and receipt hashes. **Do not** restart legacy binaries after extension writes.

**Not yet accepted:** Docker rehearsal, production deployment and Step 4 closure. Any deployed image publication or activation requires explicit approval.
