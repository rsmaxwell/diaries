# 0029-FEAT Step 3 — source commit handoff (26 November 2026)

## Accepted basis

Source manifest executed 14:02 GMT on Windows: `evidence/step-3-release-source-manifest/source-20261126-140206-13228.log`. This script pins 12 Client, 42 Responder, and 10 Reader source/test files to the SHA-256 digests from that log. The independent source bundle timestamped 13:11 is reference material; the 14:02 hashes are authoritative for staging.

## Execute (Windows Cygwin Bash)

From the Diaries parent repository root:

```bash
bash 'change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling/tools/run-step3-guarded-submodule-release-commits.sh' --plan
```

If PASS and source unchanged, execute with `--commit` to create three **local** commits; the helper never pushes or modifies the parent Git index. If the helper rejects extra or changed files, inspect rather than bypassing the checks. The helper also refuses pre-existing staged files. Commit log and new SHAs should be retained in the feature evidence.

## Parent repo staging (after reviewing submodule commits)

The parent must pin the three new submodule revisions, its `config/mosquitto/aclfile.txt` change and the reviewed 0029 change-control documentation/scripts, **not** ZIP extraction README files, other features, or large backup dumps. Inspect `git status --short`, `git diff --submodule=log` and `git diff --cached --name-status`; use exact path-based staging, never `git add -A` from the parent. Leave 0029 in `in-progress` until production verification and formal acceptance. The Playbooks ACL source change is independently uncommitted on `mango` and must be committed there as a separate repository change.

## Outstanding

Full Files restoration remains incomplete due to the stalled transfer, notwithstanding successful all-128 payload checksum verification and isolated database restore. Production release images, immutable digests, deployment and rollback acceptance remain pending. Nothing in this package authorises production execution.
