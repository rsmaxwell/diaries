# 0037-FEAT — Implementation steps

Each step needs evidence in this feature's `evidence/Step NN/`, a result, changed-file inventory and explicit closure decision. No destructive production mutation is authorised simply by progressing through a step.

1. **Freeze baseline and scope.** Capture current Playbooks code/config, native GFS policy, all relevant Snapper configs/source mount identities, inventories, timers, receipt/pin/hold state on `mars`; record receiver boundary on `backup`. Read-only.
2. **Define compatibility and coverage mapping.** Map legacy Snapper configuration(s) to managed `root`/`@data` sources; document timeline/pre/post/manual cases, UTC/time bucket semantics and required anchors. Do not assume every legacy snapshot is equivalent to a complete timestamp set.
3. **Specify selection algorithm and deletion plan output.** Deterministic combined timeline, separate per-source coverage constraints, precedence, fail-closed cases, reasons and structured dry-run listing.
4. **Implement read-only inventory and plan mode.** Permanent reusable functionality to Playbooks only after review; experimental parsers and one-off dumps stay inside `tools/` and `reports/` here.
5. **Build adversarial regression tests.** Mixed generations, no legacy, all legacy, equivalent/non-equivalent scopes, mixed pre/post, pinned/held native, recent snapshots, incomplete sets, corrupt metadata, duplicate times, disappearing candidates, command failures, and preservation of former native-only behaviour when legacy mode disabled.
6. **Implement guarded legacy deletion.** Strict disabled-by-default opt-in, config allow-list, Snapper API/CLI, preflight and per-delete revalidation, abort-on-error, existing native-set delete protections unchanged.
7. **Run mango source regressions.** Syntax/static checks, manager regressions, retention simulation and integration tests with fake Snapper and Btrfs responses; no live deletion.
8. **Run mars read-only preflight.** Capture actual legacy/native population and proposed actions; reconcile candidate reasoning, source identity, capacity and recovery coverage. No prune.
9. **Stage Playbooks deployment with deletion disabled.** Verify idempotency, schedules unchanged, native behaviour preserved, `backup` receiver/parent boundaries respected, log output and fail-closed behaviour.
10. **Operator acceptance gate.** Review precise numbered legacy IDs, Snapper configs, restore options and protected anchors. Approve or reject **specific** first candidates. No unattended legacy deletion before this gate.
11. **Controlled live legacy prune pilot.** Only approved IDs, bounded count, on `mars`; pre/post state and filesystem verification; halt if invariants fail. Capture evidence and verify current replication state remains usable.
12. **Scheduler acceptance and rollback.** Decide deliberately whether to activate automatic legacy pruning; re-verify native snapshot and `mars → backup` behaviour without triggering unnecessary full transfer/restore. Roll back legacy opt-in if uncertain.
13. **Production documentation and housekeeping.** Promote only permanent source/test/config/doc changes into Playbooks. Remove temporary host-side assets, keep feature evidence under feature directory; complete `PROMOTION-MANIFEST.md`.
14. **Final reconciliation and close.** Compare feature acceptance criteria against collected evidence, enumerate exclusions/deferred work, record Git revisions, mark feature COMPLETE and relocate this feature directory under `change-control/complete/` only after acceptance.

**Build/deployment reminder:** this is predominantly a Playbooks Python/Ansible change. Do not build/publish Diaries client/responder/web Docker images unless a later, explicitly justified change actually affects them.

## Step 1 status (2026-10-19)

**CLOSED — baseline and scope frozen.** See `evidence/Step 01/BASELINE.md` and `reports/STEP01-CAPTURE-CHECKLIST.md`. Evidence includes native capture files and follow-up read-only operator outputs; a `backup` manager diagnostic path discrepancy remains documented and uncorrected. Proceed to Step 2 (compatibility and coverage mapping). **No deletion, scheduler change or production mutation authorised.**

## Step 2 status (2026-10-19)

**CLOSED — compatibility and source-level coverage model documented.** See `evidence/Step 02/COMPATIBILITY-AND-COVERAGE-MAPPING.md`. Legacy Snapper `root` / `@data` mapping remains conditional on validation of actual `SUBVOLUME` identity, not names alone. Existing native `KEEP` decisions are an immutable floor; eligible legacy timeline singles may fill per-source historical buckets. Manual, pre/post, unknown and snapshot zero are excluded from automatic deletion. `backup` replica population is not part of local combined retention. **No code deployment or snapshot deletion performed.** Proceed to Step 3.

## Step 4 status (2026-10-19)

