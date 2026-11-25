# Owner-reported GUI acceptance, 25 November 2026

Environment: Windows local development editor with two editor windows viewing the same text Fragment. Owner confirmed **“Yes. All 6 tests passed”** after exercising the new client correction.

1. Window A: editing causes Save active and exclusive lock acquired — PASS.
2. Window B: displays “Locked by another window” and editing prevented — PASS.
3. Window A: original character restored without Save — PASS.
4. Window A: Save becomes inactive and lock automatically releases — PASS.
5. Window B: unlock becomes visible — PASS.
6. Window B: can edit, acquire lock, then restore text and release lock — PASS.

This is a transcription of the owner's acceptance statement and original test protocol, not a claim that a separate automated GUI session or direct MQTT/DB inspection was executed.
