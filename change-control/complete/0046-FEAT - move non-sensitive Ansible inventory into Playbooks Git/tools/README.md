# 0046-FEAT — Feature-local migration and verification tooling

All tools for controller baseline discovery, private repository staging, no-secret leakage checks, host/playbook coverage, side-by-side comparison, cutover and rollback belong in this 0046 directory. Do not store permanent implementation evidence under `/home/richard`, `/home/richard/playbooks` or external temporary directories.

**Execution:** The authoritative Diaries checkout is on Windows. Scripts for `mango` must be explicitly transferred/synchronised before being run from `/home/richard/diaries` or piped over SSH from Windows Cygwin. Ansible executes on `mango` with its default effective inventory; explicit `-i` is appropriate only within labelled old/new comparison tests. Include `--vault-password-file ~/.vault_pass.txt` when required.

**Secrets:** Only safe/sanitised receipts go into Diaries Git. Do not emit `ansible-inventory --list` or `--host` decrypted output to terminal logs, use `tee` on command output that may contain secrets, or materialise plaintext credentials outside trusted local processing. The full private inventory, including encrypted Vault files, belongs in the **private inventory Git repository**, never in this feature archive, public Playbooks or the controller parent. The Vault password is not Git-managed.

**Code safety:** Check live branches, SHAs, submodules, working trees and remotes before staging; preserve local uncommitted files. Use fail-fast only inside standalone scripts or subshells, never directly in the user's interactive shell. Report PASS/FAIL on failed checks and retain rollback evidence.

Current state: planning amendment only. Do not run a cutover or create remote repos until Step 1 live discovery and remote access/visibility have been checked.
