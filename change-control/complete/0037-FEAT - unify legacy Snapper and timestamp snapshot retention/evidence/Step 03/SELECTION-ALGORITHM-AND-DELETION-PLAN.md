# Step 3 — Selection algorithm and deletion-plan contract

**Date:** 2026-10-19  
**Decision:** CLOSED — specification only; no legacy pruning enabled, no host mutation.  
**Inputs:** Step 1 baseline; Step 2 compatibility mapping; Playbooks `roles/snapshots/files/btrfs-snapshot-manager.py` (19 October source bundle).

## 1. Invariants and implementation boundary

1. The native complete-set selection is calculated **exactly as before** with `retention_keep_set()` on timestamp-named complete `root`+`@data` sets, then replication pins and checkpoint holds. Legacy records cannot remove any native `KEEP`, change native deletion candidates, or relax the existing complete-set and whole-plan preflight.
2. A legacy timeline snapshot supplies **only its verified Btrfs source's** historical coverage, never a coordinated two-source restore point. `backup` received subvolumes, receipts, and receiver retention never participate.
3. Snapper snapshot `0`, manual snapshots, `pre`/`post`, unknown types, bad metadata, and unowned entries never supply replacement coverage and never become automatic deletion candidates.
4. All timestamps and buckets are UTC. ISO week key includes ISO week-year. No filesystem mutation is permitted in report-only mode.
5. For each mapped source, preserve the newest eligible legacy timeline snapshot as the migration recovery anchor even when a native bucket overlaps. Protect legacy snapshots younger than the configured minimum age, and any independently discovered explicit hold/important marker (unknown marker semantics mean BLOCKED).
6. Any uncertain source identity, incomplete native set, unresolved pins/holds, inventory failure, or failed mandatory validation **fails closed**: no authorized delete plan, and no deletion of any record. Display all known records as BLOCKED with the failure cause; do not generate executable candidates.

## 2. Snapshot identities, discovery, and verification

**Native identity:** `(native, timestamp, source)`; a native set is the ordered collection of all configured sources sharing the timestamp. Existing native scanner provides complete/incomplete state and existing path/readonly validation. Never infer a complete set from coincident Snapper snapshots.

**Legacy identity:** `(legacy, snapper_config, numeric_id, verified_source_identity)` where verified source identity includes Btrfs filesystem UUID plus subvolume ID / canonical configured path matching the appropriate native source. Read Snapper `SUBVOLUME` and independently verify path and mount boundary; snapshot pathname must match `.snapshots/<id>/snapshot` owned by the validated config, and snapshot must be a read-only Btrfs subvolume. Reject symlink escapes, duplicate IDs, missing or mismatched metadata, and unparseable dates. Use stable, timezone-aware creation metadata, not the locale-formatted `snapper list` display. Recheck filesystem and snapshot identity during later deletion execution.

**Inventory consistency:** Acquire the existing snapshot-manager lock for a full source/legacy plan. Collect native inventory and protections, then legacy configuration metadata and numbered inventory. A mismatch between Snapper list and on-disk snapshots must be reported and block deletion. Snapshot command failures must never be interpreted as an empty population. Record collection time, configuration fingerprint and stable inventory fingerprint; a later mutating step must revalidate rather than trust an old plan.

## 3. Deterministic decision procedure

Given UTC `now`, current policy limits and the verified inventory:

