# Step 2 — Compatibility and coverage mapping

**Date:** 2026-10-19  
**Decision:** CLOSED — design specification only; no production pruning or Snapper deletion authorised.  
**Input baseline:** Step 1 `BASELINE.md`, 19 October 2026 source bundles, native `btrfs-snapshot-manager.py`, current role template, and operator Snapper listing.

## 1. Scope and explicit non-equivalence

This model is limited to local snapshots on **mars**. Native snapshots are complete coordinated sets covering `root` and `@data`; the old numbered Snapper snapshots are per-configuration snapshots, not complete native sets. Their time coverage may be counted **per source only**, never as evidence of a recoverable coordinated `root` + `@data` checkpoint. `backup` received snapshots, replication receipts and receiver retention are excluded. `mango` is an operator/evidence host, not a deletion target.

| Inventory class | Current observed count | Source coverage | May fill legacy GFS bucket? | May displace a required native set? | Deletion in Step 2? |
|---|---:|---|---|---|---|
| Native timestamp set on mars | 57 complete (capture-specific) | coordinated `root` + `@data` | Native anchor for matching source buckets | Not applicable | No |
| Snapper `root` numbered | 0 | `root` only | Yes, if later discovered and validated | **Never** | No |
| Snapper `@data` numbered | 25 | `@data` only | Yes, after config/source identity validation | **Never** | No |
| Received timestamp snapshot on backup | 13 observed | received `@data` source | **No** | **Never** | No |
| Unknown, orphan, unparseable or unmatched record | unbounded | unknown | **No** | **Never** | No |

Counts are point-in-time evidence, not invariants. Re-inventory before every plan and deletion. The operator Snapper list has not been stored in the latest source archive; Step 1 references its conversation capture.

## 2. Required configuration-to-source mapping

`root` Snapper configuration is a *candidate* mapping to the native `root` source and `@data` Snapper configuration to native `@data`. **Names alone do not prove identity.** The implementation must read each Snapper config's `SUBVOLUME` and filesystem identity and compare it with the native role's configured `sources` after canonical resolution and Btrfs source/subvolume verification. Confirm mount identity and that snapshots are actually owned by that Snapper configuration. Refuse to plan deletion on mismatch, missing configuration, symlinks escaping expected roots, or ambiguous mounting. Avoid assuming `root` refers to `/` on mars or that `@data` refers to the receiver's `@data`.

Do not map `backup` Snapper configurations into mars source coverage, even if names match. `backup`'s previous verification failure (`/@data/diaries-mars-replica/pluto`) remains an unrelated outstanding diagnostic issue; correct observed receiver path is `/@data/mars-received/@data/`.

## 3. Eligible snapshot kinds

- `single` + `timeline` + Snapper-owned numbered snapshot: eligible for *coverage calculation* **only after** validated config and snapshot metadata. Inclusion is not deletion permission.
- `single` + manual or unknown cleanup: **protected/excluded from automatic deletion** unless later explicitly opt-in and accept separately. It may be displayed for recovery awareness but must not be used to make another snapshot expendable.
- `pre` and `post` snapshots: **protected/excluded** pending an independently designed pair-aware policy. Do not delete one member, merge two records, or count an unvalidated pre/post snapshot as a replacement coverage anchor.
- Number `0`: Snapper's current state, **not a historical snapshot**; exclude from all retention calculations.
- Unknown type, invalid ID/date, malformed metadata, missing read-only snapshot, unresolved provenance: **EXCLUDED/BLOCKED** with reason; never use as a deletion justification.
- Existing held/pinned native timestamp sets: remain non-deletable according to existing protection contracts, independent of this feature.

## 4. Time and bucket semantics

Match the existing native algorithm: native names use UTC `YYYYMMDD-HHmmssZ`; all legacy creation timestamps must be converted to aware UTC instants from reliable metadata (not informal locale-dependent text). The hourly key is `(UTC year, month, day, hour)`; daily key `(UTC year, month, day)`; weekly key **ISO week-year and ISO week number** (Monday start); monthly key `(UTC year, month)`; yearly key `(UTC year)`. Current defaults are hourly **48**, daily **14**, weekly **12**, monthly **24**, yearly **5**, minimum age **30 minutes**, subject to actual host configuration.

