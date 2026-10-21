# Step 4 Cygwin regression launcher

From a **Cygwin** terminal, change to the **Diaries repository root** (`.../diaries`) and run:

```bash
bash "change-control/in-progress/0037-FEAT - unify legacy Snapper and timestamp snapshot retention/tests/step04-run-from-cygwin.sh"
```

This streams `step04-plan-regression.py` to `richard@mango` via SSH and runs it
against `/home/richard/playbooks/roles/snapshots/files/btrfs-snapshot-manager.py`.
Python is needed on `mango`, **not** on Windows. It does not deploy code, create
remote temporary files, modify snapshots or invoke pruning.

If your SSH host alias or remote checkout differs:

```bash
STEP04_SSH_HOST=mango STEP04_PLAYBOOKS_DIR=/home/richard/playbooks \
  bash "change-control/in-progress/0037-FEAT - unify legacy Snapper and timestamp snapshot retention/tests/step04-run-from-cygwin.sh"
```

If the regression fails because `legacy_plan` is missing, update the Playbooks
checkout on `mango` with the Step 4 manager source before rerunning. The launcher
exits nonzero on SSH, Python or assertion failure; success prints the regression's
`PASS:` line followed by a launcher completion line.
