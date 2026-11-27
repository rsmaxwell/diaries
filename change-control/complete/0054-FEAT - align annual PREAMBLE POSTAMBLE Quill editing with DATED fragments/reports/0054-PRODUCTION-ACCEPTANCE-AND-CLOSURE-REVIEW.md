# 0054-FEAT — Production acceptance and formal closure review

**Prepared:** 27 November 2026  
**Status:** CLOSED — formal closure approved by owner on 27 November 2026.

## Scope and outcome

The change aligns DATED, PREAMBLE and POSTAMBLE Quill toolbars; retains safe hyperlinks and blocks new inline-image insertion; preserves supported Quill formatting in the Angular editor preview and Java Reader; displays selected diary identity; and initialises annual year from the earliest DATED fragment in the selected diary. The existing diary/year association of PREAMBLE/POSTAMBLE remains unchanged.

## Source revision manifest

| Repository | Commit | Purpose |
|---|---|---|
| Diaries parent | `84921a2` | Pins Client/Reader and records 0054 evidence |
| `diaries-client` | `aa6493557771f3d58c67db2842f9ff5978fe48d2` | Shared toolbar and annual editor |
| `diaries-web` | `18b18c2c090e78fd3c3ae102df869527c5e4aa58` | Safe Quill formatting in Reader |
| `diaries-responder` | `a49c6abd0ce005d58eb516770f6515313e40cdf6` | Unchanged |

All three changed repositories were pushed to their GitHub `main` branches successfully (user terminal evidence 27 Nov 2026 at 15:14). The Responder was not changed for 0054.

## Automated and development acceptance

- Final client script `tools/verify-step-3-final.sh`: Git capture 0, Angular tests 0, Angular build 0, overall PASS. Detailed logs and results are stored under `evidence/step-3-final-verification/`.
- Reader formatting/security regression tests and `installDist`: exit 0 (27 Nov 2026). The prior accepted development test and build evidence remains applicable.
- Development browser acceptance: shared controls, PREAMBLE save/reopen/cancel, Reader rendering of fonts, sizes, lists, colours and combinations, hyperlink navigation, inline-image protections, ordinary text paste, diary/year usability. Temporary test fragments were reported cleaned up by owner.

## Production release and operations evidence

| Component | Before | After on `pluto` | Verification |
|---|---|---|---|
| Client | `rsmaxwell/diaries-client:0.0.9-build-81` | `rsmaxwell/diaries-client:0.0.9-build-82` | `healthy` |
| Reader | `rsmaxwell/diaries-web:0.0.9-build-10` | `rsmaxwell/diaries-web:0.0.9-build-11` | `healthy` |
| Responder | `rsmaxwell/diaries-responder:0.0.9-build-87` | Unchanged | `healthy` |

The Jenkins pipeline outputs identified Client build-82 and Reader build-11 image tags. The supplied excerpts did not include complete Jenkins job receipts or immutable image digests. Ansible `bash scripts/diaries.sh` was executed on `mango`; recap `ok=51 changed=3 unreachable=0 failed=0 skipped=13`, exit 0. Docker inspection on `pluto` showed Client, Reader, Responder, Mosquitto and PostgreSQL healthy on 27 Nov 2026. These are observed deployment facts; do not infer immutable digests from tags.

## Production browser smoke — owner acceptance

**27 November 2026: Owner explicitly reported that all four requested browser checks PASSED:**

1. DATED, PREAMBLE and POSTAMBLE use matching Quill controls, without inline-image button.
2. Annual editor identifies the selected diary and initialises its year correctly.
3. Reader displays existing annual content, including supported rich-text formatting.
4. Normal DATED navigation and text fragment display continue to work.

This is owner-reported visual acceptance, not an automated browser transcript. No further production data changes were requested for these checks.

## Rollback

If rollback is required, restore the two prior tags in `playbooks/roles/diaries/defaults/main.yaml` on `mango` (Client `0.0.9-build-81`, Reader `0.0.9-build-10`); keep Responder `0.0.9-build-87`. Deploy through the normal `scripts/diaries.sh` process, verify containers and perform the four production smoke checks. Preserve unrelated working-tree edits on `mango`. The old Client and Reader images were confirmed present on `pluto` before deployment; availability at rollback time must be rechecked. No database restore or migration is part of 0054 rollback.

## Deferred issue

The cross-diary annual PREAMBLE/POSTAMBLE concept (e.g., the calendar year 1830 across two physical diaries) is intentionally deferred. See `reports/0054-DEFERRED-CROSS-DIARY-ANNUAL-CONTENT-DESIGN.md`. It is not a closure blocker.

## Remaining formal gate

- [x] Development acceptance and release verification.
- [x] Git commits and publication.
- [x] Jenkins image tags recorded and Playbooks deployment completed.
- [x] Deployed images and container health confirmed.
- [x] Four production browser checks owner-accepted.
- [x] **Owner explicitly authorised formal closure of 0054-FEAT on 27 November 2026.**
- [x] Status and steps marked CLOSED; feature moved to `change-control/complete/`, preserving evidence and rollback references. Closure commit/push is a separate Git operation.

**Closure approved and directory moved on 27 November 2026.**
