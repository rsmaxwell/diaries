# 0038-FEAT — Implementation steps

Every step records inputs, terminal/host, read-only versus mutating actions, outputs under `evidence/Step NN/`, acceptance decision and remaining risks. **A proposed step is not a completed step.**

1. **Freeze host/source baseline (read-only).** Reconcile latest Diaries/Playbooks ZIPs, Git HEAD/status, deployed JSON/binary hashes, installed timer enable/active state, receiver snapshot list and replication-state metadata (without secrets), and baseline failed status. Record initial `--check --diff`; determine actual role coverage. *Gate: sufficient evidence to bound exact planned changes.*
2. **Validate design and rollback.** Confirm receiver-only contract, remote-backup tasks and prerequisites, backup/restore of manager JSON/executables, no accidental receiver data or Snapper changes; decide if current Playbooks already provides entire correction. *Gate: explicitly approved deployment scope.*
3. **Regress current source and configuration (non-production).** Syntax/checks, manager config rendering, verified-dataset required-off on backup, native receipt preservation, disabled timers and negative/adversarial tests for unintended receiver mutations. Temporary harness stays under `tests/`; any reusable permanent regression is explicitly promoted. *Gate: passing tests.*
4. **Final Ansible review (`--check --diff`, read-only planning).** From `mango`, review all changed tasks and files, including systemd unit installation and remote-backup native tasks; reject unrelated changes. *Gate: operator accepts exact diff.*
5. **Controlled reconciliation on `backup` (mutating, no snapshots).** Preserve rollback copies under a *deliberately named and recorded* root-owned safety location, then deploy `remote-backup.yaml` with Ansible. Do not create/remove/prune snapshots. Record log and change count. *Gate: real run passes and receiver untouched.*
6. **Operational verification (read-only).** `btrfs-snapshot-manager status`, JSON, manager/history/verifier versions, three local timer `is-enabled` and `is-active`, receiver snapshot count/identity and replication receipts; compare pre/post. Validate native receiver without forcing a new transfer. *Gate: correct receiver-only status.*
7. **Idempotency and negative regression.** Repeat real Ansible run, expect `changed=0`; confirm failed obsolete-path status cannot recur from source config; check normal transfer is not blocked (without requiring a full send/restore). *Gate: reproducible configuration.*
8. **Documentation, housekeeping and close.** Source promotion manifest and Git revisions, retained rollback disposition, evidence index, removal of temporary host-side files (only after review), outstanding exclusions and formal acceptance. Move feature from `in-progress` to `complete` only when all acceptance conditions are met.

**Historical state at initial Step 3 closure (20 October 2026; superseded by subsequent acceptance sections below):** Step 1 CLOSED — baseline evidence accepted with explicitly documented unresolved source hygiene. Step 2 CLOSED — design, read-only rehearsal and rollback copies accepted. Step 3 CLOSED — source syntax, wrapper arguments, targeting and receiver-only source review accepted on 20 October 2026. Step 4 IN PROGRESS — final Ansible check/diff gate. Steps 5–8 NOT STARTED. The earlier Ansible `--check --diff` is prediction only and does not establish a real deployment.

## Step 1 formal acceptance — 20 October 2026

**CLOSED (documentation acceptance).** Reused 0037-FEAT mars correctness/timer evidence; recorded the current `backup` failed manager status, installed SHA-256 identities, 14 received Btrfs subvolumes and replication-state directory; creation/prune timers disabled/inactive, legacy-prune unit absent; Playbooks committed HEAD `6a80d4f4160574b243a3d1e73e2f8b0fac767846` plus identified uncommitted local edits; investigated duplicate `local_backup` YAML key, inspected corrected inventory and confirmed warning-free `--list-hosts` targets `mars` and `backup` individually, and successful remote playbook syntax check. Retain formatting findings and check-mode-only wrappers as Step 2 actions. No deployment or real receiver-integrity test has been performed.

## Step 2 execution boundaries (historical planning)

