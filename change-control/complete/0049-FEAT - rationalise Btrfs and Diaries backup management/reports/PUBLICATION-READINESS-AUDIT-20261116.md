# 0049 — Git publication readiness audit (16 November 2026)

**Status:** PASS for repository consistency and fast-forward publication planning; repositories have not yet been pushed by the audited commands. The feature remains IN PROGRESS.

## Confirmed commits and dependency order

| Repository | Local HEAD | Unpublished local commits (oldest to newest) |
| --- | --- | --- |
| Public Playbooks (`rsmaxwell/playbooks`) | `a2508ad61f479c1b2bc20cb39896006c1f2906e1` | `0904bc7` (0041), `a2508ad` (0049) |
| Private Ansible-controller (`rsmaxwell/ansible-controller`) | `a81eafdf1fccf6bcd7d9d1b3dfa77143872682e8` | `e325227` (0041), `a81eafd` (0049) |
| Diaries parent (`rsmaxwell/diaries-application`) | `f48f09dc373a5dc12bdba0493e1e2ed7cb6f0e01` | `b3bb0b5` (0041), `f48f09d` (0049) |

All three audits were run after `git fetch origin` (for the controller and Playbooks together, and Diaries separately). No publication was performed.

The controller's committed `playbooks` gitlink points **exactly** to `a2508ad61f479c1b2bc20cb39896006c1f2906e1`. Its private `inventory` gitlink remains `ebcce026723db37b9b53b76ba21903a351d48466`. The Windows Diaries submodules remain at `diaries-client` `e45ae170017fdf4974f642f654d7f709269af711`, `diaries-responder` `bd65d08435c0f5d240337cd6479cb41befe4d8c1`, and `diaries-web` `cc147426e93ee6952558b65147e444d38316b3ce`.

The two untracked `__pycache__` directories in Playbooks are generated local files and were deliberately excluded from commits. Windows Diaries has four additional *untracked* 0049 evidence/report files from the previous package; these must be committed alongside this audit before publication. They are not a blocking inconsistency.

## Publication prerequisites

1. Verify the exact remote for each repository (particularly private `ansible-controller`), check that remote `main` is an ancestor of the local HEAD, and reject unexpected branch or remote drift.
2. Push public Playbooks first, including its already-reviewed 0041 and 0049 commits.
3. Push private Ansible-controller second, after verifying its gitlink points to the published Playbooks revision and its inventory pointer is unchanged.
4. Commit the pending 0049 evidence in the authoritative Windows Diaries parent repository; push Diaries afterward, including its unpublished 0041 and 0049 commits. No application submodules should be staged.
5. Capture the actual server-confirmed Git remote ref SHAs and source `git status` as publication receipts under this feature. A successful command without readback is not a publication receipt.

## Acceptance boundary

Earlier accepted technical evidence includes a successful incremental Btrfs transfer with dedicated restricted transport, matching sender/receiver agreed parents, validated receiver read-only snapshot identity, no planned retention deletions, and a final Ansible reapply with `changed=0` on `mars` and `backup`. Do not repeat destructive snapshot, prune, or restore work for this Git-only step. Do not move feature to `complete` without formal closure approval and recorded publication receipts.