1. Validate the native preflight and all complete/incomplete sets. Resolve replication pins and checkpoint holds with the same fail-closed rules as today's manager. Derive native `KEEP` from existing native GFS, newest set, minimum age, pins and holds. Preserve native-only candidate/validation logic independently.
2. For every locally managed source/config pair, verify actual `SUBVOLUME` mapping and Snapshot `0` handling. Categorize each numbered legacy entry by Snapper type, cleanup method, provenance, source identity, creation time, read-only status, and protection metadata.
3. Form eligible legacy timeline singles only from strictly validated `single`/`timeline` records. For each source form the *coverage pool* from those singles plus native **retained** complete sets for that source; do not include native deletion candidates as coverage anchors.
4. Each nonzero retention tier visits the newest `N` **distinct populated UTC buckets** of the pool, choosing exactly one representative per bucket. A retained native set takes precedence whenever present in that bucket; otherwise choose the most recent eligible legacy snapshot. Where multiple retained native sets share a bucket, use the newest. When legacy records share a bucket, choose the newest UTC instant; resolve exact ties deterministically by `(config, numeric_id)` in ascending lexical/numeric order. A representative selected by any tier is required. Zero limits select no buckets.
5. Take union of all legacy tier representatives with newest legacy recovery anchor per source, minimum-age entries and any explicitly protected entries. NOTE: a bucket occupied by a native retained set can make a legacy snapshot redundant **only** for that tier; check every tier independently before candidate classification.
6. Classify native complete sets and legacy entries with one primary status plus *all* reason codes; ordered priority: global unsafe/block => `BLOCKED`; manual/pre-post/unmanaged => `EXCLUDED`; retained/protected/age/anchor/tier => `KEEP`; otherwise validated redundant legacy timeline => `WOULD-DELETE`. Native `WOULD-DELETE` retains the existing complete-set decision; report its roots together, never relabel one half as independently removable.
7. Compute an advisory plan only. A `WOULD-DELETE` label grants **no permission** to delete. Future Step 6 must require a separate disabled-by-default opt-in, allow-listed configs and per-ID approval/revalidation.

The coverage-pool bucket membership, newest-N selection and native-preferred representative must be implemented exactly as above, and tested for cases in which a historical legacy-only bucket falls just outside a limit after a more recent native bucket is added. This matches the existing newest-N-**populated** semantics rather than attempting to preserve a fixed number of legacy-only buckets.

## 4. Machine-readable plan (proposed schema v1)

One structured JSON document (stdout option or artifact inside `reports/`; no output under production source). UTF-8, stable sorted entries; no timestamps generated from local timezone. Required envelope:

```json
{
  "schemaVersion": 1,
  "mode": "read-only",
  "decision": "VALID",
  "generatedAtUtc": "2026-10-19T12:00:00Z",
  "host": "mars",
  "policy": {"hourly": 48, "daily": 14, "weekly": 12, "monthly": 24, "yearly": 5, "minimumAgeMinutes": 30},
  "nativeFloorPreserved": true,
  "configurationFingerprint": "sha256:<hex>",
  "inventoryFingerprint": "sha256:<hex>",
  "summary": {"nativeKeepSets": 0, "nativeWouldDeleteSets": 0, "legacyKeep": 0, "legacyExcluded": 0, "legacyBlocked": 0, "legacyWouldDelete": 0},
  "errors": [],
  "entries": []
}
```

Every `entries[]` record has `class` (`native-set` or `legacy`), `source`, `id` (timestamp string or numeric Snapper ID), `createdAtUtc`, `status`, `reasonCodes` (sorted strings), and `buckets` (tier to bucket UTC key for all selected tiers). Legacy entries additionally have `snapperConfig`, `sourceIdentity` (Btrfs filesystem UUID and source subvolume identity), `snapshotPath` and `snapperType`/`cleanup`; native set entries have all `snapshotPaths`. Retain a deterministic `sortKey` (source, creation time descending, class, ID) and print display labels alongside structured data. No passwords, secrets or entire configuration contents in plan artifacts.

**Status vocabulary:**

| Status | Meaning | Example codes |
|---|---|---|
| `KEEP` | Required for any GFS tier or absolute protection | `GFS_MONTHLY:2026-09`, `GFS_YEARLY:2025`, `NATIVE_FLOOR`, `LATEST_NATIVE`, `LATEST_LEGACY_ANCHOR`, `MINIMUM_AGE`, `REPLICATION_PIN`, `CHECKPOINT_HOLD` |
| `EXCLUDED` | Not covered by automatic legacy policy and cannot displace another | `SNAPPER_ZERO`, `MANUAL`, `PRE_POST`, `UNKNOWN_CLEANUP` |
| `BLOCKED` | Unsafe/uncertain; no deletion permitted | `SOURCE_IDENTITY_MISMATCH`, `INCOMPLETE_NATIVE_SET`, `INVENTORY_ERROR`, `UNREADABLE_PROTECTION`, `UNSAFE_PATH`, `NOT_READ_ONLY`, `UNRESOLVED_METADATA` |
| `WOULD-DELETE` | Validated, unprotected candidate; advisory only | `REDUNDANT_AFTER_UNION`, `NATIVE_GFS_CANDIDATE` |

