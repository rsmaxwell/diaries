# 0049 — Integrated source implementation and consolidated regression report

**Date:** 2026-11-16 UTC
**Status:** SOURCE IMPLEMENTED AND SOURCE REGRESSION PASS; deployment and live acceptance NOT STARTED.

## Baseline and source authority

Authoritative latest upload used for this implementation:

- Diaries bundle `diaries-sources-20261116-113517.zip`; parent checkout branch `main`, HEAD `b3bb0b5471128204c425b0cc0ae21bc717d774e1`; untracked `change-control/in-progress/` containing 0049 feature. Submodule commits: diaries-client `e45ae170017fdf4974f642f654d7f709269af711`, diaries-responder `bd65d08435c0f5d240337cd6479cb41befe4d8c1`, diaries-web `cc147426e93ee6952558b65147e444d38316b3ce`.
- Playbooks bundle `playbook-sources-20261116-113514.zip` from `/home/richard/ansible-controller` on `mango`: parent HEAD `e3252278c0daad974a84c8a145edee4a229fd4fd`, playbooks submodule branch `main` HEAD `0904bc7ebe801e391a3aa4dc59bbc9ccc7dfa532`, inventory submodule `ebcce026723db37b9b53b76ba21903a351d48466`. All reported clean; **private inventory content was intentionally excluded**.
- No actual SSH/Ansible, Btrfs, service or snapshot operations have been performed against `mars` or `backup` during this source implementation. No production state altered or acceptance gate closed.

## Implemented changes

1. `diaries-backup-status`: exclusively retained dataset IDs, logical dataset, manifest identity, retained occurrence count/range, recent titled table, JSON; no longer invokes manager status, Diaries pull marker or replication preflight. `diaries-backup-history` preserves `path` as one line; `list`, `list --all` and `show` have dynamically sized tables, readable headings and indented operator JSON.
2. New `btrfs-backup-status`: source/receiver sections, current local agreed parent/prior, source accepted publication marker, full sender preflight only when not `--local-only`, receiver local status, qgroups, retention, snapshot inventory, systemd service/timer observations, and explicit unknown last-verified-transfer semantics. JSON has schema 1 and documented 0/1/2 health semantics.
3. New active runtime `btrfs-replication`; existing protocol implementation is **identical except** executable constant and pretty-print for interactive sender status. Receiver wire replies remain compact. All runtime calls through 0041 sender wrapper and receiver gate now point to neutral executable, without changing sudoers/forced SSH dispatch privileges or key material.
4. New active `btrfs-push.{service,timer}` and `btrfs-receiver-prune.{service,timer}` with existing calendars and max deletes from effective inventory. Ansible task order installs runtime/gates before timer cutover, stops old timer first, refuses an in-flight old service, enables new timer, then removes obsolete installed units/binary. Receiver retention remains independently gated. Source snapshot-manager pruning and receiver pruning use common `prune --dry-run` and `prune --max-delete N` syntax; receiver deletion method retains all existing identity/hold/journal checks. Uncapped manual prune and `run` not exposed, and old receiver management CLI collisions are removed.
5. `btrfs-snapshot-manager status` no longer displays Diaries marker (snapshot creation still validates that marker). List, hold and prune previews use titled tables. `btrfs-backup-status` and `diaries-backup-status` group data by responsibility.
6. Existing internal `.simple-agreed-parent.json` and `.simple-prune-pending.json` paths deliberately **not migrated**. Existing filenames have recovery significance and a cosmetic rename offers no safety/correctness improvement. Internal helper names, archived historic test names and accepted historical feature reports remain unchanged.
7. New neutral Ansible vars read the old inventory key as a **temporary fallback**, because private inventory was not present in the bundle. This prevents an implicit false/off default from stopping the approved timers when the role is first applied. The inventory submodule must be reviewed and migrated explicitly, including confirming both hosts' schedules/identities/max-delete values. No secrets are included in packages.

