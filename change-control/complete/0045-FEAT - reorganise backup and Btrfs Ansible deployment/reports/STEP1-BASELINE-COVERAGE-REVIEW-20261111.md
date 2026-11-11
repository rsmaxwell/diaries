# 0045-FEAT — Step 1 initial baseline coverage review

**Date:** 11 November 2026. **Status:** REVIEWED; Step 1 remains OPEN pending definitive v2 recapture and acceptance. No Playbooks or managed-host deployment has been changed.

## Source and evidence inspected

- User-supplied `0045-step1-baseline-20261111-104837Z.tar.gz`, containing the seven original files under `evidence/Step 1/baseline-20261111-104837Z/`. The `.tar.gz` is a transport copy, not a Git artifact; commit the original seven files, not another copy.
- Supplied Playbooks bundle dated 10 November, cross-checked with the 11 November controller evidence showing clean `main` revision `7dfa93fef6d975aa82f5f4cfdf54497b106e7645`, effective `/etc/ansible` inventory and current entry points. Revalidate the live Git revision before refactoring.
- Windows Diaries `main` revision `47c96ba390ebffc6349e9c1e320aabd72f32be40` recorded by the baseline tool, with in-progress 0045 evidence and collector corrections uncommitted at capture time. This is expected and not a Playbooks source mutation.

## Review result

The baseline capture ran without errors: `mars` had 74 managed paths and `backup` 43. Snapshot status was healthy: `mars` 75 complete sets, `backup` 34; neither host had incomplete sets or stale qgroups. It captures hashes and ownership/modes for installed programs, rendered configuration, unit files and drop-ins, timer enablement, cron fingerprints, ACL fingerprints at selected roots, and the live mount. It does **not** reveal Vault or managed-config contents.

The first capture **is valid historical evidence but insufficient as the definitive installation comparison** because:

1. Additional directories managed by the roles (including receiver state/parent, user and machine backup logs, shared helper directories and source Btrfs roots) lacked independent presence/owner/mode checks.
2. A later Ansible run could alter package versions or effective loaded service commands without an explicit package-version or loaded `ExecStart` fingerprint (the unit files themselves were hashed).
3. Source-side `__pycache__` directories were included in the original manifest, even though bytecode files were excluded. Python/test/editor temporary artifacts are not installation assets and must be ignored in the before/after comparison.
4. The original collector reported one-shot service `ActiveState`, which may change naturally while a backup operation is running. Timer activation remains a meaningful static comparison; transient service activity belongs in separate operational readback.

## Correction and boundaries

The v2 collector covers additional role-created directories, package status/versions and loaded systemd command hashes, and records only ownership/permissions for selected mutable lock and hold files. Both the collector and comparator exclude disposable `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `.tox`, `.nox` directories and `.pyc`/`.pyo` bytecode, common editor swap/backup, `.tmp`/`.temp`, and coverage files **only when discovered inside the two scanned backup script trees**. Differences in these temporary artifacts never block installation equivalence. Managed program, config, systemd and security paths outside those trees remain fully compared; differences not explicitly identified as disposable must be investigated, not ignored. Transient runtime service states and evolving backup datasets remain separate operational verification, not static installed-state differences. It does not hash or traverse backup datasets, Btrfs snapshots, receipts or the **contents** of evolving hold/replication state.

A role task may apply ACLs recursively under the live backup dataset. This collector does **not** enumerate every dataset ACL. In 0045, retain the ACL role gating/logic and verify no unexpected ACL-changing tasks are invoked; use existing security evidence and read-only focused checks where justified. Do not run a recursive ACL migration merely to obtain a new baseline.

Package versions and active mount options can change independently through other administration. Treat differences as **FAIL pending investigation**, not as proof of a Playbooks defect nor a difference to be silently waived. Source/receiver endpoint separation, no historic helper reintroduction, and protected data/holds remain separate mandatory acceptance gates.

## Definitive Step 1 acceptance sequence

1. Apply this small Windows Diaries change-control package (no Playbooks change); verify both Python scripts parse.
2. Re-run `capture-0045-step1-baseline.sh` from Windows Cygwin. It records fresh v2 manifests and the unchanged controller/host baseline under a separate timestamped `evidence/Step 1/baseline-*` directory. Preserve the original v1 baseline and any failed capture as history.
3. Verify JSON schema `0045-static-installed-v2` on both host manifests; confirm expected directory, package and effective unit metadata appears, and expected absent files remain absent. Check full source-to-destination mapping against then-current roles, including optional cases and security boundaries.
4. Only then document Step 1 acceptance and freeze the baseline. The **same v2 collector** must be used both before and after the 0045 refactor; mixing v1 with v2 is intentionally rejected by `compare-0045-installed-state.py`.

No full restore, manual send/receive, package installation, snapshot deletion, Ansible apply or timer restart is justified for this coverage correction.
