# 0049 — Implementation steps

**State (16 November 2026):** TECHNICAL ACCEPTANCE PASSED — COMMITTED REVISIONS AND FORMAL CLOSURE PENDING. Earlier dated reports retain their point-in-time evidence, but the original source-only header is superseded by this update.

| Step | Current assessment | Evidence / remaining action |
| --- | --- | --- |
| 1 — Baseline and contract | Baseline/contract captured | Source review, implementation manifest and deployment preview; final committed revisions still to be recorded |
| 2 — Integrated implementation | Implemented; verified in source | 32-file Playbooks change, corrected naming and dedicated 0041 sender status transport; source/regression logs |
| 3 — Consolidated regression | Technical tests passed | 0049 (19), 0041 (8), replication (25), additional snapshot/Diaries tests, Ansible check-mode |
| 4 — Deployment and acceptance | Live technical gates passed; Git/closure incomplete | Receiver-first deployment, sender deployment, real Btrfs push, independent received-UUID read-back, zero-delete preview and strict two-host Ansible idempotence |

No step is marked **CLOSED** until final acceptance and repository records have been reviewed. No additional destructive snapshot test, restore or replication run is required to complete repository finalisation.

The objective is one **coherent functional implementation**, followed by consolidated regression/integration verification and a controlled dual-host deployment. These steps are documentary checkpoints, not permission to fragment the feature into small deployments.

## Step 1 — Freeze the post-0041 baseline and finalise the interface contract

1. From the **Windows Cygwin terminal** in the Diaries parent checkout, capture branch, HEAD, `git status --short`, `.gitmodules` and `git submodule status` (including real submodule HEADs). Do not assume the Windows and `mango` checkouts agree.
2. From an **SSH terminal on `mango`**, inspect the actual Playbooks/Ansible-controller checkout after 0046, including root/child repos, submodules, inventory path, branch, HEAD and uncommitted edits. Use the current installed inventory; do not assume source-bundle values are live values.
3. From the **`mars` and `backup` SSH terminals** (read-only only), record `command -v` and checksums/versions for relevant deployed scripts; `systemctl cat/status/list-timers`, Ansible-reconciled unit and timer definitions; accepted 0041 sender/receiver account, SSH dispatcher and privilege boundary; parent and prior records **without exposing secrets**; source/receiver snapshot inventory; and read-only command outputs/exit statuses. Record the exact configured schedules and deletion caps rather than assuming defaults.
4. Inventory all callers/consumers of current names: Ansible templates/defaults/inventory, service/timer ExecStart, on-host scripts, forced-command dispatch/sudoers, unit dependencies, operator docs, monitoring and permanent regression tests. Check whether any legacy receiver operation is still needed for disaster recovery. Identify source-mode work owned by 0048; do not overlap it.
5. Compare findings against `MANAGEMENT-INTERFACE-CONTRACT.md`, including whether to safely migrate the internal `.simple-*` state files or record an explicit internal filename exception. Record any material divergence and resolve before implementation.

**Evidence:** `evidence/Step 1/` — exact revision/status manifests, command inventory, timer/privilege baseline and decisions. No production mutations.

## Step 2 — Implement the full management interface and naming cleanup

In one coherent Playbooks implementation change set:

- Split application dataset reporting from infrastructure reporting. Implement host-aware `btrfs-backup-status` and narrow `diaries-backup-status`. Keep `diaries-backup-history` as the detailed, distinct-Diaries-backup interface. Ensure latest marker/pull/replication state moves rather than silently disappears.
- Implement shared or small common table-formatting and JSON-output support where useful. Apply to all listed operator-facing tools, including receiver retention preview and replication status. Ensure internal RPC framing, `diaries-backup-history path`, fixed JSON schemas used by other programs, and error channels are preserved or explicitly migrated.
- Rename `btrfs-simplified-replication` to `btrfs-replication`; `btrfs-native-push` units to `btrfs-push`; and receiver `simple` retention units to neutral names. Update all live consumers and Ansible defaults/inventory variable families. Keep already accepted 0041 service identities, forced commands, wrappers, sudoers policy, unit sandboxing and ownership unchanged except verified name references.
- Consolidate `btrfs-snapshot-manager prune --dry-run`/`prune --max-delete N` across sender and receiver with mode-dependent, **unchanged** protections. Source `create` and hold semantics stay endpoint-specific. Remove or formally reserve superseded receiver operations only after proving callers are gone.
- Remove Diaries-specific *display* fields from Btrfs manager status without bypassing verification gates for creating snapshots. Review the potentially dangerous `run` (implicit unbounded prune) entry point and retire only after caller audit; do not rewire any production service to unbounded deletion.
- Keep operational Ansible roles, docs and permanent regressions clean. No feature-only scripts or reports inside the Playbooks repository. Keep any feature-specific scripts in this feature's `tools/` or `tests/` directories within the Diaries parent repo.
- If internal state filename migration is selected, implement as a guarded atomic migration (no reset/bootstrap) with identity equivalence and rollback, scoped to `mars` and `backup`. Otherwise document retained internal names and why they are safe implementation details.

