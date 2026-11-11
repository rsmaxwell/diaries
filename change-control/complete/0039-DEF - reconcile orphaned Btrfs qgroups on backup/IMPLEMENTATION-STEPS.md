# 0039-DEF — Implementation steps

**Plan consolidated:** 9 November 2026; **final acceptance reconciliation:** 11 November 2026. **Status:** Steps **1–12 CLOSED**, following two consecutive unattended 05:30 UTC housekeeping cycles and final evidence reconciliation. The 0042-FEAT legacy-source retirement remains independently **CLOSED**. Formal archiving into `change-control/complete/` and Git publication are the final operator actions; their success is not asserted before terminal readback.

## Scope and safety

The original defect covered the broken `btrfs-snapshot-manager status` diagnostic and 29,437 unmatched level-0 Btrfs qgroups on the off-site receiver `backup`. It also identified repeated accumulation of `<stale>` qgroups on sender `mars`. The receiver cleanup and post-cleanup incremental replication were accepted on 22 October 2026, **but recurrence prevention was not demonstrated**.

**Agreed remaining scope (9 November 2026):** manage recurrent stale/orphaned qgroups on **both `mars` and `backup`**, using **one shared code implementation** with per-host configuration; investigate and address the underlying lifecycle cause where practical; operate **automatic, safely interlocked cleanup using systemd timers**; and verify that the backlog does not grow indefinitely or compromise snapshot management or replication. The Ubuntu OS upgrade is **out of scope**, with no upgrade dependency for this defect. Different Btrfs userspace capabilities must nevertheless be detected and handled safely. The existing 0039 directory name mentioning `backup` is historical; no directory rename is required by this documentation update.

For each new operation, record host/terminal, source revision, installed version/capabilities, read-only vs mutating behaviour, results, safety conditions and acceptance. Reuse accepted evidence; do not repeat the large cleanup, full restore or end-to-end test solely to satisfy new numbering. Agreement on an **automatic-cleanup requirement is not authorisation to enable a not-yet-verified production timer**: approve the concrete implementation and guarded production activation under Step 10. No Ubuntu/kernel upgrades, new snapshot deletion policies, receiver reseeds or unrelated retention/schedule changes belong in this defect.

## Implementation sequence

### Step 1 — Establish the diagnostic baseline — CLOSED (21 October 2026)

- Inventory Btrfs/kernel/tool versions, filesystem identity, qgroups by type, subvolumes, relationships, limits, pending deletions and quota-rescan state on `backup`; compare `mars` where relevant.
- Distinguish *unmatched* qgroup IDs from merely zero-usage rows and from the Btrfs top-level `0/5` qgroup.
- **Acceptance:** bounded, independently checked counts and a qualified candidate set. **Evidence:** `evidence/Step 01/` and `evidence/Step 03/STEP03-EVIDENCE-INDEX.md`.

### Step 2 — Diagnose the symptom and correct the reporting path — CLOSED (21 October 2026)

- Separate the parser fault on older `backup` Btrfs utilities from persistent quota metadata after subvolume deletion; correlate observed stale IDs with native/Snapper deletion on `mars`.
- Correct the version-sensitive qgroup-header parser and snapshot-manager launcher context, regression-test them and deploy the accepted changes via Playbooks. Verify read-only status and Ansible idempotency.
- **Acceptance:** diagnostics work on both supported observed output formats; deletion correlation is documented **without claiming a proven kernel-level cause**. **Evidence:** `evidence/Step 02/STEP02-CLOSURE.md` and the Step 02 logs.

### Step 3 — Design and approve a guarded receiver cleanup — CLOSED (22 October 2026)

- Validate exact candidate IDs against independent live subvolume, qgroup, limit and relationship inventories, filesystem identity, protected snapshots, read-only properties, received UUIDs, receipts and incremental-parent holds.
- Assess non-reversibility and stop conditions; test deletion on a disposable Btrfs filesystem and test the offline planner and journal/acknowledgement gates.
- Obtain explicit operator approval **before** mutating quota metadata on `backup`.
- **Acceptance:** safe candidate selection, rehearsed guarded method, and documented approval. **Evidence:** `evidence/Step 03/STEP03-RECONCILIATION-GATES-A-D.md`, `STEP03-PLANNER-REGRESSION-ACCEPTANCE.md` and `STEP03-PRODUCTION-REMEDIATION-ACCEPTANCE.md` (all under `evidence/Step 03/`).

