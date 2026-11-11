# 0045-FEAT — Step 1 capture protocol

**State:** OPEN — evidence not yet captured, reviewed or accepted.  
**Prepared:** 11 November 2026 (planning/tooling only).  
**Prerequisites:** 0039-DEF and 0043-FEAT formally CLOSED and published on 11 November (Diaries commit `27e6cbd`); 0044-FEAT and its permanent regression names already published (Playbooks commit `7dfa93fef6d975aa82f5f4cfdf54497b106e7645`). The script verifies the *actual* Git revisions at execution time rather than assuming source bundles are current.

## Collection and comparison strategy

1. Commit the existing 0045 and revised 0046 planning documents in the authoritative **Windows Diaries** Git repository, limiting staged paths to those two feature directories. No Playbooks change is required at this point.
2. Run `tools/capture-0045-step1-baseline.sh` from **Windows Cygwin**. Save the generated evidence within `0045/evidence/Step 1/baseline-<UTC timestamp>/`; do not use `/home/richard` as the permanent evidence store. The SSH commands access only controller/source metadata and managed-host read-only state.
3. Review both hosts' static managed installation fingerprints (`*-installed-static.json`), installed status/timer readbacks, and non-secret Ansible source/topology report. The tool captures **SHA-256** of installed managed config rather than plaintext, and only an explicit allowlist of non-secret effective variables.
4. Complete the full source-to-installed mapping using the *current* Playbooks role tasks, including all conditional and optional installed assets, source/receiver security boundaries, source snapshot creation and prune activation, receiver prune, qgroup cleaner, cron, local backup acquisition and rollback/absent legacy paths. Extend the collector where the current source requires it **before** accepting Step 1.
5. Mark Step 1 CLOSED only after explicitly reviewing coverage and reproducibility, installed ownership/modes/units/cron/ACLs, expected absent files and zero unintended commands. Retain a baseline Git SHA and rollback reference.
6. After the coherent 0045 refactor, run the **same** collector and `compare-0045-installed-state.py BEFORE_DIR AFTER_DIR`. All static fingerprints must match; separately verify runtime safety/state and source-to-destination coverage, then run consolidated regressions and controlled apply per the already agreed implementation plan.

## Caveats

- Do not compare dynamically changing Btrfs state as though it were an installed static file. Preserve snapshot/checkpoint/agreed-parent state; confirm its health and safety separately.
- The first collector pass is a starting manifest, not a claim of exhaustive coverage. Any missing managed destination must be added and recaptured as a consistent baseline on both endpoints **before** deployment.
- `ansible-inventory --graph` reveals only group/host names. The controller helper uses a strict allowlist for effective variables, keeping decrypted Vault data in process memory only and never writing unrestricted inventory output.
- No Ansible apply, synchronization, package installation, timer change, backup restore, manual snapshot deletion or replication is performed by these tools.
- On test failure, preserve partial evidence and the diagnostic; never mark a command PASS if it did not complete.
