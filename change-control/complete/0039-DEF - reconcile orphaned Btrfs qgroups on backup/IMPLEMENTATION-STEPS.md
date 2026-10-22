# 0039-DEF — Implementation and acceptance gates

Each step must record observed evidence, execution host, **read-only or mutating** classification, source revisions, decision, and remaining risks. Work sequentially; never infer success from a proposed command.

1. **Freeze live inventory (READ-ONLY; CLOSED 2026-10-21).** On `backup`, record supported tool/kernel versions, filesystem/quota feature context, level-0/higher-qgroup counts, live subvolume IDs, overlap/orphan candidate ID sets, zero/nonzero distributions, deletion-in-progress, and manager diagnostic baseline. Compare any prior capture where available. Minimal evidence under `evidence/Step 01/`; no 30k-row raw log needed. Gate: independent, bounded inventory and clearly qualified orphan estimate.
2. **Root cause and reproduction (DIAGNOSTIC SOURCE + READ-ONLY OBSERVATION; CLOSED 2026-10-21).** Inspect current authoritative Diaries/Playbooks source, installed program differences, parse rules, Btrfs quota state and kernel signals. Check whether candidates are genuine leftovers and whether they are still accruing; optional read-only comparison with `mars`. Gate: stated confidence/uncertainty and precise diagnosis for parser vs quota metadata.
3. **Remediation design, impact and recovery (CLOSED 2026-10-22; approved cleanup and post-remediation replication accepted; recurrence risk explicitly deferred).** Evaluate leave-as-is, targeted qgroup cleanup if actually supported and safe, alternative quota repair paths, and permanent prevention. Confirm exact installed command/version semantics; protect hierarchy relations, active snapshots, send/receive parentage and receipts. Document non-reversibility, rollback limitations, maintenance window, performance impact and stop conditions. Gate: explicit operator approval before any filesystem-accounting mutation.
4. **Permanent source changes and regressions (NON-PRODUCTION; CLOSED 2026-10-22).** If necessary amend Playbooks snapshot manager and appropriate roles; make diagnostic bounded, version-tolerant and fail-safe, add isolated test fixtures including large zero-row tables and error/timeout cases. Classify test helpers (permanent vs historical). Gate: test output and clean diff.
5. **Ansible plan and host preflight (READ-ONLY; CLOSED 2026-10-22).** Run syntax, target review, `--check --diff` on `mango` with `--vault-password-file ~/.vault_pass.txt`; freeze received snapshot IDs/UUID/receipt counts and timer states on `backup`; inspect expected exact changes. Gate: approved diff, clean safety preflight.
6. **Controlled repair/deployment (MUTATING, SEPARATELY APPROVED; CLOSED 2026-10-22).** Only perform specifically accepted Btrfs operation(s), if justified, and/or approved Ansible deployment from `mango`; never mix unrelated snapshot retention operations. Record timings, progress, command results, and any no-go. Gate: no unexpected effect on receiver/snapshots.
7. **Reconciliation and idempotency (READ-ONLY VERIFY; APPLY ONLY IF APPROVED; CLOSED 2026-10-22).** Repeat bounded inventory; verify surviving qgroup/subvolume correspondence and no new orphans, diagnostic status, receipt UUIDs, read-only flags, parent ancestry and timer states; real Playbooks idempotency if source deployed. Reuse accepted backup/restore evidence; avoid unnecessary complete restore. Gate: exact postconditions met.
8. **Documentation, evidence and close.** Record root cause, before/after counts, restrictions, risk acceptance, final Git revisions and evidence, future-maintenance behaviour, rollback limits. Move the *whole directory* to `change-control/complete/` **only after** acceptance gates satisfied; if no safe fix, record disposition and use `will-not-fix` rather than claiming closure.

