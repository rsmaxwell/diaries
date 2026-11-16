# 0049 — Playbooks commit evidence review (16 November 2026)

**Feature:** 0049-FEAT — rationalise Btrfs and Diaries backup management
**Review status:** Playbooks source commit recorded; Ansible-controller gitlink, Windows Diaries revision, and publication still outstanding.

## Results

1. Windows Cygwin invoked the 0049 helper on mango for `--inspect`, then `--stage`; both passed. It verified the baseline commit `0904bc7ebe801e391a3aa4dc59bbc9ccc7dfa532` and SHA-256 hashes for all 32 approved Playbooks files, then staged precisely those 32 files.
2. The subsequent repeated `--inspect`/`--stage` invocation refused with exit 2 because those files were already staged. This is intentional, safe staged-change protection and did **not** invalidate the successful staging.
3. On mango, `git diff --cached --check` passed, the 32-file diff showed 1,774 insertions and 474 deletions, and the Playbooks commit succeeded:

   `a2508ad61f479c1b2bc20cb39896006c1f2906e1`

4. Playbooks `main` has remote `git@github.com:rsmaxwell/playbooks.git` and the commit reported `[origin/main: ahead 2]`. Both unpublished commits must be inspected before pushing; no push is evidenced.
5. Untracked `roles/btrfs-replication/files/__pycache__/` and `roles/snapshots/files/__pycache__/` were excluded from the commit. Do not blanket-clean, stage or delete them as part of 0049.

## Remaining repository acceptance

- Inspect two local Playbooks commits pending publication and push only after their scope and remote are accepted.
- Commit the `playbooks` submodule pointer in private `/home/richard/ansible-controller`; preserve private `inventory` submodule.
- Commit the evidence and revision manifest in authoritative Windows Diaries parent checkout, preserving unrelated changes and application submodules.
- Record and verify actual Playbooks/controller/Diaries revisions and remote publication. Request formal closure acceptance before moving 0049 from `in-progress` to `complete`.

**No further production replication, prune or restore testing is needed for 0049.**
