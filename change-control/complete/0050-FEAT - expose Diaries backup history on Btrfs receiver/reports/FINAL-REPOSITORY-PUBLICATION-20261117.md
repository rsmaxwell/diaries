# 0050 — Final Playbooks and Ansible-controller publication report

**Date:** 17 November 2026

**Status:** Operational and two-repository publication acceptance PASS; Windows Diaries evidence publication and separate formal closure still pending.

## Verified publications

| Repository | Initial 0050 revision | Final revision | Verified state |
| --- | --- | --- | --- |
| Public Playbooks (`rsmaxwell/playbooks`) | `a1f27ddf20e6c9668c6ad8f0d801de0233695ccc` | `b0063d455faf4b264504405f9db72ab21c692741` | Pushed to GitHub `main`; remote SHA read-back PASS |
| Private Ansible-controller (`rsmaxwell/ansible-controller`) | `4a161f08815819cce1a72bb89deaf82ef8aecb27` | `28e394b48ba91479b147452d70adb39ff3b84559` | Pushed to GitHub `main`; remote SHA read-back PASS |
| Private inventory submodule | — | `ebcce026723db37b9b53b76ba21903a351d48466` | Unchanged |

The initial Playbooks publication contained eight intended source paths. It also unintentionally changed the Git executable mode of `roles/snapshots/files/diaries-backup-history.py` from `100755` to `100644`; that mode change did **not** affect the already deployed executable, because Ansible installs it as mode `0755`. The subsequent Git commit `b0063d455faf4b264504405f9db72ab21c692741` changed **only** this mode back to `100755` and reported 0 insertions, 0 deletions. Controller `28e394b48ba91479b147452d70adb39ff3b84559` pins this corrected revision. The two original operator logs are retained unchanged.

The final operator log reports:

```text
0050 FINAL PLAYBOOKS: b0063d455faf4b264504405f9db72ab21c692741
0050 FINAL CONTROLLER: 28e394b48ba91479b147452d70adb39ff3b84559
0050 MODE CORRECTION AND PUBLICATION: PASS
0050 FINAL SOURCE PUBLICATION: PASS
```

## Operational acceptance retained (no rerun necessary)

- Receiver `diaries-backup-history` and `diaries-backup-status` both installed and independently read the `backup` snapshot repository.
- Real selected receiver backup `production/20261116-003112Z` in snapshot `20261116-150008Z`: schema-2 content verification PASS, 128 files.
- `backup` reported 30 distinct Diaries backups in 42 retained occurrences with zero conflicts; Btrfs infrastructure HEALTHY, no stale qgroups in the accepted check.
- Strict Ansible reapply on `backup`: `ok=37 changed=0 unreachable=0 failed=0`.
- Independent histories: `mars` 22 distinct backups/77 occurrences; `backup` 30/42; 19 shared identities, 11 receiver-only, 3 source-only. Receiver-only discovery requirement proven on live data.
- No backup data mutation, receiver prune, restore or transfer was required for publication or mode correction.

## Remaining change control

1. Commit and publish 0050 history/evidence in authoritative Windows Diaries parent repository, retaining all preceding source/regression/deployment and failure logs.
2. Record the resulting Diaries GitHub revision and submodule state.
3. Obtain separate formal closure approval, mark accepted steps CLOSED, move entire feature directory from `in-progress` to `complete` and publish the relocation.

**Do not infer formal closure from publication.** The feature remains IN PROGRESS.
