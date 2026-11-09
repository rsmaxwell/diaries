# Step 02 — Scope and retention policy decisions

**Status: CLOSED — 23 October 2026 (policy decision only).** Source: `../../reports/STEP02-SCOPE-RETENTION-DECISIONS.md`; closure in `../../IMPLEMENTATION-STEPS.md`.

## Decisions accepted

- Steady-state manager and retention model: common Btrfs manager / retention selection; `mars` manages only `@data` source snapshots; `backup` manages received `@data` snapshots, never creates snapshots.
- Retention unchanged on both hosts: hourly **48**, daily **14**, weekly **12**, monthly **24**, yearly **5**, minimum age **30 minutes**. Retention does not override holds, protected parent or in-flight transfer guards.
- Approved eventual retirement includes legacy Snapper trees on both hosts, `backup` root `/.snapshots` (including APT-generated history), obsolete backup trees/configuration and unnecessary native `mars` root-snapshot population. Accepted loss of recovery history uniquely present in retired legacy trees, including pre-9 October 2026 points.
- Preserve source and receiver recovery holds, including `20261013-171228Z` and `20261018-165453Z`; preserve the native received dataset, receipts and valid common-parent lineage.
- No mandatory repeat full restore where existing accepted correctness evidence is sufficient.

## Explicit limits of approval

**No actual snapshot/legacy-data deletion approved.** Step 10 still requires a fresh, identity-specific list of subvolumes, UUIDs, active writers, coverage and risk. Step 11 needs separate explicit operator go/no-go. The operator decisions are documented in the Step 2 report; no new approval is implied by this evidence update.