**Evidence:** `evidence/Step 2/` — source diff/manifests, regression outputs, installed-file/unit migration mapping and rollback plan. Do not claim live installation merely because the source changes were authored.

## Step 3 — Consolidated regression and integration verification

Run a single comprehensive verification cycle after completing the coherent implementation; fix discovered issues and repeat only affected tests:

- Test the complete command matrix and help/argument validation on both host modes, including prohibited receiver `create`/hold/missing-cap `prune` paths, identity mismatches, lock contention, deferred replication, missing config and uncontactable receiver.
- Test all output contracts from `tests/ACCEPTANCE-MATRIX.md`: titled aligned tables, wide/empty data, UTC, no truncation, pretty JSON, JSON-only stdout, stable type/schema, explicit error output, status exit codes and `--local-only` truly avoiding remote calls.
- Compare pre/post retention selection **on identical fixtures**, including protected agreed parent/prior, independent holds, historical receipts, interrupted journals, deferred qgroup cleanup and exact max-delete behaviour; do not execute destructive operations against production snapshots to prove a formatting change.
- Prove source verification still gates snapshot eligibility; source and receiver pruning lock paths, Btrfs read-only/UUID checks and recovery remain valid. Prove dedicated sender/receiver identities, restricted SSH and sudo/dispatcher constraints remain no broader than the 0041 baseline.
- Confirm `ansible-playbook --syntax-check`, relevant permanent Python tests, host-scoped `--check --diff`, and (where justified) disposable complete sender-to-receiver testing. Avoid repeating expensive live restores or transfer tests when accepted 0041/0040 evidence plus targeted new tests suffice.
- Review the unit/timer switch for no duplication, original schedule preservation and workable rollback. Prove Ansible idempotence on a properly controlled deployment/test system.

**Evidence:** `evidence/Step 3/` — complete test matrix results, diffs, negative tests and signed-off deployment/rollback instructions; keep diagnostic output visible on failures. Any failed gate remains OPEN.

## Step 4 — Controlled deployment, read-back, acceptance and closure

1. Confirm the current repository branches, clean/dirty state, exact source revisions, pinned submodules and source-bundle precedence immediately before deployment; preserve unrelated local edits. Package Playbooks changes separately from Diaries change-control changes if ZIP delivery is used; compare and apply using Beyond Compare 4.
2. Use the current **`mango` Ansible-controller inventory and Vault configuration**; no redundant `-i` if the default inventory is effective. Review host-scoped `--check --diff` output for `mars` and `backup`. Confirm neither credentials nor secrets enter logs, reports or public Playbooks Git history.
3. Apply both host changes as one coordinated feature deployment. For renamed timers, disable/retire the superseded units and enable the new units at their **original calendars**, guaranteeing no simultaneous active source push or receiver-prune timers. Preserve the accepted 0041 service-user path. Do not launch manual push, prune, receiver state migration or destructive operation without an explicit operator-reviewed invocation.
4. Capture post-deployment output/exit status from every installed read-only operator command on **both hosts**, actual timer/unit state, receiver agreed-parent read-back, retained snapshot counts, and absence of duplicate active units. Verify a routine scheduled cycle through normal evidence where needed; no unnecessary repeated large transfer.
5. Confirm persistent state identity, lock/hold/receipt protection, rollback readiness, Ansible idempotence and the updated source revision/commit mapping. Retire obsolete installed executable files/units only after all consumers have moved. Mark completion only after accepted correctness evidence; preserve prior records unchanged.
6. Write the final accepted feature report under `reports/`, recording any explicit internal state filename exception, output contract/schema decisions, and exact Git/host state. Mark steps **CLOSED** only on evidence acceptance; move this directory to `change-control/complete/` on formal feature closure.

**Evidence:** `evidence/Step 4/` — approved installation and migration outputs, host/timer/identity read-backs, negative privilege checks as applicable, rollback receipt and final acceptance.

## Rollback principles (must be executable, not merely asserted)

- Roll back the **paired** executable/template/unit changes through the correct Playbooks revision and inventory; disable replacement timer before restoring the old timer so that there is never more than one writer/pruner.
- Maintain 0041 dedicated sender/receiver identities, SSH restrictions and sender wrapper throughout rollback; never fall back to `richard` as a service account or grant blanket `sudo` privileges.
- For state filename migration, rollback must restore the **same validated parent/prior content**, with correct owner/mode/locks and no competing old/new records. No parent rebootstrap or snapshot deletion.
- Preserve published Diaries datasets, source snapshots, received snapshots, retention limits, holds, journals, receipts and historic evidence. Do not perform a production snapshot rollback, pruning or dataset restore as a routine means of rolling back operator-interface names.
- A clean Ansible/source rollback is a **plan** until its commands and read-back evidence have been captured and accepted.

## Command-safety convention

Commands supplied later must name their **execution terminal/host** and working directory, be copy/paste ready, and must not execute `set -e`, `set -u` or `set -euo pipefail` directly in an interactive Cygwin/SSH shell. If fail-fast is needed, isolate it in a subshell or standalone non-interactive script and report PASS/FAIL without closing the interactive terminal.
