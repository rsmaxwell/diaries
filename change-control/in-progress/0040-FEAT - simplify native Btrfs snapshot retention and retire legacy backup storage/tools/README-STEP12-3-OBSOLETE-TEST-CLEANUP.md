# Retire obsolete Playbooks Step 12 tests

The following commands run on **mango**, after the new Diaries feature files have been synchronised to `/home/richard/diaries`. The tool does **not** touch operational Playbooks role files or Btrfs snapshots. It archives the actual current bytes of each selected test to the Diaries feature `tests/retired-step12-3/` directory before removing tests from `/home/richard/playbooks`.

**Terminal: SSH to mango — inspect repository status and plan first**

```bash
cd /home/richard/playbooks
git branch --show-current
git rev-parse HEAD
git status --short
cd /home/richard/diaries
python3 'change-control/in-progress/0040-FEAT - simplify native Btrfs snapshot retention and retire legacy backup storage/tools/retire-obsolete-playbooks-step12-tests.py' --playbooks /home/richard/playbooks --plan
```

Review every selected filename. In particular, ensure the new simplified regression suite has replaced the rejected staged architecture tests, or accept reduced test coverage temporarily.

**Terminal: SSH to mango — archive and remove selected test scripts only**

```bash
cd /home/richard/diaries
python3 'change-control/in-progress/0040-FEAT - simplify native Btrfs snapshot retention and retire legacy backup storage/tools/retire-obsolete-playbooks-step12-tests.py' --playbooks /home/richard/playbooks --apply
if [ "$?" -eq 0 ]; then
  echo 'PASS: obsolete test sources archived before removal'
else
  echo 'FAIL: test cleanup; inspect output before retry'
fi
cd /home/richard/playbooks
git status --short
```

Review the Playbooks deletions in Beyond Compare 4 and bring the new Diaries archive/manifest back into the primary Windows checkout. Do not delete earlier Step 12 feature evidence or the native/pruning test suites. Do not run this as part of Ansible production tasks.