**Current decision (2026-10-22, superseding the historical 2026-10-21 decision):** Steps 1–2 CLOSED; the Step 3 production cleanup, independent final state check and manual post-cleanup incremental replication checks PASSED. Step 3 is CLOSED under documented temporary recurrence-risk acceptance; Steps 4–7 CLOSED by operator acceptance of the recorded Step 2–3 evidence reconciliation; Step 8 closeout prepared, subject to applying the package and verifying the final Git move/commit. The 2026-10-21 no-mutation decision below has been superseded by subsequent explicit operator approval and execution. No OS upgrade/reseed/full restore was performed.

### Additional acceptance requirements (2026-10-21)
- Step 2 must identify why stale qgroups recur on `mars` after the previous successful cleanup, correlate qgroup creation with deletion and retained quota-limit paths, and distinguish actual Btrfs `<stale>` markers from naive whitespace column parsing. Prior cleanup history is operator-reported until the original evidence is located.
- Step 3 must separately evaluate supported kernel and `btrfs-progs` updates on both hosts, including Ubuntu 22.04→24.04 release upgrade planning for `backup`, reboot/remote-console recovery, preserved bootable kernels and independent maintenance windows. Do **not** combine OS upgrade with mass qgroup cleanup.
- No kernel/HWE migration is assumed necessary on `mars`: its installed `linux-generic` is newer than the booted kernel, and `btrfs-progs` already matches the configured repository candidate.
- Step 4/7 diagnostic regressions should use genuine `-pcre` headers, `<stale>` paths, omitted/variable path fields and large tables; do not infer orphan status from usage alone.

### Step 2 closure evidence (2026-10-21)
- Accepted identity correlation: `mars` native deletion `20919`/`20920` at 10:15:09 UTC and subsequent stale entries; 41→43 stale records. Original `note(20261021-101854).txt`.
- Corrected standalone snapshot launcher to inherit host-specific `local-backup`/`remote-backup` role context and default to Ansible `--check --diff`; no configuration regression.
- `mars`: targeted check then `--apply` (30 OK, 1 changed), runtime verification (61 complete sets, none incomplete, valid Diaries marker), post-deploy Ansible `changed=0`.
- `backup`: old Btrfs qgroup column-heading compatibility regression passed; targeted check then `--apply` (24 OK, 1 changed), runtime reports 29,571 total, 0 explicit stale, no rescan, all three local timers disabled, post-deploy Ansible `changed=0`.
- Formal gate: **Step 2 CLOSED**. Exact persistence kernel mechanism and orphan disposition deferred to Step 3. Source edits are not yet evidenced as committed: capture actual Git commit IDs after operator commits.

## Step 03 interim acceptance update — 2026-10-21

Read-only inventories and full operator-captured JSON manifests for `mars` and `backup` have passed isolated source tests, live output compatibility, count/ID uniqueness, classification and filesystem-identity verification. The evidence, exact summary figures, capture fingerprints and SHA256 values are indexed at `evidence/Step 03/STEP03-EVIDENCE-INDEX.md`. All evidence is held beneath the defect directory, not in a separate `mango` evidence tree.

**Step 03 remains IN PROGRESS:** no remediation has been authorised; permanent validator/fingerprint verification, replication/hold reconciliation, recurrence assessment and independent operator mutation gate remain open. The documentation ZIP does not contain the four large/small local inventory/identity captures already present in the operator's Windows checkout.

### 2026-10-21 Step 03 protection progress (not closure)

Accepted: complete source regressions; both saved full manifests independently validated offline against fingerprints and filesystem identity; deployed source protection configuration inspected; all three protected `@data` received UUIDs matched `mars`; six protected `mars` snapshots and three received `backup` snapshots returned `ro=true`. The exact original read-only property terminal logs are retained under `evidence/Step 03/protection/{mars,backup}/`. Evidence index updated. Outstanding: receiver receipts/active incremental-parent chain, qgroup-specific safeguards, recurrence/remediation/rollback design and operator approval. **Step 03 OPEN; 0039-DEF OPEN; no mutation authorised.**

### Step 03 receiver receipt gate (2026-10-21)