### Step 4 — Implement and test the required source changes — CLOSED by evidence reuse (22 October 2026)

- Retain the accepted parser/launcher fixes, version-aware diagnostics, bounded reporting and safety-tested cleanup tools. Keep historical, one-off cleanup helpers as feature evidence rather than enabling an unattended deletion service.
- Reuse accepted source regressions and failure-path testing instead of asserting broader tests that were not run.
- **Acceptance:** the changes needed for the approved operation and diagnostic were tested; no permanent recurrence-prevention mechanism was claimed. **Evidence:** `evidence/Step 02/STEP02-CLOSURE.md`, `evidence/Step 03/STEP03-PLANNER-REGRESSION-ACCEPTANCE.md` and `evidence/STEPS04-07-EVIDENCE-RECONCILIATION.md`.

### Step 5 — Check deployment and receiver safety — CLOSED by evidence reuse (22 October 2026)

- Review the targeted Playbooks syntax, hosts and `--check --diff` output from `mango` before deployment, alongside receiver timer/hold/receipt and filesystem-identity preflight results.
- **Acceptance:** approved, limited host changes and no unexpected change to native replication or receiver snapshot protections. **Evidence:** `evidence/Step 02/STEP02-CLOSURE.md` and `evidence/STEPS04-07-EVIDENCE-RECONCILIATION.md`.

### Step 6 — Execute the approved cleanup and source deployment — CLOSED by evidence reuse (22 October 2026)

- Accept the recorded controlled Playbooks updates and journalled `backup` qgroup removals; preserve all logs, including the interrupted 675-deletion batch **marked FAIL** and its separate reconciliation acknowledgement.
- **Acceptance:** exactly **29,437** approved unmatched qgroups removed; the failed journal is not retrospectively marked PASS. No new deletion is required. **Evidence:** `evidence/Step 03/STEP03-PRODUCTION-REMEDIATION-ACCEPTANCE.md` and original journals under `evidence/Step 03/reconciliation/backup/`.

### Step 7 — Verify the result and replication integrity — CLOSED by evidence reuse (22 October 2026)

- Independently compare remaining live subvolumes with level-0 qgroups; check protected snapshot identities, `ro` flags, receipt lineage and incremental parent, and Playbooks idempotency.
- **Acceptance:** after remediation and a real incremental `mars` → `backup` receive, the receiver had **135 live subvolumes, 136 qgroups including `0/5`, and zero unmatched qgroups**; the receive and receipt/UUID checks passed. These are **point-in-time** results, not proof against future recurrence. **Evidence:** `evidence/Step 03/STEP03-PRODUCTION-REMEDIATION-ACCEPTANCE.md` and `evidence/STEPS04-07-EVIDENCE-RECONCILIATION.md`.

### Step 8 — Rebaseline both hosts and investigate qgroup recurrence — CLOSED (10 November 2026)

- **Baseline:** Windows Cygwin collector logs `evidence/Step 08/mars-baseline-20261109-135149Z.txt` and `backup-baseline-20261109-135152Z.txt` passed. Both hosts: kernel 6.8.0-147, btrfs-progs v6.6.3, native `btrfs qgroup clear-stale` supported. `mars`: 656 `<stale>` entries, zero unmatched unmarked orphans; `backup`: zero stale. The earlier source had a receiver-only installation path and incompatible lock/target assumptions.
- **Observed lifecycle:** A native `clear-stale` attempt partially removed 594/656 entries; remaining nonzero stale qgroups were `Device or resource busy`. A controlled quota rescan completed but did not resolve these entries. Subvolume-deletion processing progressed asynchronously. Exact-ID analysis later showed 11 pending subvolume deletions matching **all** 11 nonzero stale qgroups (and no unmatched IDs on either side), supporting the deferred-deletion explanation. This is an observed operational correlation, not an assertion that every Btrfs stale marker shares this cause.
- **Acceptance:** Baseline, capability, pending-deletion and root-cause-hypothesis gates satisfied; historical evidence unchanged. See `reports/STEP08-LIVE-BASELINE-REVIEW-20261109.md`, `reports/STEP09-PENDING-SUBVOLUME-DELETION-20261109.md`, and `reports/STEP08-10-ACCEPTANCE-RECONCILIATION-20261110.md`.

