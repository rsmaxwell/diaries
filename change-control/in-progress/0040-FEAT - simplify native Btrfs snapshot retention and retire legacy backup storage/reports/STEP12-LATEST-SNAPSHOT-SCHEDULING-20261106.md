# 0040-FEAT Step 12 — Restore latest-snapshot scheduling semantics

**Status: source correction PREPARED, not deployed.** Manual simplified transfer and matching parent records were accepted on 6 November 2026. The legacy journal was archived; the old systemd timer remains stopped. No changes on `mars` or `backup` have been made by this package.

## Evidence and finding

The 6 November source backlog inventory (evidence `Step 12/raw-logs/step12-source-backlog-20261106-160214.txt`) counted **121** source snapshots newer than the agreed parent `20261101-150004Z`, oldest `20261101-160039Z`, newest at inventory `20261106-160001Z`.

The existing 03:30 UTC daily timer was previously configured to run `btrfs-native-push --latest`, selecting the **newest** validated source snapshot. The simplified sender instead used `choose_next` to select the **oldest** eligible newer source snapshot. With hourly creation and once-daily invocation, this would fall further behind indefinitely.

## Selected behaviour

Restore the previous daily **latest** policy by choosing the newest eligible source snapshot in `choose_next`. The sender still transfers a single incremental Btrfs snapshot per invocation using its pinned agreed parent; receiver Btrfs UUID/read-only checks, parent lineage, state readback, locks, error handling, prior pin and receiver-pruning-disabled state are unchanged.

This is a **fast-forward**, not a replay of every hourly snapshot: older intermediate recovery points are not copied to the receiver as part of this catch-up. The previously established daily off-site policy is preserved. Hourly local snapshots remain on `mars` according to local retention and remain subject to local pruning. A successful transfer advances the agreed parent directly to the selected newest source snapshot.

## Files and source provenance

The proposed Playbooks code ZIP contains only:

- `roles/btrfs-replication/files/btrfs-simplified-replication.py`
- `roles/btrfs-replication/tests/verify-0040-simplified-replication.py`

Basis: uploaded `playbook-sources-20261106-111342.zip`, with original runtime SHA256 `9be64295a6b6807df0fcd33d924b7a6549959f2a03dcab2953dcf0ac77fa6297`. Proposed runtime SHA256 `cfa8a696b36eb49935d518cfd2c99d38e28fe3fbbfaa7a0faa6618a485e2fd36` **only if exactly these edits are applied to the bundle baseline**.

**Important:** the live Playbooks checkout on `mango` has uncommitted edits in both these paths (and both readmes). Do not copy the ZIP over these files wholesale. The feature-local `tools/step12-latest-snapshot-selection.patch` is a minimal Git patch. Use `git apply --check` on `mango` first. If the patch conflicts, retain the local edits and inspect differences before a merge; never reset the working tree just to satisfy the patch. Recompute the source SHA256 after an accepted merge; it may differ from the proposed SHA256.

## Source regressions

Tests run on a copy of the uploaded Playbooks source with the focused patch applied (not against the modified `mango` checkout):

- `verify-0040-simplified-replication.py` — **20 tests PASS** (select newest, reject unsafe newest, ignore symlink/non-subvolume, no newer, plus existing transfer/recovery cases)
- `verify-0040-simplified-protection.py` — **3 tests PASS**
- `verify-0040-agreed-parent-prune-guard.py` — **11 tests PASS**
- `verify-0040-prune-source-selection.py` — **PASS**
- `verify-0040-step12-3-shared-retention.py` — **PASS**
- Python syntax and `git diff --check` — **PASS**

## Required operational gates (not yet executed)

1. Apply/merge small patch into existing `mango` Playbooks changes; review `git diff` and run consolidated regressions on the **actual** checkout.
2. Ansible `--tags simplified-agreed-parent --check --diff` against `mars,backup`: inspect binary-only planned changes, no scheduling or pruning changes. Deploy on both and check installed hashes equal the **actual** edited Playbooks source.
3. Verify source and receiver agreed-parent states still equal `20261101-150004Z`, and inspect the newest eligible source snapshot as a read-only Btrfs source with matching lineage. Run **one** controlled `sudo -n /usr/local/bin/btrfs-simplified-replication sender cycle` from `mars`; verify parent/prior equality on both hosts. If it fails, stop and review, do not loop or bootstrap.
4. Preview and deploy only `--tags scheduling` on `mars` to activate `/usr/local/bin/btrfs-simplified-replication sender cycle` at 03:30 UTC; verify service/timer status, no unexpected pruning or source binary replacement. Do not enable receiver pruning.
5. Preserve raw terminal and Ansible evidence under this feature in Diaries; reconcile Windows/mango evidence copies and update acceptance records before closing Step 12.

Rollback for the program edit: reinstall the accepted prior executable if needed while leaving scheduled activation disabled. Do not revert the agreed-parent state or automatically resume legacy replication. Do not delete source or receiver snapshots, receipts or the archived legacy journal.