**PASS for captured historical lineage:** protected receiver receipt UUIDs and three historical parent references reconcile; no received root snapshots are required by the @data-only contract. The current pinned parent remains accepted, but future incremental transfer health and qgroup-remediation eligibility are not thereby guaranteed. See `evidence/Step 03/STEP03-RECEIVER-PARENT-RECONCILIATION.md` and original logs. **Next:** offline qgroup-specific safety assessment and documented recovery/approval constraints. Step 03 OPEN; no mutations authorised.

## 2026-10-21 — offline assessment and historical patterns (Step 03 open)

Both actual saved manifests passed the fail-closed offline safety assessor: `mars` 191 total (140 active-excluded, 6 protected, 24 limited, 21 unmatched investigation-only) and `backup` 29,571 total (131 active-excluded, 3 protected, 13,962 limited, 15,475 unmatched investigation-only). Source-fingerprint and SHA256 verification passed. No deletion commands were generated or authorised.

Read-only historical analysis found `backup` has 29,437 unmatched qgroups over IDs 276–55746, concentrated nearly continuously from ~27000 onward, with limited and unlimited records interleaved; near the end, odd limited/even unlimited IDs alternate. This *suggests* a repeated historical pair workflow but proves neither source nor eligibility. Current snapshot-manager pruning logs exact subvolume IDs before deletion and does not explicitly reconcile qgroups; its second deletion call is creation rollback. Native receiver failed-transfer destinations are left for inspection. Causality is unresolved.

See `evidence/Step 03/STEP03-OFFLINE-ASSESSMENT-AND-HISTORICAL-PATTERN.md` for exact sources, original logs and checksums. Both locally saved assessment JSON files remain in `evidence/Step 03/assessment/` and are not overwritten. **Step 03 IN PROGRESS; 0039-DEF OPEN; no production mutation authorised.**

## 2026-10-21 — Snapper-pair linkage and disposable stale-qgroup reproduction (Step 03 OPEN)

Seven surviving `backup` Snapper `@data`/`root` snapshot pairs have adjacent subvolume IDs, and the validated manifest shows `@data` at 1.00TiB max referenced versus unlimited `root` for all seven. Historical cleanup ran for both configurations. The 2026-10-21 `backup` baseline confirms no pending deletions and idle quota rescan. This strongly supports, but does not exhaustively prove, historical Snapper association of the 29,437 unmatched qgroups.

On an isolated 512 MiB loopback Btrfs filesystem on `mango` (UUID `8346c9fd-6dbb-45b6-94dc-e8b4728e2757`), successful synchronised deletion left **both** unlimited qgroup `0/257` and 1 TiB-limited qgroup `0/259` `<stale>`. A later read-only check showed 0 B usage for both while the 1 TiB limit remained. These results do not establish backup's exact Btrfs mechanism or safety of destroying any qgroup. Original logs and hashes, limitations and next acceptance gates are in `evidence/Step 03/STEP03-STALE-QGROUP-REPRODUCTION.md`. The disposable filesystem remains intact. **Step 03 / 0039-DEF IN PROGRESS; no production mutation authorised.**

## 2026-10-21 — disposable qgroup reconciliation Gates A–D (Step 03 OPEN)

On the identity-verified 512 MiB `mango` loopback Btrfs filesystem (UUID `8346c9fd-6dbb-45b6-94dc-e8b4728e2757`), the four guarded rehearsal gates **passed**. Gate A recorded live IDs and limits; Gate B destroyed only stale unlimited `0/257`; Gate C destroyed only stale 1 TiB-limited `0/259`; Gate D verified the exact three original active qgroup rows and the two active subvolumes remained, no deleted snapshot reappeared, no pending deletions/rescan, and read-only stale selection returned zero. See `evidence/Step 03/STEP03-RECONCILIATION-GATES-A-D.md` and original logs in `evidence/Step 03/reconciliation/mango/`. The separate SHA256 manifest uses defect-root-relative paths. This supports **disposable removal feasibility only**, not any production candidate eligibility or production remediation authorisation. Gates A–D accepted on observed outputs; preservation checksum verification in local checkout remains pending. **Step 03 and 0039-DEF stay IN PROGRESS**; do not dismantle test image yet.

