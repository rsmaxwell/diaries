# Step 02 — Deployment, recurrence and diagnostic evidence (2026-10-21)

## Decision and scope

**Native-prune identity correlation: ACCEPTED.** A naturally scheduled native prune recorded the exact IDs of two deleted subvolumes; both were subsequently listed by Btrfs as `<stale>` qgroups. The earlier legacy-Snapper exact-ID matches remain accepted. The mechanism by which the Btrfs kernel retains these qgroups and the `backup` manager's `unexpected_output` symptom are **not yet resolved**. Consequently overall Step 02 remains **IN PROGRESS**, while Step 03 safety design may begin without authorising mutations.

## Controlled source change and acceptance gates

The Playbooks change introduced `native_prune_subvolume_id(path)` in `roles/snapshots/files/btrfs-snapshot-manager.py`. It calls `btrfs subvolume show` before deletion, requires exactly one positive `Subvolume ID`, logs `subvol_id=...` and fails closed if no unambiguous ID exists. The dry-run path is unchanged. A native-prune regression and existing manager/qgroup regressions passed earlier on `mango` (operator evidence discussed before these latest captures; preserve test output independently).

An initial standalone `snapshots.yaml` dry-run showed **two** proposed changes: executable (expected) and `/etc/btrfs-snapshot-manager.json` (unacceptable). The latter would have removed the writer lock and Diaries verification barrier. The stand-alone playbook originally called `snapshots` directly; `local-backup` passes those host-specific values via its `include_role` invocation. This defect was corrected by routing the standalone launcher through host-specific role context and setting the launcher to `--check --diff` by default, with explicit `--apply` for deployment. Source verification on `mango` passed: shell syntax, launcher host-context regression, Ansible syntax, and `git diff --check` (`note(20261021-100750).txt`).

The **corrected** `./scripts/snapshots.sh mars` check run proposed only the snapshot-manager executable change: `mars ok=28 changed=1 failed=0` (`note(20261021-101108).txt`). The JSON config and systemd units were `ok`, with no diff. The explicit `./scripts/snapshots.sh mars --apply` then succeeded: `mars ok=30 changed=1 failed=0` (`note(20261021-101417).txt`). The manager's deployment preflight showed valid Diaries verification (`backupId=20261021-003106Z`), `complete_timestamp_sets=61`, `incomplete_timestamp_sets=0`, `qgroups_total=189`, `qgroups_stale=41`, no qgroups under deletion. The separate `mars` runtime check passed Python syntax; all three create/native-prune/legacy-prune timers remained enabled (`note(20261021-101500).txt`). The subsequent `--check --diff` reported **changed=0**, failed=0, verifying idempotency (`note(20261021-101725).txt`). No `backup` changes were applied.

The operator provided source bundles `diaries-sources-20261021-110146.zip` and `playbook-sources-20261021-110142.zip`; documentation authored against the former. **Git commit IDs for these new Playbooks changes and their final commit are not established in these logs.**

## Decisive natural deletion-to-stale correlation

Source: `note(20261021-101854).txt`, `mars`, 2026-10-21 at **10:15:09 UTC**, from `journalctl -u btrfs-snapshot-prune.service`:

| Source | Snapshot timestamp | Deleted subvolume ID | Subsequent qgroup inventory | Limit |
|---|---|---:|---|---|
| `@data` | `20261019-100002Z` | **20920** | `0/20920 <stale>` | `3.64TiB` |
| `root` | `20261019-100002Z` | **20919** | `0/20919 <stale>` | `none` |

The journal also reports `Deleted 1 complete timestamp sets`. This is a natural scheduled operation, **not a manually triggered experimental deletion**. The same subsequent inventory explicitly marks the two exact IDs `<stale>`. Counts changed from **41 stale** at deployment preflight to **43 stale** following that deletion (qgroups total 189 at both points; qgroups under deletion 0). This establishes persistence through the observed post-deletion inventory, but **not** whether the kernel might reconcile them later or how long they persist. It does not independently quantify recurrence on `backup`.

Previously accepted Snapper matches: `20189` (19629), `20237` (19677), `20261` (19701), each stale with `3.64TiB` max-referenced limit. Thus both native prune and legacy Snapper deletion paths can leave an observable stale level-0 qgroup on `mars`. A common Btrfs quota/subvolume lifecycle issue is a **hypothesis**, not a proven kernel bug or proof that specific userspace code is innocent.

**Monitoring caveat:** after reaching 43, `btrfs-snapshot-manager status` still returned `qgroups_status=ok` because the configured warning threshold is 100. This threshold policy is not an adequate substitute for tracking count/delta and age. The `backup` manager's `qgroups_status=unavailable;reason=unexpected_output` remains separately unresolved.

## Safety, remaining Step 02 work and next decision

No qgroups, quotas, snapshots, replication parentage, receipts, retention policies, OS installations or kernels were manually altered for the diagnostic. The one authorised deployment changed the installed manager executable on `mars`, not its configuration or timers. Source changes should be committed after operator review, with Git revision evidence recorded.

Still required before **formal Step 02 closure**: establish a bounded, parser-safe diagnosis of `backup`'s actual `unexpected_output` (including its invocation and format) and finalise confidence/limitations of qgroup persistence. Step 03 can prepare non-mutating safety design and read-only preflight in parallel. **Do not infer that native qgroup cleanup is safe from the correlation alone.**