## Source regression executed in isolated build container

The following existing and new tests completed with exit status zero:

- `roles/snapshots/tests/verify-btrfs-snapshot-manager.py`
- `roles/snapshots/tests/verify-diaries-backup-history.py`
- `roles/snapshots/tests/verify-diaries-backup-status.py` (rewritten for 0049 scope)
- `roles/snapshots/tests/verify-0040-step13-source-prune-cap.py` (now verifies refusal of uncapped deletion; 0045 split-task fixture corrected)
- `roles/snapshots/tests/verify-0040-simplified-receiver-retention.py` (display assertions updated only)
- `roles/snapshots/tests/verify-0040-agreed-parent-prune-guard.py`
- `roles/btrfs-replication/tests/verify-0041-restricted-identity.py`
- `roles/btrfs-replication/tests/verify-replication.py`
- `roles/btrfs-replication/tests/verify-shared-retention.py`
- `roles/btrfs-replication/tests/verify-protection.py`
- `roles/btrfs-replication/tests/verify-0049-backup-management.py` (19 new cases)

Further source validation: YAML parsed with PyYAML, active Jinja templates parsed, and Python AST parsed. 0049 unit tests verify the exact old/new replication source diff to ensure no protocol/algorithm drift.

**Evidence:** `evidence/source-regression/REGRESSION-LOG-20261116.txt` captures the raw consolidated test output. No hosted integration, `ansible-playbook --check`, scheduled timer run, production read-back or retention deletion was performed here.

## Live prerequisites and deployment decision

**Do not deploy production from the package without a reviewed effective inventory and source revision check.** In particular:

- Confirm that the new neutral variable families resolve to the actual existing values from private `inventory`, including the 03:30 UTC push schedule, 04:15 UTC receiver prune schedule and maximum 10 receiver deletions. Confirm `btrfs_sender_service_identity == dedicated`, installed root-owned gates, and unchanged 0041 sudoers/forced SSH policy.
- Apply changes to Playbooks on `mango` and the feature evidence/docs to the Windows Diaries parent repository with Beyond Compare 4. Inspect uncommitted changes before overwriting local work. `git status` and `git submodule status` must be recaptured at deployment.
- Run source tests on **mango**, then `ansible-playbook btrfs-replication.yaml --limit 'mars,backup' --check --diff --vault-password-file ~/.vault_pass.txt` with its default configured inventory. Review changes for both roles and ensure no unrelated configuration is altered.
- Deploy `backup` first and then `mars` in a safe window, only if the old push and receiver-prune services are inactive. New runtime/gates are installed before new timers are activated, and the timer changes fail closed if an old service is active.
- Capture the post-deployment local and cross-host statuses, parent/prior identity and SHA256 read-back, schedule/next timer, new/old unit active/enabled states, service identity and sudoers/forced command, source and receiver prune plan, JSON parse and a scheduled regression without duplicating a completed transfer. Use `tools/verify-0049-live-readonly.sh` **only after** synchronising the feature from Windows Diaries to `mango`.
- Rollback: preserve original Git commits and inventory, stop new timers, reinstall former package and old executable/wrappers, re-enable only former timers, verify no dual active timers. Never reset agreed-parent state, snapshot data or receiver prune journals. A supervised rollback does not require deleting or rebootstraping Btrfs data.

**Not yet accepted:** host executable deployment, actual inventory migration, Ansible source/integration check on `mango`, receiver/endpoint read-back, one-timer invariant on hosts, live status JSON, rollback evidence, feature closure. Keep this directory in `in-progress`.

**Packaging evidence:** `reports/PLAYBOOKS-CHANGE-MANIFEST-20261116.md` records the 32 Playbooks files and SHA256 values; `reports/APPLY-AND-VERIFY-20261116.md` provides the safe operator handoff. Final source regression includes 19 new 0049 test cases.