## 2026-10-21 — offline investigation planner adversarial regression accepted (Step 03 OPEN)

The offline planner passed complete saved `backup` (29,571 qgroups) and `mars` (191 qgroups) baselines, five command-line negative tests, and **12 adversarial evidence-tampering regressions**. The first regression attempt exposed an unhandled manifest-validator exception; the subsequent targeted fix was verified by controlled `PLAN UNAVAILABLE:` errors for all 12 cases. Python compilation, source-evidence SHA256 unchanged, and `git diff --check` passed. Original successful terminal log, defect-root-relative SHA256 manifest, individual rejection cases and acceptance limits: `evidence/Step 03/STEP03-PLANNER-REGRESSION-ACCEPTANCE.md` and `evidence/Step 03/planner-regression/note(20261021-151658).txt`.

**Offline planner adversarial gate ACCEPTED; Step 03 remains IN PROGRESS.** Live protection, receipt/hold and fingerprint revalidation and any production deletion authorisation remain outstanding. This assessment does not approve production mutation. Evidence installation and checksum verification in the user's local repository are pending.

## 2026-10-22 — Step 3 production remediation and replication acceptance

**Evidence:** `evidence/Step 03/STEP03-PRODUCTION-REMEDIATION-ACCEPTANCE.md`, plus `evidence/Step 03/reconciliation/backup/` journal/acknowledgement files and checksum manifests in this source bundle.

- Baseline on `backup`: 29,571 qgroups, 133 active subvolumes, 29,437 unmatched level-0 qgroups plus `0/5`; deletion was specifically approved after independent offline and disposable rehearsal gates. Removal is irreversible as an accounting-metadata operation, not an ordinary rollback.
- Production pilot, small and bounded journalled batches, the interrupted 675-deletion batch (`FAIL` preserved), its checksum-bound acknowledgement, subsequent 1,000-deletion batches, two 10×1,000 sequences and final six 1,000 plus 640 batches together removed **29,437** candidates. Each completed batch reported PASS. Original failed journal remains unchanged and its 675 deletions were independently reconciled.
- At 2026-10-22 post-deletion check: **134 live subvolumes, 135 qgroups, zero unmatched**, no pending deletion or quota rescan; four received snapshots' identity and read-only state validated.
- Manual `mars` snapshot `20261022-082824Z`; preflight selected **incremental** parent `20261022-030026Z`; `btrfs-native-push.service` finished successfully with receiver `ACCEPTED`. Independent `backup` receipt (`schema=1`, send/receive exits 0, read-only verified) and matched source/parent received UUIDs. After receive: **135 live subvolumes, 136 qgroups, zero orphans**.
- **Decision:** production cleanup and post-cleanup replication acceptance **PASSED**. Do not rerun deletion, rebuild/reseed or restore. Recurrence, long-term prevention, remaining standalone step gates, exact Git revisions and documentation closeout remain pending. Keep 0039-DEF **OPEN**.


## 2026-10-22 — accelerated Step 03 disposition and formal closure

**Step 03: CLOSED (design/approval, production cleanup and post-cleanup verification accepted).** Operator decision: complete 0039-DEF through an accelerated evidence-based review, then upgrade `backup` from Ubuntu 22.04 to 24.04 as the immediately following, **separately controlled** change. The upgrade is a near-term mitigation opportunity, **not a proven prevention fix**.