Global `decision` is `VALID` or `BLOCKED`, never partially valid for execution. For `BLOCKED`, `summary.*WouldDelete*` must be zero and all otherwise removable entries become `BLOCKED`; `errors[]` names the controlling issue. Keep the original advisory reasons in a separate `diagnostics` field if useful, but not as actionable status.

## 5. Human-readable listing and tool exit semantics

Render `POLICY`, `NATIVE-FLOOR`, `MAPPING`, `PLAN`, per-entry `KEEP|EXCLUDED|BLOCKED|WOULD-DELETE`, and `SUMMARY`. Print scope (`mars` local only), verified `root/@data` map, snapshot counts and reasons including UTC bucket tier keys. Display Snapper config plus numeric ID (not ID alone), and complete native-set membership. Output order deterministic for a fixed inventory, policy and injected `now`. JSON `generatedAtUtc` is deliberately excluded from the comparison of deterministic decision records.

Recommended future CLI: `plan --include-legacy --format json|text`; existing `prune --dry-run` must continue to work and preserve native-only output/exit behaviour until deliberately extended. Reporting may be invoked without a legacy deletion option. No option named `--dry-run` should accidentally enable deletions. Successful complete, valid read-only plan exit `0`; invalid or incomplete plan nonzero (`2` recommended for validation/preflight failures; `3` for inventory/external command failures); argument/config errors continue to use existing manager conventions until Step 4 implements compatibility tests. A failed plan must not silently return `0` or misleading `WOULD-DELETE` entries.

## 6. Future deletion revalidation contract (not implemented in Step 3)

The operator approves exact `(host, config, ID, source identity, snapshot UUID)` identities from a current plan. Before every Snapper deletion in Step 6: acquire exclusive manager lock; refresh all native sets and pins/holds, source identity and complete legacy inventory; recompute selection using fresh `now`; recheck path, ownership, readonly flag, protection metadata, anchor and GFS reasons; reject if plan fingerprints or approved identity no longer match. Call `snapper -c <config> delete <ID>` only after those checks; stop on first failure, re-inventory/replan for next ID. No direct Btrfs deletion of legacy Snapper snapshots. Confirm acceptable Snapper metadata and current config; never delete snapshot `0` or pre/post pairs. Consider immutable audit evidence before/after.

## 7. Worked decision examples and tests for Step 5

- September 2026 legacy monthly with native retained only in October: `KEEP GFS_MONTHLY:2026-09` if within newest 24 populated months.
- October 2026 legacy and retained October native, but the legacy is the newest historical legacy: `KEEP LATEST_LEGACY_ANCHOR` despite native month overlap.
- Two October legacy entries, native retained in October, neither age protected nor newest legacy: possible `WOULD-DELETE`, **only** after checking all daily/weekly/yearly tiers and protections.
- Last legacy yearly 2025 and retained native 2026: retain 2025 when selected by the yearly tier.
- Zero daily limit: no daily representative; other tiers and protections still apply.
- Same UTC instant: a retained native anchor wins; deterministic legacy ID tie otherwise.
- Snapper `pre`/`post` or malformed locale date: `EXCLUDED`/`BLOCKED`, cannot supply coverage.
- Native incomplete set or unreadable replication receipt: global `BLOCKED`, zero executable candidates.
- Snapper config missing or `SUBVOLUME` resolves to wrong UUID: global `BLOCKED` when legacy mode is requested.
- Legacy inventory command returns nonzero or times out: global `BLOCKED`, not an empty list.
- No legacy snapshots: native selection and status remain exactly as previous native-only behaviour; plan shows zero legacy records.

## 8. Acceptance and closure

- [x] Algorithm written with native retention floor and per-source legacy GFS mapping.
- [x] Tie-break, minimum age, zero limits, unknown classes and all global fail-closed cases specified.
- [x] Human/JSON deletion-plan schema and status reasons specified.
- [x] Later approval, per-delete refresh, Snapper deletion mechanism and rollback boundary specified.
- [x] No production code, scheduler or snapshots modified.

**Step 3 decision: CLOSED (specification-only).** Next: Step 4 read-only inventory and plan-mode implementation, with legacy deletion disabled throughout.
