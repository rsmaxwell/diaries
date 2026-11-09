# 0040-FEAT — Accelerated Step 3L disposable rehearsal

User accepted a faster, riskier schedule on 2026-10-23. The `mars` read-only preflight already passed. This package combines disposable subvolume creation, actual Btrfs deletion, and simulated interruption into one explicitly authorised stage.

Run from **Windows Cygwin** by streaming the feature script into **mars**: `ssh mars 'sudo python3 - --execute' < ".../tools/step03l-disposable-rehearsal.py"`. This modifies *only* a new `/media/usb/@data/0040-step03l-rehearsal` directory; it refuses if the directory already exists and preserves it for review. The rehearsal does not invoke the installed snapshot manager, native sender, receiver, or any production backup directories.

The test checks: a disposable read-only parent survives; one snapshot and receipt delete cleanly; interruption before real Btrfs deletion leaves both intact with a journal; interruption after real Btrfs deletion leaves receipt+journal for later recovery. It does **not** prove native send/receive receipt identities, production transaction integration, or durable crash recovery. These remain outstanding before production receiver deletion is enabled.

Never automatically retry an unsuccessful or interrupted rehearsal, because its directory intentionally remains. No cleanup until evidence inspection. Keep Step 3 OPEN.
