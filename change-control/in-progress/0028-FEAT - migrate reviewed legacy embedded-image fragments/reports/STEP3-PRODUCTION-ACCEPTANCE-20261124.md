# 0028 Step 3 — production migration acceptance (24 November 2026)

**Decision: CLOSED — owner explicitly accepted Step 3 on 24 November 2026.**
**Feature status: remains IN PROGRESS.** This records acceptance of Step 3, not permission to move the feature to `complete/`.

## Production execution and identity

- Production source: `pluto` Diaries PostgreSQL 18 and associated Files dataset.
- Pinned one-shot migration artifact SHA-256: `9a2910515bbe0929c93c0557f91c2b27b8323bb9da61fb2573a0ff9b20c209a1`.
- Live production dry-run: `DRY_RUN_PASS`, `reviewedConversions=71`, `deferredFragments=[1564]`, `writes=false`; accepted plan SHA-256: `3510eb32429f789d1b99c8e26e315d060950975afe477a2910cc86d7b7b55730`.
- Applied 24 November 2026: `APPLY_COMMITTED_DATABASE_PASS_MQTT_REPLAY_PENDING`; migration journal installed, production apply process returned success. **Do not rerun apply** to create evidence.
- Production database postflight: `POSTFLIGHT_DATABASE_PASS_MQTT_NOT_CHECKED` (passed subsequently).
- Reviewed scope: 71 conversions committed; Fragment **1564** remains explicitly deferred and unchanged by this migration. Do not imply the entire legacy population has been normalised.
- Report evidence digests used for production apply: backup report SHA-256 `6cb9be986aa3b193f3622762db4a3cab10a283062c8abe374ceaa23b7795df43`; accepted rehearsal report SHA-256 `51b4bc38a19ca1654efe65116a7d2141cf7b639ed8cdf77243d3f476976c5f4d`.

## Recovery and restart

- Post-writer-stop production backup identity reported as `production/20261124-172811Z`; matching protected snapshot name `20261124-173416Z` observed on `mars` and `backup` (17:34/17:36 UTC). Existing detailed receiver hold and backup evidence must remain in the private Step 3 records; the matching directory names alone do not independently prove a complete Files restore.
- `pluto` maintenance `reopen` restored original PostgreSQL HBA content (reported SHA-256 `31f65ccbe621d83a6ac98fad2428bc075a05a566a32bc869da7313b9e34a7349`) and original timer/responder state.
- Production PostgreSQL, Mosquitto and responder all running with `RestartCount=0`; backup publication timer active.
- Responder startup log at 19:21:37 UTC reported `Synchronise - synchronise: ok`; migrated retained fragment objects were published, including Fragments 84, 598, 606, 1397 and 1461. MQTT connections, RPC listener, `getVersion` and sign-in RPC all succeeded.
- **Evidence limit:** the logs demonstrate responder startup synchronisation and sample retained publications, not an independent exhaustive 71/71 topic-by-topic database-to-broker diff or every tombstone check. The owner accepted Step 3 on the evidence available.

## Production UI observations (owner-provided screenshots)

- **Editor:** `evidence/Step 3/production-visual-20261124/editor-whitley-park-page-692.png`. Page 692, 20 March 1828, Source img2840. Whitley Park renders as IMAGE Fragment 84, Image ID 3. The selected supplementary IMAGE Fragment 2334 references the same Image ID 3; the owner confirmed its Marquee is in the correct original source position. The selected fragment and source-page highlight are visible. Other adjacent image fragments share Image ID 3.
- **Reader:** `evidence/Step 3/production-visual-20261124/reader-whitley-park-1828-03-20.png`. Same day; Whitley Park image and caption render, adjacent transcription is present, source image/highlight and surrounding fragment ordering appear correct. No legacy raw HTML is visibly substituted for the image.
- Screenshots provide representative UI verification, not a screenshot of all 71 converted records.

## Source logs (private, do not copy unredacted to public Git)

Owner-provided Cygwin terminal notes, in execution order:

1. `note(20261124-182005).txt` — 11 tests PASS, live production dry-run 71 + DEFER 1564 and dry-run evidence saved.
2. `note(20261124-182344).txt` — matching mars/backup snapshot and maintenance isolation.
3. `note(20261124-190759).txt` — production APPLY_COMMITTED_DATABASE_PASS_MQTT_REPLAY_PENDING.
4. `note(20261124-192028).txt` — production POSTFLIGHT_DATABASE_PASS_MQTT_NOT_CHECKED.
5. `note(20261124-192136).txt` — production maintenance reopen.
6. `note(20261124-192350).txt` — container state, synchronise/republication, successful RPCs.

The last log contains **plaintext sign-in credentials and authentication tokens**. Do **not** commit or circulate it unchanged. Rotate the exposed password/revoke live sessions as appropriate, preserve only redacted evidence, and separately track credential logging as a security issue. The downloaded ZIP deliberately excludes this raw log.

## Acceptance and outstanding work

The feature owner explicitly stated **“I accept Step 3 of 0028-FEAT”** on 24 November 2026 after viewing the successful production Editor and Reader screenshots. Step 3 is therefore **CLOSED**, as accepted. Step 4 remains OPEN: consolidate final inventory/journal reconciliation, document Fragment 1564 and 0029 implications, record exact Git/deployment/evidence identities, perform closure review, and obtain separate formal feature closure approval before moving directories.

Do not infer missing command receipts or checksums from this summary; retain/reconcile actual private execution evidence in the feature directory.
