# 0037-FEAT Step 4 — Formal closure decision

**Date:** 2026-10-19  
**Status:** **CLOSED — read-only inventory and plan mode accepted**  
**Next:** Step 5, adversarial regression testing.  
**Destructive legacy deletion:** **NOT AUTHORISED**.

## Objective and scope

Implement and demonstrate read-only legacy Snapper discovery, source validation, unified retention coverage and text/JSON planning. Preserve existing scheduled native `create`, `prune` and `run` semantics; no legacy deletion mechanism or scheduler change was introduced under this step.

## Source and host evidence (observed on 2026-10-19)

- Playbooks `roles/snapshots/files/btrfs-snapshot-manager.py` updated on `mango`, with `legacy-plan` CLI. Native manager verification passed on `mango`, as did feature-local selection, empty-config, CSV-format, and timezone regression checks run from Cygwin via `mango`.
- On `mars`, targeted Ansible `copy` of the executable to `/usr/local/sbin/btrfs-snapshot-manager` returned `CHANGED` and preserved its previous version as `/usr/local/sbin/btrfs-snapshot-manager.240746.2026-10-19@18:21:17~`. Deployed SHA-1 (reported by Ansible): `f24862555ba55648d47e5e88b86944c7566d01de`; file size 43,269 bytes, root:root, 0755. This is a **deployment file checksum**, not a Git commit identifier.
- Snapper `root` maps to `/media/usb` and is empty: no numbered snapshots or `.snapshots` directory. Snapper `@data` maps to `/media/usb/@data` and has 25 numbered snapshots.
- The live Snapper CSV uses `number` and date strings such as `2024-05-26 13:00:20` without a timezone. The host timezone was independently observed as `Etc/UTC`; parser checks now accept timezone-less values only on a verified UTC host, while normalising explicit offsets.
- Regression evidence: modern and historical CSV variants, ambiguity rejection, empty configuration, missing/symlink snapshot directory rejection, valid UTC-naive date acceptance, non-UTC and unknown timezone rejection, and explicit offset normalisation all passed.

### Live `mars` read-only plan

Command:

```sh
sudo btrfs-snapshot-manager legacy-plan --legacy-map root=root --legacy-map @data=@data
```

Observed summary: `LEGACY PLAN READ-ONLY native=57 native_keep=57`.

| Inventory / decision | Count |
|---|---:|
| Complete native timestamp sets | 57 |
| Retained native sets | 57 |
| Numbered `root` Snapper snapshots | 0 |
| Numbered `@data` Snapper snapshots | 25 |
| Legacy `KEEP` | 17 |
| Legacy `WOULD-DELETE` | 8 |
| Legacy `EXCLUDED` | 0 |

**Eight advisory candidates in configuration `@data`:**

| ID | UTC timestamp | Plan decision |
|---:|---|---|
| 19605 | 2026-09-28 00:00:38 | WOULD-DELETE |
| 19629 | 2026-09-29 00:00:12 | WOULD-DELETE |
| 19677 | 2026-10-01 00:00:03 | WOULD-DELETE |
| 19701 | 2026-10-02 00:00:25 | WOULD-DELETE |
| 19725 | 2026-10-03 00:00:31 | WOULD-DELETE |
| 19773 | 2026-10-05 00:00:07 | WOULD-DELETE |
| 19869 | 2026-10-09 00:00:00 | WOULD-DELETE |
| 19885 | 2026-10-09 16:00:06 | WOULD-DELETE |

The 17 `KEEP` entries include the 2024 and 2025 historical coverage snapshots and `@data` #19886 (2026-10-09 17:00:01 UTC), retained as `LATEST_LEGACY_ANCHOR`. The plan terminates with `NO DELETION AUTHORISED`.

**Interpretation:** These are read-only selection results from the current inventory and clock, **not** individually approved deletion candidates. Retention decisions may change on later runs. No snapshots were deleted by this plan, and no permission for future deletion is implied.

## Compatibility findings addressed during Step 4

1. Rejecting empty `root` when `.snapshots` did not exist; now permit absence only if Snapper lists no numbered snapshots (still reject unsafe symlinks).
2. Snapper CSV `number` rather than `#`; now accept both while rejecting ambiguous numeric headers.
3. CSV date strings with no offset; now interpret as UTC only after host timezone validation, otherwise fail closed.

## Formal acceptance / boundaries

**Step 4 CLOSED** on the strength of source regressions, safe targeted deployment, and successful live read-only plan on `mars`. Existing native pruning and scheduler behaviour has not been changed by the new command; no independent timer-state re-audit is claimed at this step. The `backup` diagnostic-parent discrepancy captured in Step 1 remains an unrelated documented limitation and is not claimed fixed.

Proceed with Step 5 adversarial regression testing, followed by later safety and operator authorisation gates. Guarded legacy deletion and live pruning remain explicitly outside Step 4.

## Artefact containment

Store test harnesses, reports, transcripts and scratch output only inside this feature directory; permanent manager source resides under the Playbooks role. No feature-specific temporary tools should be promoted to normal Playbooks paths. Raw operator captures may remain locally ignored by Git; this Markdown record preserves the audited results without committing bulky logs.