**Originally IN PROGRESS; later CLOSED.** Review current-source versus live `mango` local edits before making modifications; distinguish native receiver actions from `snapshots` role installation; document rollback source and permissions; confirm `--check --diff` scope against the corrected `remote_backup` target; obtain operator acceptance before any mutating deploy. Do not modify received subvolumes, receipts, timers or source revisions as part of this documentation package.

## Step 2 acceptance — 20 October 2026

**CLOSED.** Corrected local/remote playbook targeting (`mars` and `backup` separately), YAML LF whitespace, both backup wrapper Bash syntax and defaults. Wrapper without arguments uses Ansible `--check --diff`; `--apply` explicitly requests real deployment. Operator executed `git diff --check`, both Bash `-n`, both playbook syntax checks (all passed). Actual default `./scripts/remote-backup.sh` check-run reported `backup: ok=22 changed=5 unreachable=0 failed=0 skipped=13`, proposing manager, history tool, schema-2 verifier, manager JSON and new legacy-prune systemd unit files. The predicted JSON has empty writer lock, `verification.required=false`, empty obsolete dataset and marker fields. Creation/prune timer activation tasks skipped. **This is a check-mode prediction, not a real deployment.**

On `backup`, the operator copied the existing manager executable, manager JSON, backup-history utility and manifest verifier into `/root/remote-backup-pre-reconcile/` (root-owned directory, `0700`). Subsequent root-side `sha256sum` values matched all four Step 1 installed baselines and four `cmp` comparisons emitted no differences. No manager deployment, snapshot mutation or receipt modification took place.

Step 3 must establish source regression coverage and negative receiver-safety properties before Step 4's final check/diff approval. Do not run `--apply` during Step 3.

## Step 3 formal acceptance — 20 October 2026

**CLOSED (source-level acceptance).** Evidence: uploaded `mango` logs `note(20261020-202013).txt` (syntax/targets/arguments), `note(20261020-200913).txt` (remote wrapper check-mode `ok=22 changed=5 failed=0`) and `note(20261020-202256).txt` (role/default/template/receiver inspection). `git diff --check`, both Bash `-n`, remote syntax and list-hosts succeeded; `--help` succeeded and invalid arguments were rejected. Target: only `backup`. Snapshot activation, verified local Diaries integration and unattended legacy pruning default false, writer lock empty. Native receive tree and receipts remain separately addressed by native receiver source.

Scope limit: source review and Ansible planning, not proof of live receiver immutability. No separate destructive/adversarial regression or complete transfer/restore was performed. Final rendered diff, task mutation scope, systemd timer states and actual receiver invariance remain separate Step 4–6 gates.

## Step 4 opening — 20 October 2026

**IN PROGRESS.** Run read-only final `./scripts/remote-backup.sh` from `mango` and review exact changes, targeting, local timer activation, receiver/receipt non-mutation and avoidance of unexpected host changes. Do not run `--apply` in Step 4. Ansible check mode predicts changes; it cannot certify real deployed runtime behaviour.

## Step 4 formal acceptance — 20 October 2026

**CLOSED — final Ansible check/diff accepted.** Operator transcript `note(20261020-203011).txt` from `mango` records clean `git diff --check`, valid `remote-backup.yaml --syntax-check`, and `--list-hosts` resolving **only `backup`**. Default `./scripts/remote-backup.sh` completed Ansible check mode with `backup: ok=22 changed=5 unreachable=0 failed=0 skipped=13`. Five changed Ansible tasks: install current manager, history utility, schema-2 manifest verifier, replace obsolete manager JSON, and install the two legacy-prune systemd unit files (single looped task).

The JSON diff removes the retired `diaries-mars-replica` writer lock, dataset and marker; sets `writer_lock_path` empty, `verification.required=false`; and leaves host-specific replication protection/checkpoint holds not required on `backup`. Snapshot create/prune and unattended legacy-prune activation tasks were skipped. The plan contains no received-snapshot or receiver-receipt mutation. Historical root-owned rollback copies of four installed files are verified (`Step 2`).

