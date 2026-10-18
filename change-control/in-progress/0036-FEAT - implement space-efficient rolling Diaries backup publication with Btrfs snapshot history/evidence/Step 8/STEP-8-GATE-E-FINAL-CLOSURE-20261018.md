# 0036-FEAT — Step 8 Gate E final evidence reconciliation and formal closure

**Decision date:** 2026-10-18  
**Disposition:** **Gate E CLOSED — PASS; Step 8 CLOSED — PASS; 0036-FEAT CLOSED — PASS**.  
**Basis:** operator-supplied execution, verification and post-operation evidence reviewed in the Gate E sequence. This record is the controlling final disposition and supersedes earlier notes saying Gate E remains open.

## Acceptance chain

| Area | Accepted evidence | Result |
|---|---|---|
| Gate A/B/C | Inventory and rollback readiness; controlled fixed-path cutover on `pluto` and guarded fixed receive on `mars` | CLOSED |
| Gate D | Distinct unattended backup IDs `20261017-003102Z` and `20261018-003102Z`; manifests matched between `pluto` and `mars`; verified Btrfs snapshots `20261017-030007Z` and `20261018-030006Z`; accepted off-site incremental receipts | CLOSED |
| Gate E source safety | Compatibility-first variable aliases and preserved `DIARIES_0036_*` runtime interface; source regressions passed, including corrected legacy publication test | PASS |
| Gate E inventory-aware rendering | `pluto`: 10 OK; `mars`: 1 OK; zero changed/failed/unreachable; fixed-capture service, NAS and guarded pull selectors verified without deployment role execution | PASS |
| Gate E deployment | Approved Ansible apply on 2026-10-18: `pluto` 16 OK, 1 changed (pre-deployment unit copy), 0 failed; `mars` 5 OK, 0 changed/failed. Candidate unit equal to installed unit; fixed commands and timers preserved | PASS |
| Gate E Stage 1 | Six non-alias generations moved to reversible hold: three on each of `pluto` and `mars`; postcheck shows all six at `location=hold`; current repositories and timer status preserved | CLOSED |
| Gate E Stage 2 | Exact-target and manifest checks passed; both `diaries-backup.pre-0036-rollback` symlinks renamed to `.retired`; postcheck `before=retired`, `after=retired` on both hosts | CLOSED |
| Historical preservation | Both `20261016-003019Z` generation directories retained with SHA-256 `58e594a6327e20a0fe4800e2b24871458dfc7742cb217f2a7be136ba162ea6e4`; six held directories retained; no permanent deletion authorised | PASS |

## Final runtime state

- `pluto`: fixed production backup repository remains a real directory at `/home/richard/projects/diaries/data/diaries-backup`, with service commands `fixed-capture-preflight` and `fixed-capture`.
- `mars`: fixed receiver remains a real directory at `/media/usb/@data/backup/pluto/diaries-backup`, with guarded fixed-destination pull.
- Both old aliases now have the `.retired` suffix and still point to their preserved historical generations. Their original operational alias names are retired.
- Stage 1 hold is under `.diaries-backup-generations/.0036-retirement-hold/` on both hosts; 3 historical generations per host.
- No user-requested new complete restore, throughput benchmark, or further unattended cycle is necessary under the previously agreed Gate D acceptance criteria.
- No Docker rebuild, backup timer restart or backup dataset rewrite was part of Gate E retirement.

## Retirement vs deletion: explicit boundary

**Operational retirement is complete; permanent deletion is not part of 0036 closure.** The six held generations and both `20261016-003019Z` targets remain as historical recovery material. The two retired symlinks are intentionally kept for reversibility. Historical Snapper snapshot repositories, 0035 timestamp snapshots, replication protection markers and off-site received Btrfs snapshots/receipts remain outside the cleanup scope.

Follow-on housekeeping may later decide when and how to delete historical generations and consolidate Snapper/0035 retention under a separately approved, protection-aware process. An exact manifest match within a snapshot is **not** a complete payload validation or permanent retention guarantee. Do not implicitly delete these assets as a consequence of this feature's closure.

Legacy `publish` support and `DIARIES_0036_*` compatibility runtime keys remain intentionally supported; stable Ansible names were introduced without requiring a breaking runtime migration. Do not interpret closure as authorisation to remove compatibility code or rename deployed environment variables.

## Source-control reconciliation

Last **operator-confirmed clean, pushed baselines** before the subsequent Gate E source changes:

- Diaries: `eec87b9b1f63b1e64e3b8f0625eae53563926119`.
- Playbooks: `fd6345d824778009450c31ba926a3e351c0720eb`.

Subsequent applied Gate E changes and the present closure documents require local `git status`, review, commit and push by the operator on the separate Windows Diaries and `mango` Playbooks working copies. No later commit hashes have been supplied as evidence, and this record does **not** claim those commits already exist. This source-control administration does not negate the accepted operational Gate E results.

## Scope of formal closure

Steps 1–7, Step 8 Gates A–E and overall **0036-FEAT** are **CLOSED — PASS**, effective 2026-10-18, with historical retention/deletion and optional follow-on naming simplification deliberately deferred. Further destructive operations require separate approval and read-only preflight.
