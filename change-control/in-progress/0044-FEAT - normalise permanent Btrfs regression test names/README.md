# 0044-FEAT — Normalise permanent Btrfs replication regression test names

**State:** IN PROGRESS — permanent regression cleanup and final evidence reconciliation. **Rename commit:** Playbooks `06cf0886a863ce2d4d5e19289fc1fbf124d97554` (10 November 2026). The Windows Diaries repository is authoritative for this change-control directory.

## Purpose

The five permanent regression scripts retained by 0042-FEAT no longer represent temporary 0040-FEAT work. Remove their historical numbering while keeping the scripts under `roles/btrfs-replication/tests/`. Keep historical README filenames and explanatory references to 0040 for traceability; update executable filenames in two README files.

No snapshot creation, pruning, replication, inventory editing, service deployment or filesystem cleanup is involved.

## One-off tool

`tools/rename-btrfs-regressions.py` checks the Playbooks `main` revision and clean Git state, confirms all five original filenames, parses Python source, identifies *all* tracked references to the old filenames, and refuses unknown references. `--check` makes no changes. `--apply` runs `git mv` for five files and updates the documented commands in:

- `roles/btrfs-replication/tests/README-0040-SIMPLIFIED.md`
- `roles/snapshots/tests/README-0040-SIMPLIFIED-RECEIVER-RETENTION.md`

The tool then checks that old script filenames are absent from tracked Playbooks contents, parses renamed scripts, runs Git whitespace checks, and leaves all seven changed files staged for review. It **does not commit or push**. No broad search-and-replace of historical feature text.

## Execution

Apply this feature ZIP to the Windows Diaries checkout using Beyond Compare 4. Transfer the feature folder to `/home/richard/diaries` on `mango` before using the tool there. Run as user `richard` from `/home/richard/playbooks`:

```bash
script='/home/richard/diaries/change-control/in-progress/0044-FEAT - normalise permanent Btrfs regression test names/tools/rename-btrfs-regressions.py'
python3 "$script" --check
python3 "$script" --apply
```

After applying, run the five current source regressions, review the staged Git diff, and make an isolated Playbooks commit. Keep command output/commit receipt under this feature's `evidence/` directory in the Windows Diaries checkout. Mark CLOSED only once test results and source-control evidence are accepted.

## 10 November rename and regression acceptance

The transfer to `mango` succeeded. The guarded rename script passed preflight and changed exactly five regression script filenames with no executable-content changes. It updated two retained README files and staged seven paths. The source-control baseline was Playbooks `6d7f397048b8ed47c94f973a98096fc6e806e4e8`.

All five renamed regression entry points were executed on `mango`: simplified replication (25 tests), agreed-parent protection (4), cutover readiness (5), shared retention (PASS), and legacy-retirement source guard (PASS). Git staged whitespace validation passed. The raw transfer and regression transcripts are preserved under `evidence/Step 1/` and `evidence/Step 2/`; the assessment is in `reports/RENAME-ACCEPTANCE-20261110.md`.

**Accepted source-control receipt:** the five renames and two README edits were committed as Playbooks `06cf0886a863ce2d4d5e19289fc1fbf124d97554`. The verified receipt is in `evidence/Step 3/`.

## Step 4 — consolidate overlapping permanent tests (pending)

Retire `verify-legacy-retirement-source.py` from permanent Playbooks regression tests after incorporating its still-relevant safeguards into `verify-simplified-cutover-readiness.py`. The historical test is preserved verbatim as `tests/historical-verify-legacy-retirement-source.py` (SHA-256 `f47979cdef418a014dfbd540fa4cb31c8cf9441215bfcfa61d451c949afae1f9`), along with the accepted PASS transcript in Step 2 evidence and the immutable 0044 rename Git commit.

The permanent cutover test retains runtime executable, root group, simplified command installation, default-disabled activation, qgroup maintenance and receiver scheduling checks. The historical absence-of-retired-files assertions do **not** become a permanent maintenance obligation.

Apply the 0044 consolidation Playbooks ZIP using Beyond Compare 4. It updates just two files. Transfer the updated 0044 feature directory from Windows to `/home/richard/diaries` on `mango` and run `tools/retire-legacy-regression.py --check`, then `--apply`, from `/home/richard/playbooks`. The tool requires a clean base at commit `06cf088...`, verifies the exact updated file hashes, removes only the legacy test via `git rm`, stages the other two edits and runs the four remaining regression entry points. Do not commit or close the feature until the `mango` regression output and the new Git receipt are captured.

No Ansible deployment or production filesystem changes are required.

## Step 5 — retire completed cutover-readiness acceptance

After Step 4 consolidated the legacy-file retirement checks (Playbooks commit
`b393602f3086a570e429dbec57d1a9ff1db7304b`, successful regression log
under `evidence/Step 4/`), the operator approved retiring the remaining
migration-specific cutover-readiness test. The original test is preserved under
`tests/`, and the small enduring safety assertion (all three pruning planners
must consult the agreed-parent pin set) moves to the existing permanent
`verify-simplified-protection.py` test. There are then three permanent tests in
`roles/btrfs-replication/tests/`: replication, protection and shared retention.

Apply the Step 5 Playbooks ZIP using Beyond Compare. Transfer the updated 0044
feature directory to `/home/richard/diaries` on `mango`, then execute
`tools/retire-cutover-regression.py --check` and `--apply` from
`/home/richard/playbooks`. The script is fail-closed and stages but does not
commit or publish. Capture passing tests and the eventual commit receipt under
`evidence/Step 5/`. See `reports/STEP5-CUTOVER-REGRESSION-RETIREMENT-20261110.md`.
