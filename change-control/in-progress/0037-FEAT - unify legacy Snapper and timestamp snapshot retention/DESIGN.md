# Retention and migration design — 0037-FEAT

## Starting point

`roles/snapshots/files/btrfs-snapshot-manager.py` enumerates complete timestamp sets and applies `retention_keep_set()` to only those sets. Its prune path validates and removes all managed source subvolumes in each selected set. Historic numbered Snapper `.snapshots/<id>` trees are intentionally excluded. Defaults are configurable hourly/daily/weekly/monthly/yearly plus minimum age. Replication protection and independent checkpoint holds must be preserved.

## Data model and safety boundary

Represent an inventory record with: host, filesystem identity, config/owner, physical path, source subvolume, snapshot ID/name, UTC creation time (and trustworthy provenance), read-only flag, snapshot kind (`native_complete_set`, `legacy_snapper`, `received_replica`, `unknown`), covered sources, protection flags, deletion interface, and validation issues. Capture Snapper metadata (`snapper list --columns ...` / XML or machine-readable formats where available), Btrfs subvolume metadata and config mappings; avoid parsing fragile human date strings without controlled locale and tests.

**Crucial coverage distinction:** Old numbered Snapper snapshots may capture `root` or `@data` separately and may contain single/pair pre/post snapshots. They cannot automatically substitute for a complete native multi-source timestamp set. Define retention coverage per managed source; do not silently treat incomparable records as identical. Designate protected recovery anchors independently of ordinary GFS buckets.

## Selection

- Build a canonical, validated inventory and determine which legacy snapshots are eligible for automated lifecycle handling. Leave everything else KEEP/EXCLUDED with reasons.
- Compute configured time buckets deterministically, with documented week boundary, timezone, ordering and tie-break rules consistent with the existing manager.
- Across **comparable coverage groups**, rank protected/complete native timestamp sets ahead of eligible legacy snapshots when choosing a representative in the same bucket, without breaking chronological GFS intent. Within the same class, prefer the most recent valid candidate. Never permit legacy coverage to displace required retention of native complete sets.
- Keep required safety anchors, newest native complete set, minimum-age records and all holds/pins. An eligible legacy snapshot becomes a deletion candidate only when no required retention or coverage role remains and its protections permit removal.
- Print deterministic KEEP, EXCLUDED, WOULD-DELETE and BLOCKED actions with multiple reasons and count totals before any deletion.
- Validate the complete candidate set before performing any deletion; recheck candidate identity and safeguards immediately before invoking Snapper. A failure aborts remaining work.

## Legacy deletion mechanism

Invoke `snapper -c <validated-config> delete <validated-id>` only on supported Snapper-owned snapshots after source/identity checks. Explicitly confirm Snapper deletion semantics for timeline, numbered pairs, cleanup metadata, snapshots configured as important or users' manual checkpoints. Never run a blanket numeric-ID range deletion or generic `btrfs subvolume delete` against Snapper trees. Ensure Snapper's native cleanup scheduling is not inadvertently re-enabled.

## Replication and hosts

`mars` is the primary candidate for integrated local legacy/native selection. `backup` received Btrfs snapshots and the `mars → backup` replication parent/receipt protections stay under their existing separate rules. Inventory of other hosts is read-only unless scope is explicitly amended. Neither replicated snapshot counts nor remote hold records can be interpreted as local Snapper retention coverage.

## Control flags and migration

Default behaviour is existing native prune policy + legacy reporting with **no legacy deletion**, until explicit configuration and runtime acceptance. Prefer a separate `legacy_snapper_retention.enabled` and `legacy_snapper_retention.allow_delete` (both false by default), with a validated allow-list of host/config/source scope; exact config names determined during implementation. Changes must remain backward compatible and fail closed on missing/malformed config.

## Hard failure cases

Unknown owner/config; unparseable time; incompatible filesystem; inconsistent sources; lost `root/@data` partner; active send/receive; invalid or missing pins/holds; incomplete native sets; disappearing/changed snapshot; Snapper command failure; missing access rights; candidate overlaps active or historically protected recovery point. No destructive action under uncertainty.

## Rollback

Stop integrated pruning and disable legacy delete opt-in, revert the Playbooks implementation/configuration, leave native timer ownership unchanged, and inventory retained snapshots. A deleted Btrfs snapshot cannot be restored by reverting code; recovery of a removed legacy snapshot is only possible from an independently existing verified recovery source. Therefore rollout requires dry-run review, approved candidate list and confirmed recovery coverage before first delete.

## Step 2 frozen interpretation

The authoritative compatibility matrix, coverage grouping, time-bucket semantics and native-retention floor for this feature are in `evidence/Step 02/COMPATIBILITY-AND-COVERAGE-MAPPING.md`. Any future implementation must preserve the existing native keep set independently before evaluating eligible legacy `single/timeline` snapshots per verified source. No name-only Snapper mapping, pre/post pair handling, or cross-host coverage assumptions are permitted.


## Step 3 selection and plan contract (2026-10-19)

The normative, reviewed algorithm and advisory deletion-plan schema are frozen in `evidence/Step 03/SELECTION-ALGORITHM-AND-DELETION-PLAN.md`. It preserves the native GFS `KEEP` floor, applies UTC newest-populated-bucket selection per mapped source, and requires fail-closed plan status and guarded future Snapper deletions. No production behaviour is changed by Step 3.