As in the current manager, for each nonzero tier select the **most recent** representative of each of the **newest N distinct populated buckets** (not the last N wall-clock intervals). Bucket tiers are unioned, so one item can represent several tiers. Gaps are not filled by fabricating snapshots. Sort by UTC instant descending with deterministic class/config/ID tie breaks; native retained sets win ties and all source-local collisions. Repeatable dry-run output must show UTC time and the applicable bucket reasons.

## 5. Two-layer retention decision

**A. Immutable native floor:** Run the existing `retention_keep_set()` over complete native timestamp sets only, and preserve its results, current newest native set, minimum-age sets, all replication pins and checkpoint holds. Existing incomplete-set fail-closed behaviour remains in force. No legacy record may change a native `KEEP` into a native `DELETE`. This intentionally prioritises safety over reducing the native set count.

**B. Legacy per-source coverage:** For each validated Snapper-owned source/config, run the same GFS bucket policy over comparable coverage: (i) already-required native `KEEP` sets as immutable anchors for that source, plus (ii) eligible legacy timeline singles for that source. For each tier, a kept native anchor representing a populated bucket wins over any legacy in that bucket; otherwise choose the most recent eligible legacy snapshot in the bucket. Take the union of required legacy representatives across all tiers. Always preserve the newest eligible legacy snapshot for each source **until explicit separate recovery-anchor acceptance**, to avoid accidentally removing the last legacy-era recovery point. Preserve all legacy records younger than the configured minimum age. Note that an older legacy entry can remain needed for e.g. the yearly tier even if its monthly bucket is already covered by a native record.

**C. Candidate eligibility:** Legacy snapshot is *potentially* redundant only when it is validated `single/timeline`, is not a chosen per-source bucket representative, has no age/anchor/explicit hold protection, and passes all independent deletion preconditions. Covered by a native set means *time-bucket coverage*, not byte-identical contents or cross-source restore equivalence. The overlap does not justify an unconditional delete.

**D. Native deletion:** Not altered by Step 2. Do not use a legacy snapshot to free or replace any native complete set. Actual deletion remains disabled until the later approval gates.

### Worked examples

| Situation | Required behaviour |
|---|---|
| September `@data` Snapper monthly vs October native | Keep September legacy if it satisfies a historical monthly bucket not covered by a retained native anchor |
| October legacy `@data` and October native retained | Prefer native for October bucket; legacy may be redundant, except other-tier/anchor/minimum-age protections |
| Legacy `root` and legacy `@data` both exist for a date | **Not** a complete coordinated native timestamp set; evaluate two source histories independently |
| Annual 2025 legacy `@data` and only October 2026 native | Keep 2025 history for yearly tier if eligible, not replace with unrelated 2026 checkpoint |
| Native set pinned by replication, and one legacy snapshot in same month | Native remains pinned; legacy needs all per-source coverage/protection checks before it can become a candidate |
| Snapshot is `pre` or `post` or manual | Exclude from automatic deletion; cannot justify deleting another historical point |
| Incomplete native timestamp set or unreadable protective state | Fail closed: no destructive changes and report diagnostic |

## 6. Boundaries and items for Step 3

Step 3 must turn these semantics into deterministic *plan records* with explicit `KEEP`, `EXCLUDED`, `BLOCKED`, `WOULD-DELETE` reasons per source and tier; model safe tie breaks and the chronology where native anchors are included only if already retained; define source identity validation, anchored newest legacy, policy zero limits, dry-run exit/error semantics, deletion flag separation, and restart-safe revalidation. Confirm on live mars that Snapper `SUBVOLUME` resolves to the intended Btrfs sources and inspect genuine Snapper metadata (including any important/userdata flags) before approving any deletion. Consider whether future retention windows should preserve multiple migration-era anchors; do not silently weaken the conservative newest-legacy rule.

## 7. Acceptance and closure

- [x] Legacy config candidates mapped conceptually, with required *runtime* identity verification specified.
- [x] Native set vs legacy per-source recovery coverage distinction documented.
- [x] Timeline, manual, pre/post, snapshot zero, unknown and protected cases specified.
- [x] UTC hourly/daily/ISO-week/month/year and native defaults recorded.
- [x] Recovery anchors and no-native-displacement rule defined.
- [x] Receiver, replication and production deletion boundaries preserved.

**Step 2 decision: CLOSED (design and compatibility mapping only).** Runtime mapping validation, algorithm implementation, deletions and host verification are deliberately allocated to later steps. No production mutation is authorised.