**CLOSED — live read-only validation PASSED (2026-10-19).** Updated manager deployed on `mars` using a targeted Ansible copy with backup. Snapper compatibility corrections (empty `root`, CSV `number` header, host-verified UTC timestamps) passed regression checks. Live `legacy-plan --legacy-map root=root --legacy-map @data=@data` completed with 57 native complete sets, 57 native keepers, 25 legacy `@data` entries: 17 KEEP and 8 WOULD-DELETE; no legacy `root` numbered entries. No deletion authorised or performed. See `evidence/Step 04/STEP04-FORMAL-CLOSURE.md`. Proceed to Step 5 — adversarial regression tests; candidates remain advisory only.

## Step 5 status (2026-10-19)

**CLOSED — adversarial read-only planner regressions PASSED on `mango`.** The feature-local `tests/step05-adversarial.py` was streamed from Cygwin over SSH and executed with Python on `mango` against `/home/richard/playbooks/roles/snapshots/files/btrfs-snapshot-manager.py`. Operator evidence: **20 tests, all passed (OK), 0.011 s**; results captured locally under `evidence/Step 05/results.txt`. See `evidence/Step 05/STEP05-FORMAL-CLOSURE.md` and `STEP05-RESULTS.md`. The tested scope covers inventory, malformed metadata, duplicate numbers/mappings/timestamps, mismatched/unknown source, missing protections, incomplete native sets, anchors, native retention preservation, and absence of deletion calls. **No destructive actions, deployments or scheduler changes in Step 5.**

**Deferred explicitly to Steps 6–7:** adversarial revalidation immediately before deletion, disappearing candidates during deletion, and failing Snapper delete commands cannot be exercised until guarded deletion is implemented. A missing configured source can raise an unwrapped `FileNotFoundError`; this fails safely but diagnostic formatting should be improved before any deletion enablement. Step 6 remains not started, and legacy deletion is not authorised.

## Step 6 status — FORMALLY CLOSED (2026-10-19)

**CLOSED — source-level implementation and verification.** The guarded `legacy-delete` path was added to Playbooks source on `mango`. Operator-provided evidence from 2026-10-19 shows 14/14 simulated guarded-deletion tests PASSED via Cygwin SSH streaming, `python3 -m py_compile` successful, and the existing Playbooks native snapshot-manager verification suite PASS. See `evidence/Step 06/STEP06-FORMAL-CLOSURE.md`. This closure is strictly for source implementation; the new command has NOT been deployed to `mars` or `backup`, and no real deletion or approval file was authorised. Step 7 remains OPEN for full regression/integration verification.

## Step 7 status — FORMALLY CLOSED (2026-10-19)

**CLOSED — full source and integration regression passed on `mango`.** Operator execution of `tests/step07-run-from-cygwin.sh` on 2026-10-19 produced successful Python compilation, SHA-256 `3eb8717fdb06410943a2e9513dfc5f3e8b6892021bac0d741b58e2524bdff671`, native snapshot-manager regression PASS, Step 5 adversarial **20/20 PASS**, Step 6 guarded-deletion **14/14 PASS**, and CLI/scheduler source-isolation PASS. Raw captured output is `evidence/Step 07/results.txt`; formal closure is `evidence/Step 07/STEP07-FORMAL-CLOSURE.md`. The mocked `LEGACY DELETE` output is not a production deletion. No guarded deletion was deployed to `mars` or `backup` as part of this step.

## Step 8 status — FORMALLY CLOSED (2026-10-19)

**CLOSED — `mars` read-only preflight reconciled.** Captures under `evidence/Step 08/` confirm 57 complete native timestamp sets (0 incomplete, 57 keepers), 0 numbered legacy `root` snapshots and 25 legacy `@data` snapshots (17 KEEP, 8 WOULD-DELETE). Machine-readable JSON and text planning output agree with Snapper CSV identities. Host timezone and source mapping are consistent with UTC Btrfs layout; Diaries verification marker is valid. Native creation/pruning timers remain enabled and legacy Snapper timers disabled. See `evidence/Step 08/STEP08-FORMAL-CLOSURE.md` and `STEP08-RECONCILIATION.md`. No approval files or deletion actions were run. The manager's pin/hold safety preflight succeeded, but this capture is not an independent audit of each protection record or receiver health. Proceed to Step 9 only with deletion disabled.

## Step 9 status — FORMALLY CLOSED (2026-10-20)

