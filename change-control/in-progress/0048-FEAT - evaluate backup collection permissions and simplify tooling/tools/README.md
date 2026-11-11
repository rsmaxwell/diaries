# 0048 — Feature-specific tools (planned)

No tool implementation or deployment is included in the planning ZIP. Add only the one-off verification needed to evaluate permissions, with tools under this directory, test fixtures under `../tests/`, and raw sanitized evidence under `../evidence/Step N/`. Do not create permanent temporary directories outside the Diaries feature or add one-off logic to Playbooks roles.

Expected tools at implementation time:

- Read-only inventory of actual modes/owner/group/ACL, source hashes and Git index executable bits (mango and mars); avoid credentials, file contents and decrypted inventory in logs.
- Disposable fresh-checkout setup and a two-iteration rsync + Ansible-directory-order test, requiring unchanged second-run metadata.
- Focused user/group access checks and security-delta report, without manually changing live ACLs or backup data.
- Guarded consolidation verifier and static installed-state comparator, reusing accepted 0045/0047 collectors where appropriate; preserve post-0046 inventory handling.

**Execution:** Windows Cygwin is the authoritative Diaries editing location; `mango` is the Playbooks working checkout and Ansible controller. If running feature scripts on `mango`, explicitly synchronize the feature files into `/home/richard/diaries` first. Run Ansible using its then-current accepted inventory configuration (without redundant `-i`) and `--vault-password-file ~/.vault_pass.txt` where required.

Check Git branch/revisions/uncommitted changes and submodule pins before changing code or running repository-backed tools. Scripts must refuse symlinks/unexpected paths and stop visibly on failures. If invoking an interactive SSH/Cygwin terminal, do not paste standalone `set -e`, `set -u` or `set -euo pipefail`; isolate fail-fast logic in scripts or a subshell with explicit PASS/FAIL. Preserve rollback instructions and evidence within this feature.