**Limit:** This was predictive check mode only. Do not claim deployed status, current timer activation, unchanged Btrfs UUIDs or runtime status until Steps 5–6 prove them. The operator accepted this narrow predicted scope for the controlled Step 5 deployment, not snapshot deletion, a fresh transfer, retention change or restore. Source tree remains locally modified as recorded; duplicate Python imports are non-blocking source housekeeping.

## Step 5 opening — 20 October 2026

**IN PROGRESS — controlled reconciliation only.** Use the step-specific runbook `evidence/Step 05/STEP05-CONTROLLED-DEPLOYMENT.md`. Run the explicitly opted-in deployment only after confirming rollback files still exist, then collect actual Ansible results and host verification. Step 5 may not be marked CLOSED until the real deployment and scoped receiver-integrity checks pass.

## Step 5 formal closure — 20 October 2026

**CLOSED — controlled deployment and immediate verification accepted.** `backup` baseline `note(20261020-203555).txt` recorded four preserved root-owned rollback copies with matching SHA-256 sums, 14 received subvolumes and disabled/inactive local timers. `mango` deployment `note(20261020-203837).txt` ran `./scripts/remote-backup.sh --apply`, ending `backup: ok=27 changed=5 unreachable=0 failed=0 skipped=8`; manager preflight succeeded, `diaries_verification=disabled`. `backup` runtime `note(20261020-203934).txt` verified `btrfs-snapshot-manager status` succeeds, valid corrected JSON (writer lock empty, verification not required), all three local timers disabled/inactive, unchanged received subvolume IDs 55593–55792 (14 entries), and `/.replication-state` directory remains present. `mango` post-deployment default check-run `note(20261020-205235).txt` ended `ok=22 changed=0 failed=0`.

**Scope and limits:** Deployment did not deliberately initiate a snapshot, delete a received subvolume, prune, send/receive replication or restore. A status-only qgroup diagnostic reports `qgroups_status=unavailable;reason=unexpected_output`; treated as non-blocking and deferred. Receipt content, installed history/verifier diagnostics and next normal transfer are not yet proven; these belong to subsequent acceptance gates.

## Step 6 operational verification — 20 October 2026

**IN PROGRESS; NOT CLOSED.** Existing runtime evidence accepts snapshot manager status, JSON structure, timer state and received Btrfs subvolume ID/path invariance. Still required: read-only inspection of receiver receipt files/identities (without publishing secrets), sanity/usage of installed history and schema-2 verifier, and confirmation that the native receiver configuration is present and stable. Do not infer receipt validity merely from existence of its directory. Run the focused read-only verification under `evidence/Step 06/STEP06-OPERATIONAL-VERIFICATION.md`; record command outputs before closing Step 6 or opening Step 7.

## Step 6 formal acceptance — 21 October 2026

**CLOSED.** The read-only `backup` verification was accepted using four existing logs: `note(20261020-203934).txt` (installed manager status, corrected JSON, disabled/inactive local timers, 14 baseline receiver subvolumes), `note(20261020-205235).txt` (Ansible dry-run convergence `changed=0`), `note(20261021-071157).txt` (installed manager/history/verifier all root:root mode `0755`, Python syntax passes; 15 receipt files with `richard:richard` mode `0600`, protected receipt directory) and `note(20261021-071328).txt` (read-only Btrfs subvolume/receipt identity check and inventory).

The new received subvolume `20261021-030006Z` has ID `55805`, `Flags: readonly` and Btrfs **Received UUID** `c0ad8538-dc61-bc48-8922-6c37eaf1a902`, matching the receipt's `received_uuid` and `source_uuid`. The receipt has `schema:1`, `transport:btrfs-incremental`, parent `20261020-030026Z`, exact destination `/@data/mars-received/@data/20261021-030006Z`, `read_only_verified:true` and source-send/receiver-receive exits `0`. The receiver inventory contains 15 subvolumes, including all 14 baseline IDs and the new ID `55805`. A normal overnight native receive therefore succeeded following Step 5 deployment **without forcing another transfer or restore**.

