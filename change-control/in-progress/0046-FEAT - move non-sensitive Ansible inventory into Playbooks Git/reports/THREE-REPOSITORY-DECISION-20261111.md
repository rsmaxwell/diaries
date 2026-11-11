# 0046-FEAT — Architecture decision: private parent, public Playbooks, private inventory

**Date:** 11 November 2026
**Status:** ACCEPTED DESIGN; NO IMPLEMENTATION / DEPLOYMENT YET

## Decision

The user explicitly selected a Git-submodule arrangement consisting of (1) a private top-level controller repository, (2) the **existing public** Playbooks repository as one submodule, and (3) a **new private** repository for the complete inventory, including properly Vault-encrypted files and values, as the other submodule. The Vault password stays outside Git.

This **supersedes** 0046 planning from 10 November 2026 that would have placed only non-secret inventory in the public Playbooks repository and retained all Vault ciphertext externally. Retain the old planning reports as history; the active README, implementation steps, architecture/secrets contract and acceptance matrix have been revised together. The legacy 0046 change-control *folder name* is unchanged to preserve links and evidence paths.

The names `rsmaxwell/ansible-controller` and `rsmaxwell/ansible-inventory` and checkout `/home/richard/ansible-controller` are **proposals**, not claims that repositories, permissions or a checkout have already been created. Verify actual remotes and GitHub visibility before proceeding. Do not change the existing public Playbooks Git remote without explicit reason.

## Why this design

- Prevent public redistribution of the site's inventory and Vault ciphertext, while keeping reusable roles public.
- Allow independently audited inventory and code histories and a single private parent Git commit that pins the precise pair of child commits.
- Let native Ansible inventory-relative group/host variable discovery load Vault ciphertext without custom external loaders or symlinks.
- Preserve `/etc/ansible` as the conventional system configuration location and normal operator commands without redundant `-i`.

## Constraints

- No plaintext secret, Vault password, private SSH key or credential-bearing rendered output in **any** Git repo or feature evidence. Private repo visibility is necessary but not sufficient: verify encrypted status.
- Preserve the source `/etc/ansible` inventory and current `/home/richard/playbooks` checkout until exact all-host installation-equivalence evidence and a rollback route are accepted.
- Compare all hosts and applicable playbooks, not just Btrfs endpoints. Preserve the frozen Playbooks implementation SHA and existing installed behaviour; do not introduce destructive Btrfs verification.
- Include private-repository access for required automation, caller path changes, parent submodule update procedures and fresh-clone reproducibility in closure.

## Effect on other features

0045-FEAT and 0047-FEAT are closed. 0046 remains OPEN until implementation and all acceptance gates pass. Planned 0048-FEAT is blocked until formal 0046 closure. No 0046 acceptance step is closed merely by approving this architecture.

## Source basis and gaps

The 0046 documents in the 11 November 2026 Diaries source bundle match the 10 November revised-acceptance package and are the basis of this amendment. The supplied Playbooks bundle was captured earlier on 11 November, before the latest 0047 commits and source-mode corrections. Therefore neither bundle establishes *current* `mango` Playbooks Git SHA, `/etc/ansible` content, Vault classification, existing GitHub repository visibility or present CI caller state; Step 1 must discover these live.
