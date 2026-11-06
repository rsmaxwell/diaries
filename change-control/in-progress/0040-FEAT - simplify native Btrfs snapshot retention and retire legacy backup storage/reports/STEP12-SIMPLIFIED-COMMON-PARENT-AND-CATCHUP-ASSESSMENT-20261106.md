# 0040-FEAT — Step 12 common-parent evidence and catch-up assessment

**Date:** 6 November 2026 (UTC). **Decision:** live common parent **IDENTIFIED**, source and receiver installation-only **ACCEPTED**, operational bootstrap and cutover **OPEN**.

## Corrected snapshot identity evidence

The earlier `MISSING` lines in pasted direct-host commands did not prove snapshot deletion: the subsequent cross-host inventory verified both original snapshots. Read-only inventory confirmed seven common snapshot names: `20261013-171228Z`, `20261018-165453Z`, `20261023-030037Z`, `20261029-030003Z`, `20261030-030033Z`, `20261030-170009Z`, `20261101-140039Z`. The newest is suitable as the initial simplified parent:

| Property | `mars` source | `backup` received |
| --- | --- | --- |
| Snapshot | `20261101-140039Z` | `20261101-140039Z` |
| UUID | `69ef9a57-50ff-9a4e-92ed-8f10560ab1f2` | Native receiver UUID `37dcf2fc-8af2-444c-97b4-b0598b1766dc` |
| Received UUID | `-` | `69ef9a57-50ff-9a4e-92ed-8f10560ab1f2` |
| Flags | `readonly` | `readonly` |

The pre-existing `.agreed-parent.json` files on both hosts still establish `20261030-170009Z` (`a9b78fb9-4da6-cf4f-b242-13909f574193`); both simplified files were absent at inspection. Preserve these historical states and independent October recovery checkpoints. There is **no basis** for a full reseed or a claim of lost source snapshots.

## Current legacy scheduled failures

The legacy native sender completed an incremental transfer and receipt for `20261101-140039Z` on 1 November. The 03:30 scheduled sender failed on 2, 3, 4, 5 and 6 November when its receiver invocation returned status 1. Source-side systemd logs contain the remote command but not the receiver's specific rejection message. The actual `btrfs-native-push-receiver.py` `validate()` will reject, among other conditions, an existing `.agreed-parent-transfer-pending.json` marker, destination collision or invalid parent receipt. **No particular cause is confirmed yet.**

The feature tool `tools/verify-0040-step12-legacy-receiver-readonly.sh --run` checks the exact `mars` → `backup` route in **validation-only mode** (deliberately omits `--accept`) and lists legacy transaction marker metadata. It changes no Btrfs subvolume, state file or systemd configuration. Never delete a pending journal merely because it blocks the legacy receiver; first reconcile it against real state.

## Daily catch-up issue and candidate correction

The accepted prototype chose the oldest eligible newer source and handled **one** candidate per scheduled invocation to guarantee deterministic retries of the same failed candidate. With hourly source snapshots but one daily 03:30 sender invocation, this **cannot catch up** after normal operation or missed runs: new snapshots are created faster than they are transferred.

A focused Playbooks correction is prepared, **not yet deployed or operationally accepted**: retain oldest-first selection but process a bounded number (maximum 96) of *distinct successfully confirmed* candidates in one scheduled invocation. Each success updates receiver then source, with Btrfs identity/state readback; the **first failed candidate ends the invocation without immediate retry**. Next run selects that same oldest failed candidate, retaining the already accepted incomplete cleanup/retry semantics. A new `sender cycle --max-transfers 1` option supports one-candidate controlled real-host verification before activating unattended catch-up. The correction has 21/21 targeted source-level tests locally; the user must run those against the actual `mango` Playbooks checkout and review the updated install-only Ansible diff before redeployment.

## Remaining gates

1. Run the read-only legacy receiver diagnostic and examine any pending journal state. Do not remove or overwrite state based on filenames alone.
2. Apply and verify the targeted Playbooks catch-up correction. Reinstall the simplified binary with existing source service **inactive** (`active_enabled=false`). Verify file hashes again.
3. Revalidate the common parent identities and no blocking legacy marker; bootstrap the simplified parent on both hosts using the installed sender's `bootstrap` command only after inspecting diagnostic evidence.
4. Run a controlled one-candidate live replication (`sender cycle --max-transfers 1`), verify the source/receiver state identities, then decide whether to enable the simplified 03:30 service.
5. Leave receiver pruning disabled; preserve legacy binaries, state and historical checkpoints for rollback.

**Step 12 and 0040-FEAT remain OPEN.** The accepted Nov 5 disposable real-Btrfs test is not repeated unchanged; the catch-up correction needs only focused regression and its one-candidate live operational validation.

## Raw evidence

- `evidence/Step 12/raw-logs/note(20261106-112019).txt` — seven common snapshots and Btrfs identity of newest verified parent.
- `evidence/Step 12/raw-logs/note(20261106-112059).txt` — source prune extract, Nov 1 successful push and Nov 2–6 receiver failures.
