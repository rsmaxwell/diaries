# Step 12.3 historical test cleanup — conservative revision

Run this tool from the **Diaries parent repository** on mango; it works on
`/home/richard/playbooks` but stores all archive evidence within this feature.

The previous 148-file dry run was too broad. This version considers **only
untracked**, explicitly named obsolete Step 12.3 prototype tests and matching
guides. All tracked/modified tests, native replication, retention and agreed
parent test families remain. New simplified tests must already exist before
`--apply` can be requested; operational acceptance is still required.

## Read-only plan — terminal SSH `mango`

```bash
cd /home/richard/diaries
python3 'change-control/in-progress/0040-FEAT - simplify native Btrfs snapshot retention and retire legacy backup storage/tools/retire-obsolete-playbooks-step12-tests.py' --playbooks /home/richard/playbooks --plan
```

Do **not** use `--apply` until the replacement regressions are accepted and
all paths in the plan have been reviewed. The tool performs no removal by
itself; a subsequent explicit `--apply` archives and checksum-verifies before
removing eligible untracked files. Repository status and SHA-256 are recorded.
