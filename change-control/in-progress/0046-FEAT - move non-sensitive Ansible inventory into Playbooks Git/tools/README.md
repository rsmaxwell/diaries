# 0046-FEAT — One-off inventory migration and verification tools

**Planning only.** No scripts were produced or executed, and no inventory, Playbooks roles, Vault files or installed systems were modified by creation of this feature.

When 0045 closes, create feature-specific inventory-discovery, **complete host/playbook coverage**, secure effective-variable diagnostic comparators, controller-configuration readback and **all-host installation-result** collectors here, with non-production test harnesses under `../tests/`. Prefer reusing accepted 0045 installed-state collectors for `mars`/`backup` while extending the same comparison standards to every other managed host.

**Protect secrets:** never persist plaintext Vault values, passwords, private keys, encrypted Vault files or credential-bearing rendered configuration in tools, ZIPs or evidence. Any effective-variable diagnostics must keep protected values in trusted memory and output only redacted findings; equal values/precedence are not independent acceptance requirements. The per-host installed result and security behaviour must still be identical. Do not dump raw `ansible-inventory --list/--host` results into a report. All evidence in `../evidence/Step N/` must be sanitised before entering Diaries Git.

Tools run on `mango` from `/home/richard/diaries` only after the new feature tools have been explicitly synchronised from the authoritative Windows Diaries checkout. The permanent Playbooks repository remains `/home/richard/playbooks` on `mango`. Avoid extra temporary execution/evidence roots and permanent ad hoc logic in Ansible roles.

Include explicit terminal/host labels and reliable PASS/FAIL exit-status handling. Never run standalone `set -e`, `set -u` or `set -euo pipefail` inside interactive Cygwin or SSH shells. Preserve before/after receipts and rollback evidence. The normal post-migration operator Ansible commands must use repository `ansible.cfg` without a redundant `-i`, except a comparison tool may explicitly select each source.
