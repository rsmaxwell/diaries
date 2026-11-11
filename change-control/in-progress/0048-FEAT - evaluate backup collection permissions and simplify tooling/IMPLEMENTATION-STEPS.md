# 0048-FEAT — Implementation and acceptance steps

**Status:** PLANNED / NOT STARTED. **Do not execute until both 0046-FEAT and 0047-FEAT are formally CLOSED.** Prefer one coherent implementation and one consolidated verification, not a series of unnecessary deployments.

## Step 1 — Freeze the accepted baseline and map permission dependencies (OPEN / BLOCKED)

1. Read the formal 0046 and 0047 closure reports, original 0045 static installation baseline, and the accepted 0047 source-mode verification. Confirm both prerequisite feature directories are in `change-control/complete/` and both publication receipts are valid.
2. On **Windows Cygwin**, capture authoritative Diaries parent Git branch/full SHA/status, `.gitmodules` and `git submodule status`; on **`mango`**, capture the Playbooks checkout branch/full SHA/status, remotes, effective Ansible configuration and the post-0046 inventory entry point. Check for local modifications before making changes. Keep outputs in `evidence/Step 1/` under this feature.
3. Inventory all relevant sources and installed paths with contents' hashes, mode, owner/group, ACLs where present, symlink status, and execution/read/write users. Include the nine synced filters, five synced directories, and any adjacent executable scripts, templates or source entries with meaningful permissions. Derive actual target paths instead of assuming the old inventory.
4. Trace the Ansible `file`/`synchronize`/`template` task order, especially `0750` directory creation followed by archive-mode rsync; identify where source and destination permission decisions may conflict.

**Exit evidence:** full per-path baseline and permission-consumer matrix, frozen revisions and both prerequisite closure receipts. No production mutation.

## Step 2 — Determine minimum necessary permissions in a clean clone (OPEN / BLOCKED)

1. Create a disposable, clean Playbooks clone at the frozen published revision, using a normal Git checkout and **without** applying the 0047 restoration tool, copying preserved filesystem metadata from `mango`, or importing source-mode overrides. Keep one-off fixtures/results under 0048 `tests/` and `evidence/` (sync the Diaries repo to `mango` explicitly before running its tools there).
2. Compare fresh-clone source modes to 0047's historical `0664`/`0750` contract and examine the actual process users, ownership, group membership, ACLs and parent directories. Test necessary read, traverse, write, execute and no-unauthorised-access conditions for each affected class/path. A script executing only through an interpreter need not automatically have an executable bit; a directly invoked script does.
3. Exercise the two archive-mode rsync tasks and their surrounding Ansible directory-creation tasks in a disposable target; run at least twice. Assert that first-run changes are explained and the second run is genuinely idempotent, including modes, not just contents. In particular, reject directory-mode oscillation between `0750` and fresh-clone `0755`.
4. Document a path-by-path disposition: historical mode required, safely replaceable by ordinary clone mode, or unresolved. Treat group-write (`0664`) as something to justify, not something to preserve automatically; also assess whether relaxing directory traversal (`0750` to `0755`) exposes sensitive information.

**Exit evidence:** source-versus-installed mode matrix, clean-clone and repeated-run output, permission/security assessment and a proposed minimal design. Any unmet requirement remains a blocker to tool retirement.

## Step 3 — Implement one coherent, reversible simplification (OPEN / BLOCKED)

1. Prefer retaining `ansible.posix.synchronize` with native archive-mode permission propagation and **without** `--chmod` or `--no-perms`. Where ordinary clone modes satisfy documented requirements, revise affected Ansible directory-mode rules and permanent tests/documentation consistently so one playbook invocation converges and repeated runs are stable.
2. Retire the *active* 0047 source-mode restoration contract only if Step 2 proves it is unnecessary: remove `roles/backup-collection/source-modes.json` and references to it, replace/retire its special source-mode regression as appropriate, and delete the pre-deployment restoration requirement from active instructions. Do **not** delete or edit one-off 0047 historical tools/evidence in the already-closed Diaries feature.
3. If any mode not representable by Git remains mandatory, preserve the smallest transparent, per-path mechanism needed (or an equivalent explicitly reviewed design). Do not force a retirement outcome or introduce a blanket mode transformation; document why the tool remains necessary.
4. Produce a **Playbooks-only** repository-relative ZIP for permanent source changes, and a separate **Diaries-only** ZIP for feature tools/tests/reports. Apply via Beyond Compare 4. Stage/commit/push only intended changes; capture both source and rollback revisions. Do not assume `mango` and Windows repositories are synchronized.

**Exit evidence:** coherent reviewed source changes, focused source tests, syntax checks, and an explicit retain-or-retire decision. No service/backup dataset changes before controlled verification.

## Step 4 — Consolidated verification, rollback readiness and formal closure (OPEN / BLOCKED)

1. After checking the exact Playbooks revision, run one guarded normal deployment using the **post-0046 inventory** and accepted vault handling (`--vault-password-file ~/.vault_pass.txt` where needed), limited to the intended `backup-collection` scope on `mars` unless evidence requires another host. Capture the complete Ansible recaps and itemized changes; no unexplained changes are acceptable.
2. Re-run the same playbook to verify `changed=0`, `failed=0`, `unreachable=0`, including the two rsync tasks and directory-creation tasks. Reconcile installed content hashes, mode, ownership, ACLs, access checks and operational state with the Step 1 baseline, accepting only explicitly documented security-reviewed permission differences.
3. Check normal backup readers/writers and schedules read-only, verify snapshot/replication readiness and relevant marker/lock/pin invariants without generating, deleting, transferring or restoring snapshots. Reuse previously accepted destructive/end-to-end evidence rather than replaying those tests.
4. Confirm the intended outcome: fresh clone works without special metadata restoration **or** explain/verify the minimal retained mechanism. Validate the rollback route to the frozen Playbooks revision and applicable permission state; preserve receipts in `evidence/Step 4/`.
5. Record the full final acceptance, update Step states to CLOSED, commit/push accepted evidence and change control in the authoritative Windows Diaries repo; only after formal acceptance move all of 0048 to `change-control/complete/` and publish the closure commit.

**Stop conditions:** either prerequisite not closed, unresolved security exposure, permission/ACL drift outside approved scope, repeat-run Ansible changes, source-mode dependency not correctly handled on a fresh clone, secrets in evidence, or unverifiable rollback. Do not claim PASS or close on proposed commands alone.
