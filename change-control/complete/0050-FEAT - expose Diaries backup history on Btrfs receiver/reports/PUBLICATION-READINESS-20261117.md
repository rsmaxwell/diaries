# 0050 — Publication readiness (17 November 2026)

**Ready for controlled repository finalisation.** No additional Playbooks operational change is required from this report.

## Scope to publish

Only these eight intended Playbooks source paths form the 0050 implementation (from the prepared source and correction packages):

1. `roles/btrfs-replication/README.md`
2. `roles/btrfs-replication/tasks/native.yaml`
3. `roles/btrfs-replication/tasks/receiver-diaries-history.yaml`
4. `roles/btrfs-replication/templates/btrfs-receiver-manager.json.j2`
5. `roles/btrfs-replication/tests/README.md`
6. `roles/btrfs-replication/tests/verify-0050-receiver-history-contract.py`
7. `roles/snapshots/files/diaries-backup-history.py`
8. `roles/snapshots/files/diaries-backup-status.py`

Expected published 0049 Playbooks baseline before 0050: `a2508ad61f479c1b2bc20cb39896006c1f2906e1` on `main`. `ansible-controller` at `a81eafdf1fccf6bcd7d9d1b3dfa77143872682e8` pins that Playbooks baseline; private inventory commit `ebcce026723db37b9b53b76ba21903a351d48466` remains unchanged. Verify actual branches, remotes, ancestry, working-tree changes, staged paths and submodule pointers before any commit or push. No `__pycache__/` directories should be staged.

After publishing Playbooks, stage its **gitlink only** in private `ansible-controller`, commit and publish that parent. Then commit/publish the authoritative Windows Diaries feature evidence. Preserve original operator logs and current user-local work. No git operation is claimed completed by this readiness report.

**Closure:** All operation/acceptance results are compatible with formal closure, but retain `change-control/in-progress/0050-FEAT - expose Diaries backup history on Btrfs receiver/` until separate approval to mark CLOSED and relocate.

## Publication progress receipt — 17 November 2026 (supersedes the earlier readiness state)

- Initial Playbooks commit/push: `a1f27ddf20e6c9668c6ad8f0d801de0233695ccc`; initial Ansible-controller commit/push: `4a161f08815819cce1a72bb89deaf82ef8aecb27`.
- Source executable-mode-only correction, Playbooks commit/push: `b0063d455faf4b264504405f9db72ab21c692741`.
- Final Ansible-controller commit/push: `28e394b48ba91479b147452d70adb39ff3b84559`. It pins corrected Playbooks; private inventory `ebcce026723db37b9b53b76ba21903a351d48466` unchanged.
- Both publications verified against `origin/main` by `git ls-remote`; logs retained verbatim in `evidence/Step 4/`.
- The original readiness section above describes pre-publication conditions and is preserved for historical traceability.
- **Remaining:** Windows Diaries publication, final receipts, and formal closure approval.
