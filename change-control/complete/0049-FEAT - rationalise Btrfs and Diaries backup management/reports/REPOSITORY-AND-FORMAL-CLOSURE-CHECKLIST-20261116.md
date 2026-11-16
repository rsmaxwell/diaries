# 0049 — Repository and formal closure checklist (16 November 2026)

**Technical acceptance:** complete. **Administrative closure:** pending revision manifest, Git publishing and explicit operator acceptance.

## Required finalisation

1. On **`mango`** in `/home/richard/ansible-controller/playbooks`, record `git branch --show-current`, `git rev-parse HEAD`, `git status --short`, `git diff --check`, and identify the committed Playbooks implementation revision after checking all staged files. Exclude generated `__pycache__/` directories and any secrets, and preserve unrelated dirty files. No commit is claimed in this report.
2. In the **`mango`** Ansible-controller parent `/home/richard/ansible-controller`, record `git status --short` and `git submodule status`. Make deliberate submodule pin updates only after reviewing the child commits. Check the private inventory submodule without copying vaulted contents to public Playbooks records.
3. In the **Windows Cygwin terminal** at `/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries`, check `git branch --show-current`, `git rev-parse HEAD`, `git status --short`, and `git submodule status`; confirm all 0049 reports/raw logs appear in `change-control/in-progress/0049-FEAT - rationalise Btrfs and Diaries backup management/` and are committed in the parent Git repository.
4. Record the exact final Git commits, host-specific installed configuration and rollback reference in a final revision/rollback manifest. Rollback must preserve 0041 identities/forced-command gates and the existing agreed-parent state; never reset `.simple-*` recovery files. No live rollback is required when safe rollback readiness is documented and tested in accepted fixtures.
5. Reconcile outdated status wording in the 0049 README/IMPLEMENTATION-STEPS/ACCEPTANCE-MATRIX with these accepted results, and only mark each step **CLOSED** after its evidence is formally accepted.
6. On explicit formal feature approval, move the 0049 directory to `change-control/complete/0049-FEAT - rationalise Btrfs and Diaries backup management/` and commit the relocation in the **Windows Diaries parent**.

## Useful read-only commands

**mango SSH terminal — Playbooks checkout:**

```bash
cd /home/richard/ansible-controller/playbooks
git branch --show-current
git rev-parse HEAD
git status --short
git diff --check
git diff --stat
```

**mango SSH terminal — Ansible-controller parent:**

```bash
cd /home/richard/ansible-controller
git status --short
git submodule status
```

**Windows Cygwin terminal — Diaries parent:**

```bash
cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries
git branch --show-current
git rev-parse HEAD
git status --short
git submodule status
```

Do not invoke unscoped `git add -A` or auto-commit without checking unrelated existing work first.
