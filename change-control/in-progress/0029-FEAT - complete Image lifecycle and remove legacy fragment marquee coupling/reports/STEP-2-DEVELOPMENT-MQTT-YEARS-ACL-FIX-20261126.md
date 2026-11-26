# 0029-FEAT — Missing years ACL: development MQTT fix (2026-11-26)

## Evidence and cause
After verified development DB conversion (49 receipts, 49 archives, 51 IMAGE Fragments), responder startup attempted to publish retained annual PREAMBLE topics under `diaries/years/<diaryId>/<year>/preamble/<fragmentId>`. MQTT Explorer did not show `diaries/years/`. Live development broker's `/mosquitto/config/aclfile.txt` has no `diaries/years/#` rules. Broker log (notice level) did not show an explicit rejection; missing ACL is a strongly supported cause, not yet confirmed by a post-fix test.

## Change
Add `topic read diaries/years/#` for diaries-client and diaries-web; `topic readwrite diaries/years/#` for diaries-responder. Preserve existing privileges and deny clauses. Do not change health account.

The development Compose binds `config/mosquitto/aclfile.txt` read-only from repo root. Restart **only** `diaries-development-mqtt` after updating ACL (this does not remove its named persistence volume); restart the IDE responder afterwards to republish missing PREAMBLE topics. Restart the reader if required for subscription refresh. Never clear retained MQTT messages or restore the database.

## Acceptance
After restart verify years branch in MQTT Explorer and keys `diaries/years/1/1828/preamble/1`, `diaries/years/1/1829/preamble/387` (if their DB IDs are correct); verify `diaries/fragments/598`, `606`, and that obsolete 84 is absent. Verify actual retained payloads and reader/editor display. Keep Step 2 OPEN until observed.

## Source provenance
Based on uploaded 2026-11-25 Diaries source bundle; verify against current uncommitted Windows checkout before applying. Playbooks deployment ACL is in a separate ZIP, for later deployment with the updated application; do not deploy production changes now.
