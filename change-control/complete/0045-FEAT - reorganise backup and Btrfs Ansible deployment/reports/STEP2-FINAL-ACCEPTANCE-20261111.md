# 0045-FEAT — Step 2 final source/caller acceptance (11 November 2026)

**Decision: CLOSED — technical source refactor accepted; original operator entry points retained.**

## Source and publication

- Baseline Playbooks: `7dfa93fef6d975aa82f5f4cfdf54497b106e7645`.
- Refactored Playbooks: `1939a0984934062d03c01de826ad4a5a87d3338d`, `main`, pushed to `origin/main` with clean status (terminal log `note(20261111-130119).txt`).
- One coherent commit: 28 files changed, 992 insertions and 759 deletions; eight snapshot phases and nine native replication phases; role and source/receiver dispatch retained. `backup-collection.yaml` and launcher introduced without removing old launchers.
- Verified source-equivalence: 24 snapshot tasks and 36 native replication tasks had identical attributes/ordering; entrypoint dispatch passed (`note(20261111-115703).txt`).
- Ansible syntax: `backup-collection.yaml`, `btrfs-replication.yaml`, `snapshots.yaml` passed (`note(20261111-120403).txt`).
- Permanent regressions: replication 25 pass; protection 5 pass; shared retention pass; snapshot manager and local backup pass (`note(20261111-120403).txt`, `note(20261111-121247).txt`). Snapshot test was updated to resolve statically imported phases while continuing to reject removal of activation guards.
- Refactored Playbooks check mode completed on both endpoints, without a real apply (`note(20261111-125051).txt`). Docker signing-key task had one predicted change, later shown to be unchanged by the real deployment.

## Caller audit and interface decision

- Read-only filesystem scans: `mango`, `mars`, `backup`, `pluto` each returned 0 matching legacy callers; no oversize files skipped (`note(20261111-122105).txt`; evidence `evidence/Step 2/caller-audit-20261111-122038Z/`).
- Jenkins audit through the live Kind pod on `pluto`: 27 job configurations examined, 0 legacy caller references (`note(20261111-124141).txt`; evidence `evidence/Step 2/pluto-jenkins-pod-20261111-124105Z.txt`). The earlier host-path audit was incomplete and is retained as historical evidence.
- **Decision:** retain `local-backup.yaml`, `remote-backup.yaml` and both original launchers while exposing the new `backup-collection` operator entry point. The scanned paths and accessible Jenkins job definitions do not cover SCM-fetched Jenkinsfiles or unmanaged external schedulers. Keeping original entry points avoids an unsupported absence claim or accidental breakage.
- The installed `/root/scripts/backup/remote/` on `mars` remains managed and must not be conflated with the obsolete operator playbook file.

## Boundary

This is Step 2 acceptance only, not a declaration that 0045 is fully closed. Step 3 confirms actual installed-state equivalence; Step 4 completes Diaries evidence publication and formal feature closure. Do not rerun the accepted tests unless source changes affect them.
