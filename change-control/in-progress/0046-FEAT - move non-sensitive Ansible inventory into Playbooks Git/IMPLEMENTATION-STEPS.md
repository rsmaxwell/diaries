# 0046-FEAT — Implementation steps and acceptance gates

**All steps remain OPEN.** The three-repository architecture of 11 November 2026 supersedes the former public-inventory/external-Vault implementation. Prefer one coherent migration and one consolidated all-host verification rather than many trial deployments.

## Step 1 — Freeze current controller, source, inventory and installed estate (OPEN)

- Verify the published 0045 and 0047 closure receipts, the authoritative Windows Diaries `main` revision, and the actual `mango` Playbooks branch, SHA, clean/dirty state and origin. Do not infer current revisions from the 11 November source archive; discover live state.
- Read-only inventory of `/etc/ansible`, its actual effective configuration, Vault files and inline encrypted values, owner/modes/ACLs, external paths, inventory plugins, static/dynamic sources and every environment override. Classify every candidate as public metadata, private plain inventory data, genuinely Vault encrypted material, plaintext secret or unknown. Resolve unknowns before migration; no raw secrets in evidence.
- Catalogue all managed hosts, groups, all applicable playbooks and host/tag/limit combinations, SSH/become settings, wrapper scripts, CI and systemd/cron callers. Include all hosts, not only `mars`/`backup`.
- Capture estate-wide per-host installation baselines using repeatable collectors: managed asset hashes, owner/mode/ACL, packages, services, units/timers, schedules, mounts, SSH/sudoers, intended absent paths and secure sensitive-result comparison. Reuse accepted 0045 tooling for Btrfs endpoints where applicable; mutable backup/application data is out of scope.
- Freeze **one Playbooks installation-producing source SHA** for old/new inventory comparison. Verify remote privacy and access plans for the two proposed private repositories before any push.

**Evidence:** `evidence/Step 1/` scrubbed inventory map, Git/config/coverage receipts and every-host baseline. **Gate:** complete classification, host/playbook coverage and accepted baseline; unmeasured hosts remain open.

## Step 2 — Establish private controller parent and complete private inventory submodule (OPEN)

- Confirm/create a **private** `ansible-controller` parent and a **private** `ansible-inventory` repository (names proposed, verify before use). Reuse the existing **public** `ansible-playbooks` repository without rewriting its history.
- Create a new parent checkout on `mango`, proposed `/home/richard/ansible-controller`, with `playbooks/` and `inventory/` Git submodules. Pin the accepted Playbooks revision and a reviewed private inventory revision; record `.gitmodules` URLs and each Git SHA.
- Migrate the **entire** old inventory into the private submodule with its relative group/host variable scope. Whole-file encrypted Vault files and inline encrypted values can be committed to the **private** repo only after checking they are genuinely encrypted. Plaintext secret fields, Vault password, private keys and credentials stay **outside every Git repository**; where needed, encrypt plaintext credentials before first private commit and verify the result without displaying values.
- No Vault data or inventory is added to the public Playbooks repo. Confirm `.gitignore` does not hide required inventory files and no Git submodule points at an unverified or mistakenly public destination. Keep `/etc/ansible` and the existing `/home/richard/playbooks` checkout unchanged and usable as rollback references.
- Prepare reversible `/etc/ansible/ansible.cfg` inventory-path changes (preserving existing effective options), controller bootstrap and private-repository SSH permissions. Do not activate until estate-wide equivalence is viable. Audit playbook-root variable locations and caller working directories.

**Evidence:** `evidence/Step 2/` reviewed source classification/commit manifests, private/public remote visibility checks, parent/child Git SHA receipts, exact inventory file mapping, secret-safe negative tests and rollback procedure. **Gate:** staged reproducible parent/submodules and no plaintext secrets or Vault in the public repository.

## Step 3 — One consolidated estate-wide old/new acceptance (OPEN)

- Use the same frozen Playbooks code SHA, Ansible version, collections and flags on both sides. Compare **every** host and applicable playbook/host/tag/limit selection under explicitly selected old and staged inventories. Variable equality and precedence are diagnostics; the binding test is identical installed result and secure behaviour.
- Compare protected variables only inside trusted processes; write PASS/FAIL, no decrypted YAML, Vault ciphertext or private inventory payload in Diaries evidence. Missing/invalid Vault password or wrong repo permissions must fail clearly rather than silently substitute defaults.
- For each host/playbook, compare complete installation-producing outputs and managed static installed-state manifests; where necessary perform controlled, non-destructive applications, then check idempotence, security, package/unit/timer/ACL and schedule parity. Unverified hosts or unexplained deltas remain OPEN.
- Run the maintained backup/Btrfs regression suite and validate `mars` and `backup` agreed-parent protections and read-only health, plus every other managed host's contracts. No manual Btrfs pruning, snapshot deletion, replication or restore for this feature.
- Validate the operational `cd`, CI, Jenkins, systemd/cron and SSH caller matrix against the proposed new path. Verify fresh `--recurse-submodules` clone and normal Ansible Vault discovery, with the password outside Git.

**Evidence:** `evidence/Step 3/` all-host/playbook matrix, sanitised comparisons, regression and controlled deployment logs, accepted zero-installation-delta receipt, reproducibility and failure-mode tests. **Gate:** zero unexplained installation/security differences on every managed host and applicable playbook.

## Step 4 — Reversible activation, Git publication and formal closure (OPEN)

- Review the staged change and rollback package; publish the **private inventory child**, **public Playbooks child if its operational docs/scripts change**, then update/publish the **private parent submodule pins**. Record full Git SHAs and check actual remote visibility and access without leaking credentials.
- Activate the new inventory location through the *actual effective* Ansible config on `mango`. Point routine operator and automated callers to the parent `playbooks/` checkout; preserve normal `ansible-playbook ... --vault-password-file ~/.vault_pass.txt` without `-i`. Keep old state available for explicit rollback but never as a silent active fallback.
- Verify normal operation, installed-state equality, zero unintended changes on every host, authorised private repo checkout and replay from pinned parent revision. Collect post-cutover readbacks. Retire obsolete active inventory/checkout only after evidence acceptance; avoid destructive removals, data/snapshot mutations or incidental application upgrades.
- Commit all **sanitised** change-control reports and evidence only under this Diaries feature folder; update status, formally accept gates, move to `change-control/complete/` and publish parent Diaries repo. 0048 permission simplification may start only after this closure.

**Evidence:** `evidence/Step 4/` published three-repo SHA/visibility/pin receipts, Ansible configuration and caller cutover, rollback record, final all-host verification, clean status. **Gate:** formal user acceptance, documentation closed, 0046 published under `complete/`.

**No step is closed by adopting this design document.**
