# 0040-FEAT — Accelerated integration: receiver inventory/plan lock coherence

## Source change

Receiver `receiver-inventory` and `receiver-plan` now take the snapshot-manager lock followed by the existing exclusive receiver `writer.lock`, as receive coordination does. The read-only plan refuses an unresolved `.receiver-prune-pending.json` deletion journal.

No receiver deletion permission or timers were enabled; `receiver-prune` still refuses execution. This is an incremental hardening change, **not completion of the production receiver deletion transaction**.

## Local verification

`receiver-lock-coherence.py`: all four checks passed, including lock order, release order, pending-journal refusal, and disabled deletion. Historical Step 3B, 3C, 3D, 3G, 3I, 3J, 3K and receiver-root preflight regressions were also run on the merged source; all returned success. Source Python compilation passed.

## Remaining gates

Source-side persistent pin must be proven non-releasable while a receiver transaction relies on it; the receiver needs a fully gated on-host executor holding `writer.lock` through the Btrfs/receipt transaction, and recovery verification. Current production receiver plan had 19 retained, 0 candidates. Do not enable receiver pruning or remove existing receipt/snapshot storage.

## Change control

0040-FEAT Step 3 remains OPEN. This report is evidence for an accelerated integration increment, not authorisation to prune.