### Step 9 — Implement shared, guarded stale-qgroup management — CLOSED (10 November 2026)

- **Implementation:** One maintained `roles/snapshots/files/btrfs-clear-stale-qgroups.py`, installed by `btrfs-replication.yaml` for `mars` and `backup`, with distinct `/etc/btrfs-stale-qgroups.json` configurations and common service/timer templates. The safety checks include correct Btrfs target/UUID, manager and writer locks, live-subvolume correlation, native capability, bounded batches, and fail-closed errors. Dry-run is the CLI default; no snapshot/subvolume deletion, quota reset/rescan, or replication-state modification occurs in the cleaner.
- **Failure classification:** The native command may return `Device or resource busy` when its rejected IDs are still pending subvolume deletion. The shared code accepts `result=deferred_pending` only after checking that every remaining stale ID matches a pending deletion; all other errors fail. **22 regression tests PASS** including 91 eligible / 11 pending replay and security/lock cases.
- **Live acceptance:** 9 November 22:58 UTC `mars` cleanup: `stale_before=103`, `removed=95`, `stale_after=8`, `deferred_pending=8`, `result=deferred_pending`, systemd `Result=success`, `ExecMainStatus=0`. Next dry run: `stale_eligible=0`; complete snapshot sets remained **69** before and after, with valid source backup marker. `backup` installed dry run and controlled zero-stale cleanup also passed.
- **Evidence:** `evidence/Step 09/`, its raw terminal captures and `reports/STEP08-10-ACCEPTANCE-RECONCILIATION-20261110.md`.

### Step 10 — Deploy and activate automatic maintenance on `mars` and `backup` — CLOSED (10 November 2026)

- **Deployment:** Ansible installed identical shared cleaner source and host-specific configuration. On 9 November, 22 tests passed, both installs and dry runs passed, and `mars` was safely enabled only after its controlled cleanup passed. Both timers were enabled/active for 10 November at 05:30 UTC. This was the operator's executed and accepted mutation path; do not retrospectively claim that an unreviewed timer was authorised.
- **First unattended cycle:** 10 November `mars` 05:30:21 UTC: `stale_before=14`, `removed=14`, `stale_after=0`, `result=complete`; `backup` 05:30:00 UTC: `stale_before=0`, `stale_after=0`, `result=complete`. Both `ExecMainStatus=0`. At 07:29, `mars` had two newly eligible stale qgroups; a once-daily timer need not leave zero at all times. Source and receiver snapshot managers reported zero incomplete sets; the source production backup verification remained valid. Ordinary native replication was independently verified under completed 0042-FEAT, with identical protected parent on both hosts.
- **Rollback boundary:** `sudo systemctl disable --now btrfs-clear-stale-qgroups.timer` on a host stops subsequent scheduled runs; reinstalling a prior executable/config is through normal Playbooks and does **not** undo qgroup metadata already cleared. No rollback was required.
- **Evidence:** `evidence/Step 10/scheduled-maintenance-20261110.txt`, additional read-only captures, and `reports/STEP08-10-ACCEPTANCE-RECONCILIATION-20261110.md`.

### Step 11 — Consolidated recurrence and integration verification — CLOSED (11 November 2026)

