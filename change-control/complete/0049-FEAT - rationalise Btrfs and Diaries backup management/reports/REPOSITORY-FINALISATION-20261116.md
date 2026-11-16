# 0049 — Repository finalisation procedure (16 November 2026)

**Technical gates:** accepted. **Git publication and formal closure:** pending.

## Commit order and ownership

1. On **`mango`**: verify the current Playbooks branch/revision, and stage **only the 32 approved 0049 source files**. `tools/verify-and-stage-0049-playbooks.py` is a feature-only helper; it checks file SHA-256 against the authoritative final 0049 three-ZIP overlay and refuses unknown pre-staged changes. Never stage `__pycache__/`, credentials or private inventory. The helper is read-only unless explicitly called with `--stage`.
2. Review `git diff --cached --check`, `git diff --cached --stat` and `git diff --cached` for 0049-only source. Commit Playbooks: `0049-FEAT: rationalise Btrfs and Diaries backup management`. Record `git rev-parse HEAD`.
3. On **`mango`** in `/home/richard/ansible-controller`: inspect `git status --short`, `git submodule status`, `.gitmodules`, then stage only the `playbooks` gitlink. Do **not** stage or alter the private `inventory` submodule. Commit the updated Playbooks pin and record controller revision.
4. On **Windows Cygwin** in the authoritative Diaries parent checkout: verify branch, dirty files and pinned application submodules, confirm all prior evidence ZIPs were applied, then stage only the existing `change-control/in-progress/0049-FEAT - rationalise Btrfs and Diaries backup management/` directory. Commit accepted evidence, technical reports and this finalisation record; record the new Diaries parent revision. Do not move the directory to `complete/` yet.
5. Push child Playbooks commit before publishing the Ansible-controller parent commit that points to it. Only push the current checked branches after checking remotes/upstream; do not force-push. Push Diaries evidence via its normal reviewed workflow.
6. Create `reports/REPOSITORY-REVISION-RECORD.md` from actual commit hashes, deployed unit names and rollback baseline; include actual command output in `evidence/Step 4/` in this **Diaries** parent feature. Request explicit formal closure acceptance, then and only then move `in-progress/0049-FEAT ...` to `complete/0049-FEAT ...` and commit that move in the Windows Diaries parent.

## Safety requirements

- Do not use `git add -A`, `git reset --hard`, `git clean -fd` or blanket staging. Avoid deleting ignored/untracked `__pycache__/` automatically.
- Source hashes for all 32 files must match the final approved overlays before staging. If a local file differs, stop and reconcile it rather than silently including an unrelated edit.
- Refuse staged changes outside these 32 files. No secrets, inventory vault data or local runtime state belong in public Playbooks Git.
- Do not repeat the accepted Btrfs send, live prune or restore as a prerequisite for repository bookkeeping.
- All commands must identify their terminal/host and working directory. No interactive `set -e`.

## Source of revision values

The current logs establish the **pre-commit** Playbooks `main` HEAD `0904bc7ebe801e391a3aa4dc59bbc9ccc7dfa532`, but **do not establish** the final Playbooks, Ansible-controller or Diaries commits. The helper cannot infer them. Keep these values pending until the actual commits finish.
