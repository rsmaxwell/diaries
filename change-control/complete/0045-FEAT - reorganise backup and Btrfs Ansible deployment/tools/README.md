# 0045 one-off tooling

0045 Step 1 is eligible to start **after formal closure of 0039-DEF and 0043-FEAT**. 0045 remains **IN PROGRESS / Step 1 OPEN** until its captured baseline, source-to-installed asset map and safety coverage have been reviewed and accepted. 0046 remains **PLANNED** until 0045 closes.

## Step 1 capture — Windows Cygwin

Run from the authoritative Windows Diaries repository root:

```bash
bash 'change-control/in-progress/0045-FEAT - reorganise backup and Btrfs Ansible deployment/tools/capture-0045-step1-baseline.sh'
```

The script writes a timestamped directory under `../evidence/Step 1/`, records the parent repo SHA and submodule pins, and invokes *read-only* SSH commands on `mango`, `mars` and `backup`.

The invoked helpers are:

- `collect-0045-controller.sh` — source SHA, tracked asset names, active entry points, caller filenames, `/etc/ansible` inventory filenames, Ansible group/host topology and a strict allowlist of **non-sensitive** effective variables. No raw `ansible-inventory --list` or unfiltered `--host` output is ever logged.
- `collect-0045-host-state.py` — JSON static managed-file metadata and SHA-256 fingerprints for program/config/unit paths, script trees, root/user crontab hashes, **POSIX ACL xattr hashes read without `getfacl`**, installed timer schedule metadata and mount description. Protected file content and ACL bytes are never printed. No backup data or mutable snapshot/protection state is traversed.
- `compare-0045-installed-state.py` — future Step 3 exact fingerprint comparator; it compares the Step 1 outputs with outputs captured **using the same scripts** after the refactor. It reports changed path names, **not** file contents or secret values.

**Important:** The initial collector covers known managed assets from the latest uploaded source; Step 1 must confirm and extend the source-to-installed path coverage from the *live* Playbooks source on `mango`, including optional/conditional paths, negative (expected-absent) paths and systemd drop-ins. A collector PASS does **not** itself close Step 1 or establish full installation equivalence. All incomplete coverage and errors must be resolved before the Step 1 gate is accepted.

The operational readbacks are separate from the static JSON: natural snapshot count, current agreed-parent timestamps and Btrfs qgroup metrics can change overnight without representing an installation difference. Never run a manual replication, prune or restore solely for this feature.

Do not capture Vault plaintext, private keys, credential-bearing rendered file contents or unsafe raw Ansible variable dumps. The default `/etc/ansible` inventory remains authoritative throughout 0045; the inventory relocation is deferred to 0046.

Only historical feature evidence and one-off tools belong under this directory. Permanent Playbooks regression tests remain with their roles.
