# Step 03 — Historical Snapper evidence and disposable stale-qgroup reproduction

**Date:** 2026-10-21. **Defect:** 0039-DEF. **Status:** evidence accepted for observed results; Step 03 OPEN. **Scope:** original terminal evidence stored under this defect, with no production modification authorised.

## Historical evidence on `backup`

- Installed Btrfs userspace is **btrfs-progs 5.16.2**; Snapper is **0.9.0**. Configurations `root` (`/`) and `@data` (`/@data`) both existed, with `QGROUP=""`, `SPACE_LIMIT="0.5"`, `FREE_LIMIT="0.2"`, timeline and cleanup policies. `snapper-cleanup.service` logs show cleanup phases for both configurations during 1–10 October 2026, but do not list precisely which subvolume IDs were deleted.
- Seven surviving pairs, sampled from October 2023 through October 2026, have adjacent Btrfs IDs (`@data`, `root`): (310,311), (4598,4599), (22851,22852), (41067,41068), (53427,53428), (55023,55024), (55455,55456). The independently saved `backup` manifest confirms **all seven `@data` qgroups have max_rfer 1.00TiB**, while **all seven `root` qgroups have no limit**. This directly corroborates the alternating historic limited/unlimited pattern.
- Ansible host inventory on `mango` supplied `btrfs_subvolume_limit: 1099511627776` for `backup` `/@data` (exactly 1 TiB); this establishes a matching historical configured value, **not** proof this role limited every Snapper snapshot.
- The read-only `backup` check on 21 October observed **no pending subvolume deletions**, **no quota rescan in progress**, Btrfs on `/dev/sda2` mounted with `subvolid=5`. Device size **1.81 TiB**, free estimated **296.87 GiB**. There is no evidence quantifying how much space qgroup reconciliation might reclaim.

The validated production inventory has **29,571 qgroups** on `backup`, including **15,475 unmatched investigation-only** and **13,962 unmatched limited-protected**. The originating workflow for each record is not individually proven. No unmatched record is thereby eligible for deletion.

## Disposable experiment on `mango`

- Host: Ubuntu 24.04.4, kernel 6.8.0-142-generic, btrfs-progs 6.6.3. Preflight verified loop support, 48 GB free, and unused paths.
- **Disposable only:** backing file `/var/tmp/diaries-qgroup-reproduction/filesystem.img` (512 MiB), loop device `/dev/loop0`, mount `/mnt/diaries-qgroup-reproduction`, label `diaries-qgroup-test`, filesystem UUID **8346c9fd-6dbb-45b6-94dc-e8b4728e2757**. Quotas were enabled **only on this disposable filesystem**. The initial enable triggered a transient running-rescan warning; a subsequent query confirmed idle.
- **Experiment A (unlimited):** created read-only `snapshot-a`, subvolume ID **257**, no qgroup limit. After `btrfs subvolume delete` and `btrfs subvolume sync` had confirmed deletion, `0/257` remained with `<stale>` label.
- **Experiment B (limited):** created read-only `snapshot-b`, subvolume ID **259**, explicitly set `max_rfer=1 TiB` on the disposable qgroup. After successful deletion and synchronisation, `0/259` remained `<stale>` with its **1.00TiB limit preserved**.
- Final joint verification: both `snapshot-a` and `snapshot-b` paths absent; no pending deletion; quota rescan idle; `0/257` remained `<stale>`, max_rfer `none`, and `0/259` remained `<stale>`, max_rfer `1.00TiB`. **Both ultimately reported 0.00B referenced/exclusive** (earlier immediate post-deletion output reported 16.00KiB). This distinction shows usage accounting settled later while metadata remained.

The test **reproduces the stale limited and unlimited qgroup symptoms** under mango's kernel and userspace. It does **not** demonstrate the exact underlying Btrfs mechanism, persistence after an arbitrary future interval, identical behaviour on backup's older software, or safe removal of any production qgroup. Historical Snapper origin is **strongly supported**, not proven for all 29,437 records.

## Preservation and acceptance

The original terminal logs were placed under `evidence/Step 03/investigation/` and `evidence/Step 03/reproduction/mango/`, with original names and byte-identical source contents. See `STEP03-REPRODUCTION-EVIDENCE-SHA256.txt` for the hash of every added log. Existing production manifests, safety assessment JSON and protection records are **not replaced** by this package.

**Acceptance:** proof of the observed two stale-qgroup states, paired historical examples and safe experimental isolation. **Not accepted:** production deletion eligibility, an approved qgroup-destruction script, any quota rescan, an OS change, or completion of Step 03. The disposable filesystem **must remain mounted and intact** until an explicit cleanup/rehearsal gate; it has not been dismantled in these records.

## Next gated work

1. Verify evidence file hashes and no unintended diff after applying this package; keep raw logs separate from operational source.
2. Design a fail-closed, offline remediation plan with explicit exclusions and a distinct disposable **qgroup-destruction** rehearsal. Include lost-state/non-atomic rollback constraints, side effects, btrfs-progs version differences and required independent approval.
3. Before any real modification, require fresh live qgroup/subvolume/protection/replication identity checks and a documented stop/rollback gate. Historical unmatched classification is not sufficient.
4. Preserve the loopback image until its own explicit cleanup and evidence acceptance. **0039-DEF and Step 03 remain IN PROGRESS.**

## Subsequent reconciliation rehearsal

The originally preserved reproduction logs remain unchanged. Subsequent **Gates A–D passed** on the same disposable filesystem; the two stale qgroups were then destroyed, while active qgroups survived. See `STEP03-RECONCILIATION-GATES-A-D.md` and its separate raw-log checksum manifest. Do not treat the original stale-qgroup observation as a description of the later current filesystem state.
