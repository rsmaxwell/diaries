# 0046-FEAT — Planning source review (10 November 2026)

**Status:** design evidence; **not a live inventory audit or operational acceptance**.

## Sources reviewed

- Uploaded Playbooks source bundle `playbook-sources-20261110-180604.zip`, provided for this Diaries work. It contains `playbooks/AGENTS.md`, `.gitignore`, Btrfs roles, operator playbooks and `MAINTENANCE-SCHEDULE.md`; it does **not** include the actual external `/etc/ansible` inventory. We cannot infer its complete file list, secret distribution, active `ansible.cfg` or variable precedence from that archive alone.
- Planned `0045-FEAT - reorganise backup and Btrfs Ansible deployment/` ZIP, including `README.md`, `IMPLEMENTATION-STEPS.md` and `INSTALLATION-EQUIVALENCE-CONTRACT.md`. This explicitly defers 0045 until 0039 and 0043 close, keeps the authoritative inventory under `/etc/ansible` throughout 0045, and requires installed-state equivalence.
- Accepted 0043 maintenance scheduling evidence discussed in this project: `/etc/ansible/group_vars/all/btrfs-maintenance-schedule.yaml` was the *single operational schedule source*; 0043 deliberately did **not** create a duplicated Playbooks inventory. Its actual effective **then-current** values must be re-read after 0045, rather than assumed fixed for 0046.
- Accepted 0044 closure evidence: Playbooks `main` commit `7dfa93fef6d975aa82f5f4cfdf54497b106e7645` and Diaries commit `30eeb2e71bfa0de9030eefcef009e06a4e27d572`, both published on 10 November. 0044 left three maintained regression tests `verify-replication.py`, `verify-protection.py`, `verify-shared-retention.py`.
- Official Ansible documentation for configuration-file search order, host/group vars discovery and variable precedence. Relevant URLs are linked in `SECRETS-AND-DISCOVERY-DESIGN.md`.

## Grounded observations

1. The Playbooks `AGENTS.md` instructs maintainers to inspect `/etc/ansible/hosts`, `/etc/ansible/group_vars/`, `/etc/ansible/host_vars/` and effective inventory overrides because role defaults are not necessarily effective values.
2. `MAINTENANCE-SCHEDULE.md` explicitly identifies `/etc/ansible/group_vars/all/btrfs-maintenance-schedule.yaml` as authoritative. Its operator commands assume the current controller's standard inventory.
3. In the reviewed Playbooks source bundle no repository `inventory/` or repository-root `ansible.cfg` was supplied; this is **not** evidence that a config cannot exist on `mango` after the source export or be supplied via environment/home/system locations.
4. The then-current role structure and playbook entry points may change under 0045. Therefore a fixed list of roles/launchers from the source bundle must **not** be used as 0046's implementation or installed-baseline manifest.
5. Variable precedence is a material **diagnostic risk**, not a required equality property. In particular, encrypted variables moved from inventory `group_vars`/`host_vars` to `vars_files`/`include_vars` can resolve differently; such differences need investigation and proof that the installation and security behaviour are unchanged for every affected host.

## Information unavailable until 0045 closes / Step 1 is performed

- Full current `/etc/ansible` tree: host/group hierarchy, the number of Vault files, embedded encrypted values, any plaintext secrets, plugin sources, configuration precedence and duplicate variable definitions.
- Which launcher, cron, CI or operator invocation chooses what Ansible config and inventory, and from which working directory.
- The accepted then-current Playbooks SHA, Ansible version, full managed-host/playbook coverage, effective-variable diagnostics and installation-result baselines **for every managed host**, including `mars` and `backup`.
- Which secure external Vault-loading arrangement will produce the required unchanged installed results on the whole estate, with or without identical variable precedence.

**Do not mark any 0046 acceptance check as passed using only this source review.** The initial task is a read-only audit after 0045 closure and freeze of the actual operational inputs. If findings contradict this proposed layout, update the design before making changes.
