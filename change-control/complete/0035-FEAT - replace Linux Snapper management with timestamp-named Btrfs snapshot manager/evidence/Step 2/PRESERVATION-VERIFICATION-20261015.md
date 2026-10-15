# 0035-FEAT Step 2 — mars source-preservation gate (2026-10-15)

**Status: CLOSED — 2026-10-15 (read-only source-preservation gate).**

Step 1 established a working timestamp-named manager on mars: 53 complete `root`/`@data` snapshot sets, zero incomplete sets, verified schema-2 production backup `20261015-003023Z`, hourly creation and quarter-past pruning timers enabled, legacy Snapper timeline/boot/cleanup timers disabled. At capture, the `20261015-030004Z` @data source UUID was replication-protected, matched the most recent accepted off-site receipt, and `20261013-171228Z` was checkpoint-held. These are the observed invariants, **not approval to change retention or prune historical data**.

The Step 2 Playbooks verification adds an explicitly read-only capture of the source whole-subvolume boundary, nested subvolumes, snapshot UUID/read-only flags, holds/pins, scheduler state, installed configuration and lock-related process inventory. The source-contract checker checks that the existing manager retains cross-filesystem rejection, managed timestamp filtering, read-only creation, rollback, complete-set pruning and replication/checkpoint holds.

## Accepted live evidence — 15 October 2026

Executed on `mango`: `python3 verification/0035-step2/verify-source-contract.py` reported **PASS** for same-filesystem validation, timestamp filtering, read-only native creation, snapshot rollback, set-based pruning, replication protection, checkpoint hold protection, writer-lock integration and the Step 2 source-preservation contract. `ansible-playbook verification/0035-step2/capture-mars.yaml --ask-vault-pass` completed with `mars: ok=2 changed=0 unreachable=0 failed=0`.

Observed `mars` Btrfs `/media/usb` filesystem UUID `72d1d8ea-900e-4fca-837f-1b1febec036c`; `/media/usb/@data` source subvolume ID 260 and UUID `fc4585b5-1649-b94c-bcb6-a9253c9cf080`. The installed manager reported **52 complete** paired `root,@data` timestamp sets, **0 incomplete**, and a valid production verification marker for backup ID `20261015-003023Z`. The capture observed `ro=true` / `Flags: readonly` for sampled recent snapshots, the held `20261013-171228Z` recovery checkpoint, and the `20261015-030004Z` replication parent. The checkpoint JSON UUIDs matched the inspected `root` and `@data` subvolumes; the replication-protection JSON referenced `@data` UUID `6f44e0e0-1968-6e4d-a3bd-9f77d71e9a47`, also confirmed in the Btrfs inventory. Creation and pruning timers were enabled/active (hourly at `:00` and `:15`). Writer and manager lock paths were present. No transfer was identified by the capture's process inventory.

**Scope qualification:** the nested historical `@data/.snapshots` subvolume (ID 262) was observed. The capture did not exercise a send stream or prove nested subvolume contents are included; preserve this as a replication-scope consideration for later work. Source-contract tests establish code safeguards, not a new destructive live prune or an active-transfer concurrency test. Existing numeric Snapper snapshots remain outside Step 2 cleanup authority.

**Disposition:** Step 2 preservation/verification acceptance satisfied; formally CLOSED. No manager deployment, restore, snapshot deletion, pruning, retention alteration, or Docker image build occurred. Subsequent changes to received snapshot identity/retention remain under Step 3 and later gates.

**Evidence attachment:** `mars-preservation-20261015-083123.txt` (complete supplied console transcript).