- Exercise normal scheduled snapshot pruning and ordinary replication/receiver activity (using the existing operational schedule and already accepted correctness evidence where sufficient); observe at least enough subsequent maintenance cycles to establish that cleanup runs repeatedly and any newly produced stale qgroups are reconciled or an understood, bounded transient backlog remains.
- Compare per-host pre/post counts and candidate classification; inspect logs, retries/deferrals and failure handling. Verify protected parents, checkpoint holds, received subvolumes, replication receipts and existing timers remain intact. Check no unbounded accumulation across the observation window; record any version-dependent limitation explicitly rather than claiming it fixed.
- Run consolidated source/Ansible regressions and relevant integration checks. Correct defects and repeat only affected tests. **Do not require a full restore, reseed or another large one-time 29,437-qgroup cleanup** merely to re-prove the accepted October remediation.
- **Acceptance — PASS, 11 November:** The 10 and 11 November natural 05:30 cycles completed successfully on both hosts. `mars` removed 14 and 24 native stale entries, leaving zero after each run; `backup` removed zero because none were present. `Result=success` and `ExecMainStatus=0` on both hosts; follow-up dry-run classification found zero stale, under-deletion, pending and unmarked orphan entries. Source/receiver complete snapshot sets were 73/34 with zero incomplete, source production-backup verification valid, the installed shared cleaner SHA256 matched, and the agreed-parent timestamp `20261111-030031Z` matched. This demonstrates bounded behaviour in the accepted two-day observation window, **not** that the kernel can never produce future stale entries. **Evidence:** `evidence/Step 11/unattended-20261111-080933Z.txt`; `reports/FINAL-CLOSURE-RECONCILIATION-20261111.md`.

### Step 12 — Final evidence reconciliation and formal defect closure — CLOSED for acceptance (11 November 2026)

- Reconcile accepted October Steps 1–7 and newly collected Steps 8–11 against the actual Windows Diaries and `mango` Playbooks Git revisions, deployed units and journal evidence. Record remaining limitations and ownership without claiming prevention of future kernel-level stale markings.
- **Acceptance — PASS:** Historical Steps 1–7, accepted Steps 8–10 and the new Step 11 evidence are reconciled. The installed cleaner has identical SHA256 on both hosts; operational health and the protected agreed parent are intact. The defect is accepted for closure without asserting that no future stale entries can arise. Keep all historical evidence, including the interrupted October **FAIL** journal and separate acknowledgement, undisturbed. The existing `evidence/STEP08-FINAL-CLOSEOUT.md` remains a superseded *proposal*.
- **Evidence:** `reports/FINAL-CLOSURE-RECONCILIATION-20261111.md` with the raw Step 11 terminal capture in `evidence/Step 11/`. The final Git move/commit/push and resulting revision must be verified before claiming repository publication.

## Agreed decisions and explicit exclusions (9 November 2026)

| Topic | Decision |
| --- | --- |
| Stale/orphaned qgroups on `mars` and `backup` | **IN:** common management implementation, configured per host. |
| Investigating and mitigating recurrence | **IN:** seek lifecycle cause and improve it where practical; automatic safe cleanup must still work. |
| Timer-based unattended maintenance | **IN:** improve the existing disabled receiver-specific systemd design and safely activate on both hosts after checks. |
| Long-term acceptance | **IN:** verify sustained bounded backlog and preservation of snapshots/replication without needless full restores. |
| Ubuntu upgrades and broad kernel/platform upgrades | **OUT:** independent maintenance work, not a prerequisite or unverified cure in this defect. |
| Re-running accepted 22 October bulk deletion, receiver reseed or full restore | **OUT:** preserve and reuse accepted evidence, unless a new defect justifies targeted testing. |
| Changing snapshot retention, Btrfs replication protocol or protected parent semantics | **OUT:** only use existing interlocks/contract; any unrelated functional change requires its own change control. |

The old 21 October *no-mutation* statements were superseded **only for the specifically approved 22 October cleanup**. The current scope confirms a future automatic cleanup **design**, but does not itself grant permission to run existing unverified mutating code. The earlier eight-step sequence is retained as Steps 1–7 (completed) plus new Steps 8–12; historical dated evidence and the old draft Step 8 closure remain unchanged in `evidence/`.