**Non-blocking diagnostic:** local manager status prints `qgroups_status=unavailable;reason=unexpected_output`. This optional summary limitation does not undermine accepted receiver identity, receipts or manager preflight; defer parser investigation unless future health checks require it. Do not enable local timers or change receiver state in Step 7.

**Step 7 IN PROGRESS.** Reuse the accepted post-deployment Ansible check-mode `changed=0` result but independently perform bounded negative/configuration-regression checks; the implementation plan asks for a repeated real Ansible idempotency run, so check-mode evidence alone does not prove that separate criterion. A real repeat must be explicitly approved and reviewed before Step 7 closure. See `evidence/Step 07/STEP07-REGRESSION-PLAN.md`. Step 8 NOT STARTED.

## Step 7 formal acceptance — 21 October 2026

**CLOSED — real-run idempotency and receiver-only negative configuration regression accepted.** Three new operator transcripts complete the gate:

- `note(20261021-072024).txt` (`mango`): `git diff --check`, `remote-backup.yaml` syntax and `--list-hosts` pass, only `backup` targeted; default snapshot activation, verified-Diaries integration and unattended legacy pruning all `false`, writer lock empty; checked deployment inputs contain no `diaries-mars-replica`.
- `note(20261021-072206).txt` (`backup`): six installed JSON safety assertions PASS, and creation, pruning and legacy-prune timers all explicitly `disabled` and `inactive`.
- `note(20261021-072739).txt` (`mango`): **real** `./scripts/remote-backup.sh --apply` ended `backup: ok=26 changed=0 unreachable=0 failed=0 skipped=8`; no manager/config/unit changes and activation gates remained unselected. This supplements accepted `note(20261020-205235).txt` **check-mode** `changed=0`.

The overnight incremental receipt and received Btrfs snapshot from Step 6 substantiate that normal replication was not blocked. Tests were deliberately bounded: no adversarial destructive test, manual snapshot operation, forced transfer, full restore or retention mutation. The optional `qgroups_status=unavailable;reason=unexpected_output` remains an explicitly deferred non-blocking diagnostic.

**Step 8 IN PROGRESS.** Reconcile all acceptance records, actual source revisions/status and promotion manifest, outstanding exclusions and rollback-copy disposition; only then formally close Step 8 and move the feature directory from `in-progress` to `complete`. Do not infer committed Git revisions or cleaned host files without evidence.

## Step 8 formal acceptance — 21 October 2026

**CLOSED.** Operator-provided evidence confirms that all previous Step 1–7 acceptance gates are closed; Step 7's repeated actual deployment converged with `backup ok=26 changed=0 failed=0`. Final Git provenance was verified: Diaries `main` clean and synchronized at `e69e08b2ff100b7d2afcf8458e9cb9204bc6be5a`; Playbooks `main` clean and synchronized at amended/pushed `fc8233da3464aa114d69a2e34bd8990f96daf281`. The prior Playbooks SHA `908509ec57e06f972b4412fae8f98b7a4f4edc1f` was superseded by commit-message amendment; do not use it as current revision.

The four root-owned pre-reconciliation rollback copies under `/root/remote-backup-pre-reconcile/` on `backup` are **intentionally retained** as a manual emergency baseline; no deletion or restore was performed. The optional `qgroups_status=unavailable;reason=unexpected_output` status summary is a **deferred, non-blocking diagnostic**, not evidence of failed receive or a blocker for this feature. No full restore, forced transfer, snapshot prune/delete, changes to retention/receipts/schedules, or local timer activation are required.

**Overall feature decision: CLOSED (21 October 2026).** Source delivery includes moving this entire feature tree to `change-control/complete/`; final Git commit/push of that directory move is an operator follow-up and should be captured as the archival revision when done. See `evidence/Step 08/STEP08-ACCEPTANCE.md`.
