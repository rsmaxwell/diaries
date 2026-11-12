# 0046-FEAT — Step 2: Three-repository staging

**State: READY TO RUN / NOT EXECUTED on mango.** The previously accepted prepared-inventory semantic comparison remains the basis for staging: 44 matching inventory paths, 12 intended file changes, 14 newly encrypted values and 8 verified active-host Vault representations. This package does not repeat conversion, include inventory contents, or include Vault secrets.

## Agreed Git topology

- Private `rsmaxwell/ansible-controller` parent at `/home/richard/ansible-controller` (on `mango`): two Git submodule links, `inventory/` and `playbooks/`.
- Private `rsmaxwell/ansible-inventory` from already-prepared `/home/richard/ansible-controller/inventory/`.
- Existing public `rsmaxwell/playbooks`, pinned to frozen revision `dca638c00cc3b0fe2f2a46ef01c060cb1a1f6296` in the parent. The operational `/home/richard/playbooks` checkout remains untouched.
- Vault password `~/.vault_pass.txt` stays outside Git. The prepared inventory includes encrypted Vault values, and must only be published to a **private** repository.

## Implementation

Feature tool: `tools/establish-0046-three-repositories.sh`.

The read-only `--preflight` validates: execution as `richard` on `mango`; the prepared 44-file inventory; exact clean Playbooks revision and its actual GitHub remote; the public Playbooks visibility; authenticated `gh` identity; Git SSH read access; commit identity; and absence or empty/private state of the two target repositories. It refuses to overwrite existing local staging Git metadata or a populated private remote.

The `--apply` mode performs the same preflight and then creates the two private repositories when absent, commits/pushes the prepared inventory, initialises the private parent, registers both submodules, pins the Playbooks revision, publishes the parent, and verifies both private visibility settings, gitlink entries, remote commits and clean local working trees.

**Do not rerun `--apply` blindly after a partial failure:** commits/repositories may exist. Preserve logs and reconcile the current state before proceeding.

## Run, evidence and acceptance

Run the feature script directly from the authoritative **Windows Cygwin** Diaries checkout, via `ssh mango 'bash -s -- ...'`. It is supplied via standard input, so no assumptions are made about the `mango` Diaries clone being synchronised. Keep preflight and apply output under `evidence/Step 2/` in the Diaries parent repository. The full copy-and-paste command is also in `tools/README-THREE-REPOSITORY-STAGING.md`.

Preflight-only is safe; apply performs persistent GitHub and local Git changes. Successful staging **does not** activate the new inventory or prove estate-wide installed-result equivalence. `/etc/ansible`, the operational Playbooks checkout, all Ansible scheduled jobs and managed host installations remain unchanged. Later verification and controlled cutover remain OPEN until accepted.

### Package test evidence

- Bash syntax check: PASS (packaged tool and offline integration test).
- Disposable local Git topology integration: PASS; existing local inventory Git repository adopted as submodule, public submodule pinned, private-parent shape produced and remote refs pushed. No live GitHub account or `mango` commands were executed by the package author.
