# 0037-FEAT — Step 13 formal closure: production documentation and housekeeping

**Decision: CLOSED — PASSED WITH RECORDED DEFERRED HOUSEKEEPING (2026-10-20).**

The production source and operating guidance are promoted to permanent Playbooks roles; successful real full-playbook reconciliation and subsequent idempotency are demonstrated. This closes Step 13 only, **not** the 0037 feature (Step 14 outstanding). No snapshot, qgroup, hold, receipt, or host-side helper deletion is authorised by this record.

## Acceptance evidence

| Gate | Observed result |
| --- | --- |
| Source regression | Publisher, fixed schema-2 manifest, transaction, mars fixed receive, diaries pull and production tooling regressions PASSED on `mango` |
| Original manifest checksum regression | Source is the accepted 0036 implementation, SHA-256 `d9490f706f427b11a5b5758b9a818e3218aa0624e5e659ea6187b2518fdfbc73`; historical 0033-only hash assertion updated. The test's `frozen 0033` success wording is stale and should be corrected as documentation hygiene |
| Source file modes | `production-complete-dataset.py` and `complete-dataset-manifest.py` corrected to executable in Playbooks source |
| Program reconciliation | `mars` installed publisher SHA-256 `ae5431fdc56eba7fea4411103d869f6f913e87f91c0c4500a4cc5185e89b64ea`; independent verifier SHA-256 `d9490f706f427b11a5b5758b9a818e3218aa0624e5e659ea6187b2518fdfbc73` |
| Python bytecode | `__pycache__/` and `*.pyc` excluded from backup script rsync, no remaining generic script synchronisation diff |
| Directory permissions | Two tasks originally alternated 0750 → 0755; rsync directory chmod corrected; observed host state `750 richard:richard /home/richard/scripts/backup` |
| Real deployment | Earlier full untagged run `ok=64 changed=2 failed=0`; final full `./local-backup.sh` run `ok=64 changed=0 unreachable=0 failed=0 skipped=17`, demonstrating repeat-run idempotency |
| Docker key | Real playbook execution reports `ok`; check mode had reported `changed`, treated as check-mode artefact |
| Native data | 60 complete timestamp sets, zero incomplete, qgroups 155 total / 8 stale / 0 under deletion, status `ok`; valid verified production dataset `20261020-003106Z` |
| Timer state | Native create/prune and legacy prune timers `enabled`; historical Snapper timeline, boot and cleanup timers `disabled` |
| Housekeeping inventory | No `step13-predeployment-*` directory found under `/home/richard` at scan depth 2; three root-owned legacy helper files remain in `/root/scripts/backup/` |

## Residual findings and explicit disposition

1. **Retained root-owned helpers**: `/root/scripts/backup/diaries-pull.py`, `/root/scripts/backup/complete-dataset-publisher.py`, `/root/scripts/backup/complete-dataset-manifest.py` exist. Their safe removal is **not established** by the inventory alone; check current cron/systemd/manual references and `diaries_pull_cleanup_legacy_root` gate before a separately approved deletion. No cleanup claimed. Carry this to Step 14 / follow-up.
2. The `find /home/richard -maxdepth 2` check is limited; it is **not** a comprehensive audit of all temporary material on `mango`, `mars` or `backup`. Additional broad host hygiene is deferred, not silently marked clean.
3. Latest source bundles do not include Git metadata or deployed host inventory file. **Final Git revision IDs, clean working-tree status, and current host-vars contents not independently verified**; reconcile in Step 14 before final feature closure. The earlier reported Playbooks HEAD `95303d96ae5a8c9970fb287b7c5aa3a20deaa701` predates the final local edits and is not asserted as the final promotion commit.
4. Natural 08:20 daily timer trigger not independently observed in Step 13. Step 12 accepted successful direct execution of installed oneshot unit; do not claim an observed natural calendar firing.
5. The production source checksum manifest should be refreshed when final Git commits are made. Step 13 source hashes in this package are based on the latest *uploaded* Playbooks bundle, not on live repo state.

## Decision and next gate

**Step 13 CLOSED — PASSED, with deferred housekeeping explicitly inventoried.** Rationale: residual files are retained and non-blocking, with no cleanup action needed for safe operation; production deployment, configuration and source regression gates all passed. Step 14 must reconcile Git revisions, remaining root-owned helper disposition, and overall feature acceptance before closing 0037-FEAT or relocating the change-control directory.

Original operator log evidence: user-provided `note(20261020-164854).txt` (real run `changed=2`), `note(20261020-171149).txt` (real run `changed=0`), and `note(20261020-171342).txt` (host housekeeping inventory). This ZIP records a verbatim copy of the last two outputs for traceability.
