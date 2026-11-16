# 0049-FEAT — Closure script Cygwin root-guard correction (16 November 2026)

**Status:** Closure approved; Git relocation/publication still pending.

## Observed failure

The first Windows Cygwin closure execution ended with `0049 CLOSURE: FAIL — Wrong repository root` and wrapper exit code 1. The check was executed before Git staging, the directory move, commit, or push. No closure action is evidenced by that attempted run.

## Root cause and correction

The prior script directly compared `git rev-parse --show-toplevel` with `pwd -P`. Git for Windows and Cygwin can return different absolute-path formats for the same checkout. The replacement retains the fixed Windows Diaries checkout `cd`, requires a Git worktree, requires Git's repository-relative `--show-prefix` to be empty, and requires the repository `.git` metadata at that location.

**Unchanged gates:** main branch, exact published Diaries baseline `34be53fe219dbe773b516596e3d36fa5b29801bb`, Git remote, complete acceptance evidence, no previously staged changes, approved 0049-only tracked edits, 46 published source files, remote tracking baseline, complete file migration, staged change confinement, closure commit, push and remote SHA readback.

## Re-execution

Replace only the feature-specific script and add this report and the raw first-failure transcript using the repository-relative correction ZIP. Then rerun the existing Windows Cygwin `bash "$script"` command within its protective subshell. Inspect the resulting output; no success is asserted until the final `0049 FORMAL CLOSURE: PASS` and published SHA appear.

**Production impact:** None; no `mars`, `backup`, Playbooks, inventory or application code modification.