- **Mutating evidence accepted:** guarded, journalled removal of all **29,437** unmatched level-0 qgroups on `backup`. The interrupted 675-deletion journal remains marked `FAIL`, with distinct checksum-bound reconciliation acknowledgement; do not recast it as an uninterrupted success.
- **Read-only verification accepted:** independent filesystem inventory after cleanup and independent post-cleanup incremental `mars` → `backup` receive, including receipt/UUID/parent/`ro` correlation and **zero unmatched qgroups** afterwards. See `evidence/Step 03/STEP03-PRODUCTION-REMEDIATION-ACCEPTANCE.md` and its original logs/journals.
- **Temporary residual risk explicitly accepted:** stale qgroups may recur on `backup` or `mars`; updated `btrfs-progs` may expose `<stale>` and cleanup capability, but neither visibility nor upgrade alone proves recurrence is prevented. Preserve bounded diagnostics, protected snapshot holds, replication receipts and existing sender/receiver operation. Do not start a background destructive cleanup service as part of this defect.
- **Follow-on change (outside 0039-DEF):** Ubuntu 24.04 upgrade of `backup`, with separate approval, recovery/console and boot fallback, Ansible review, replication safety checks, and post-upgrade observation of qgroup accumulation. Evaluate `mars` recurrence during this follow-on work. Do not bundle the upgrade with quota deletion or mass cleanup.
- **Limits:** no further full restore, filesystem repair or production mutation is required solely for Step 03. Successful tests are accepted as recorded; future recurrence and post-upgrade performance are not validated here.
- **Change-control boundary:** Steps 4–7 require a concise evidence/NA reconciliation against the original gates; Step 8 and the defect directory remain **OPEN** until this reconciliation and final source revision review are recorded. Commit ID `b6d87da8919ba85312ad03a675660080cbea01aa` is only the operator-reported pre-closure HEAD, **not** a commit containing these local changes.


## Accelerated cross-step evidence reconciliation — 2026-10-22

Review `evidence/STEPS04-07-EVIDENCE-RECONCILIATION.md` before accepting Steps 4–7. The original Step 2 and Step 3 evidence is reused; **no further qgroup deletion, snapshot/retention change, Ansible apply, restore or OS upgrade is requested**. Recorded source states: Diaries `6d682e48bb31513c19f6f7600d1b05e082cd9f12` (reported synced); Playbooks `b55d1f4cf0d72dbbca461bedd2338b0bcf1b98fc` (merge synced). These commits identify the operator's reported repository state; they are not an independent verification that each historical evidence artifact is committed.

**Disposition:** Steps 4–7 ACCEPTED based on historical evidence reuse, with the limitations listed in the reconciliation. The remaining Step 8 operation is to apply this documentation patch, relocate the entire defect directory intact, verify the final diff and commit. Recurrence prevention is deferred to a separately controlled Ubuntu 24.04 upgrade; an upgrade is not evidence of recurrence prevention until tested.


## 2026-10-22 — Steps 4–7 accepted; Step 8 closeout procedure

The operator agreed to accelerated acceptance based on the existing evidence and then requested final closeout. Steps **4, 5, 6 and 7 are CLOSED by evidence reuse**; see `evidence/STEPS04-07-EVIDENCE-RECONCILIATION.md`. This is not a new regression run, deployment, restore or filesystem operation.

**Step 8 disposition:** cleanup objective met; no new orphaned qgroups after accepted post-remediation incremental replication. Original failure/recovery journal, receipt and snapshot protections are retained. Causal prevention remains unproven; temporary recurrence risk is knowingly accepted pending an immediate, separately governed Ubuntu 24.04 upgrade on `backup`. No automatic qgroup deletion service is authorised. Post-upgrade qgroup recurrence on `backup` and `mars` is for the follow-on change.

**Closeout acceptance gate:** apply Step 8 documentation, move the entire feature directory from `change-control/in-progress/` to `change-control/complete/` using Git, preserving original evidence filenames, then verify `git diff --cached --check`, staged rename inventory, and clean worktree after committing. Only after those checks should Step 8 and overall 0039-DEF be recorded administratively CLOSED. Final closeout commit hash will differ from the reported starting Diaries revision `6d682e48` and must be captured after commit; Playbooks baseline `b55d1f4` is already reported synced.
