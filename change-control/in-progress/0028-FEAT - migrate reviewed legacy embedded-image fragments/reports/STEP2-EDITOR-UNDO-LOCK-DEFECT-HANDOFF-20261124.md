# 0028 Step 2 — Separate Editor unlock defect handoff (24 November 2026)

## Finding

During isolated Angular Editor GUI acceptance for 0028, existing **Fragment 1252** (MARQUEE transcription, diary 3, Page ID 893) acquired a lock when a character was typed. In a second browser session it correctly appeared locked. Undoing or deleting the inserted character back to the original text did **not** automatically release the lock while the first session remained on the Fragment. Switching away from the Fragment after restoring text **did** release it. The owner confirmed both behaviours on 24 November 2026.

This is a general Editor lock-lifecycle defect. It was reproduced on a non-migrated transcription Fragment, and no evidence shows the 71 IMAGE conversions caused it.

## Disposition

- Track independently under **0053-DEF — Editor does not release Fragment lock when transcription is restored** (`../../0053-DEF - editor does not release fragment lock when transcription restored/README.md`).
- Owner agreed to defer its fix until after 0028. **No 0053 implementation is included in the 0028 image migration**.
- Known workaround: after returning text to its saved value, select another Fragment; the lock was observed to release. Do not navigate away with uncommitted edits.
- 0028 Reader/image/navigation/Marquee GUI acceptance evidence remains valid. This specific undo-to-original auto-release behaviour is **FAIL / tracked as 0053**, not incorrectly reported as PASS.
- Continue remaining 0028 acceptance and production approval separately; registering 0053 does not authorise production migration or close 0028.

## Evidence status

The defect is supported by the owner's interactive test report in the Diaries project conversation, not by an attached full console, RPC, MQTT or responder trace. Collect those traces when implementing 0053. Do not attribute a proven root cause to async locking without that evidence.