**CLOSED — targeted Playbooks deployment to `mars` accepted with legacy deletion disabled.** Post-deployment SHA-256 matches `mango` source (`3eb8717fdb06410943a2e9513dfc5f3e8b6892021bac0d741b58e2524bdff671`), deployment rollback copy recorded, systemd units and Snapper inventories unchanged, 57 complete native sets with no native dry-run deletions, and legacy plan unchanged (17 KEEP, 8 WOULD-DELETE). The native list's two additions and two removals represent routine complete-set rotation. No legacy delete approval or execution. See `evidence/Step 09/STEP09-FORMAL-CLOSURE.md`. **Step 10 OPEN — exact operator acceptance required before any pilot.**

## Step 10 status — technical review completed (2026-10-20), OPEN pending acceptance

Fresh `mars` read-only capture reconciled: 58 native complete/retained sets, zero native dry-run deletion, 25 numbered legacy `@data` snapshots (16 KEEP, 9 WOULD-DELETE). Snapshot `19605` still qualifies as an advisory candidate, and its read-only Btrfs identity is verified. See `evidence/Step 10/STEP10-RECONCILIATION.md`. Independent receiver/recovery evidence and explicit one-ID operator approval or rejection remain outstanding; no legacy deletion authorised.

## Step 10 receiver evidence update (2026-10-20)

Independent read-only receiver capture reconciled. Fourteen read-only received subvolumes including `20261020-030026Z`, with a matching Mars replication pin and receipt metadata presence. `backup.service` and `user@0.service` are reported failed; assess their relevance before operator approval. Step 10 remains OPEN; no deletion authorisation. See `evidence/Step 10/STEP10-RECEIVER-RECONCILIATION.md`.

## Step 10 final status — CLOSED (2026-10-20)

The operator explicitly approved only `mars` / `@data` / Snapper ID `19605` for the controlled Step 11 pilot. Mars and independent backup receiver preflights were reconciled; failed historic service states were assessed as non-blocking. This supersedes the earlier interim Step 10 OPEN statements. No broad deletion mandate was granted.

## Step 11 status — FORMALLY CLOSED (2026-10-20)

**CLOSED — single authorised guarded deletion and independent post-execution reconciliation PASSED.** Snapper inventory performance initially blocked execution; `legacy_snapper_inventory()` was updated to call `snapper ... list --disable-used-space`. The modified shared manager on `mango` passed syntax, focused parser verification, existing native suite, Step 5 20/20 and Step 6 14/14 mocked regressions plus Step 7 isolation. The manager was deployed by targeted Ansible `copy` to `mars` only; installed SHA-256 `200998f4bdf129637025fd94730735d27919d48b1f47941b58846e408f2692c5`. One-ID executable approval for `19605` was checked along with subvolume UUID `489332dc-3b48-eb40-b59a-d9bd86cc9915`, ID `20165` and read-only status. Guarded manager output confirmed `LEGACY DELETE completed config=@data id=19605`. Post-deletion Snapper inventory contains 24 numbered legacy `@data` snapshots; `19605` absent, remaining 16 KEEP / 8 WOULD-DELETE; 58 native complete, 0 incomplete, 0 native prune candidates, 2 checkpoint holds, replicated pin `20261020-030026Z`, valid production dataset verification and all five Btrfs device error counters zero. No further deletions approved; there was no change to automation schedules, quotas or backup receiver.

Formal decision and verbatim evidence: `evidence/Step 11/STEP11-FORMAL-CLOSURE.md`, `evidence/Step 11/execution/operator-execution.txt`, `evidence/Step 11/execution/operator-post-verification.txt`, `evidence/Step 11/execution/SHA256SUMS.txt`. The former Step 10/11 OPEN wording above is chronological history and superseded by these final entries.

**Out of scope / follow-on:** assess and clean up approximately 16,000 stale Btrfs qgroups under a distinct safety/approval gate; no `btrfs qgroup clear-stale` performed. Do not treat this closure as approval for unattended legacy deletion or the eight additional WOULD-DELETE candidates.

## Supplemental Step 12 — qgroup metadata cleanup (2026-10-20)

**CLOSED — PASSED (quota metadata cleanup only).** The supplemental qgroup work arose after original Step 11; it is **not** original planned Step 12 above, which remains OPEN for scheduler acceptance/rollback. `mars`: stale qgroups 15,984→0; total qgroups 16,129→145. Native snapshot complete sets 58, incomplete 0, native prune candidates 0, both holds and replication pin retained; all device error counters zero. Verbatim operator preflight and cleanup logs retained in `evidence/Step 12/execution/`; formal record `evidence/Step 12/STEP12-RECONCILIATION-AND-CLOSURE.md`. Read-only original Snapper inventory performance verification pending separate measurement; do not claim improvement without results. No other snapshot pruning, scheduler change, or receiver mutation authorised.

## Step 12 unattended retention implementation staging (2026-10-20)

Operator requested unattended aging-out of both native timestamp sets and legacy Snapper snapshots. The native 08:15 UTC timer already prunes timestamp sets. Playbooks source changes stage a bounded, opt-in legacy-prune command (one legacy snapshot per run by default) under the same existing oneshot service; defaults off and not yet activated. See `evidence/Step 12/STEP12-UNATTENDED-PRUNING-STAGING.md`. Original Step 12 remains OPEN until runtime activation, verification and rollback acceptance.

## Step 12 scheduler acceptance and rollback — FORMALLY CLOSED (2026-10-20)

**CLOSED — PASSED.** Permanent `local-backup.yaml --limit mars --tags legacy-prune-units` deployment installed the guarded legacy pruning service and daily timer, passed check-mode first-install and repeat-run idempotency (`changed=0`), and activated the inventory opt-in. Native `btrfs-snapshot-prune.timer` remains hourly at `*:15`; `btrfs-legacy-prune.timer` runs daily at **08:20 UTC**, enabled and active. Former Snapper timers remain disabled. Native and legacy retention decisions remain separate and protected.

Two explicitly observed production systemd executions at **15:41:49–15:41:54 UTC** and **15:43:08–15:43:13 UTC** deleted only eligible legacy `@data` IDs **19629** and **19677**, one per invocation, each exiting `0/SUCCESS`. Post-state: **58 complete** native snapshot sets, **0 incomplete**, Diaries verification valid (`backupId=20261020-003106Z`), both holds preserved, **6 remaining** legacy deletion candidates, qgroups `151 total / 8 stale / 0 under deletion` (`ok`). Last systemd verification found both native and legacy prune timers enabled and active, the legacy timer next due **2026-10-21 08:20 UTC**.

**Scope and limitations:** the natural daily timer firing was not observed; manual oneshot executions exercise the exact installed service but do not prove the calendar trigger. `--max-delete 1` is **per invocation**, not per calendar day; two manual starts produced two deletions. No new end-to-end restore or full replication was performed; prior independent off-site receiver evidence, receipt and pin checks remain the recovery basis. No restore of deleted legacy snapshots was attempted. Rollback disables future legacy runs via inventory flag false and redeployment, or `systemctl disable --now btrfs-legacy-prune.timer`; deletion cannot be undone by toggling the flag.

Detailed closure record, operating evidence and exact source logs: `evidence/Step 12/STEP12-SCHEDULER-FORMAL-CLOSURE.md` and `evidence/Step 12/scheduler-acceptance/`. The separately CLOSED supplemental Step 12 qgroup metadata cleanup remains a distinct record. **Proceed to Step 13; overall 0037-FEAT remains in progress.**

## Step 13 status — documentation reconciliation in progress (2026-10-20)

Permanent-source promotion inventory and operational housekeeping checklist prepared. See `PROMOTION-MANIFEST.md` and `evidence/Step 13/STEP13-PRODUCTION-DOCS-AND-HOUSEKEEPING.md`. **Step 13 remains OPEN** pending host-side temporary-path inventory, full untagged local-backup check-mode drift reconciliation, Git revision recording and explicitly approved cleanup. Step 14 not started.

## Step 13 — FORMALLY CLOSED (2026-10-20)

**CLOSED — PASSED WITH DEFERRED HOUSEKEEPING.** Production source regression and reconciliation accepted; full untagged real `./local-backup.sh` idempotent (`ok=64 changed=0 failed=0`); timers and snapshot verification healthy; `mars` backup directory mode `0750`. Three root-owned legacy pull helpers remain intentionally retained pending reference checks; exhaustive host cleanup and final Git revision reconciliation are deferred to Step 14. See `evidence/Step 13/STEP13-FORMAL-CLOSURE.md`, deployment/host transcripts and revised `PROMOTION-MANIFEST.md`. Earlier Step 13 OPEN wording is chronological history. Overall feature remains OPEN for Step 14.

## Step 14 — formal closure (20 October 2026)

**CLOSED — PASS. 0037-FEAT COMPLETE.** Final host timers and backup verification accepted; three legacy root-owned helper files absent; Git sources previously clean/synchronized. See `evidence/Step 14/STEP14-FORMAL-CLOSURE.md`. Administrative relocation to `change-control/complete/` and subsequent closure commit are the remaining repository actions. Earlier Step 13 deferred housekeeping is resolved without amending historical Step 13 evidence.
