# 0047-FEAT — Step 3 final acceptance and formal closure (11 November 2026)

**Formal decision:** Technical implementation and deployment evidence are
ACCEPTED. **Feature status becomes CLOSED only after the final Diaries
feature-directory move, commit, push and branch verification succeed.**

## Accepted source and installation

- Original Playbooks rollback anchor: `9a21c69` (pre-0047). Rollback was not
  required or executed. Preserve backup datasets, snapshots and agreed-parent
  state in any future source rollback assessment.
- Role/entrypoint retirement commit `b04de9e`, source executable-mode
  preservation `833da94`, and source-mode-preserving rsync correction
  `dca638c00cc3b0fe2f2a46ef01c060cb1a1f6296` are published on Playbooks
  `main`.
- All intended source regressions, Ansible syntax tests, 14 source-mode
  checks and native rsync second-run idempotence checks passed.
- First corrective install changed only the two expected `mars` file-copy
  tasks; second normal installation returned `changed=0`, `failed=0`,
  `unreachable=0` on all three targeted play/host combinations.
- Managed static installed-state on `mars` and `backup` matched the accepted
  0045 v2 baseline. Runtime-only systemd history differences were reconciled.
  Docker signing key unchanged. Read-only Btrfs health returned success.

## Retained operational and security contracts

The remaining supported interfaces are `backup-collection.yaml`,
`snapshots.yaml` and `btrfs-replication.yaml`. The `local_backup` and
`remote_backup` inventory group names remain intentionally unchanged;
`0046-FEAT` owns inventory relocation. Installed scheduled jobs, backup
scripts, sender/receiver protections and existing backup data remain in place.
The former generic receiver snapshot entry point is replaced by
`snapshots.yaml --limit backup --tags snapshots`, **not** by the native
replication entry point.

The prior four-host/27-Jenkins-job caller audit had no inspected matches;
SCM-loaded Jenkinsfiles and external schedulers are residual unknowns.
That limitation was accepted when legacy operator retirement was requested.

## Follow-up feature

`0048-FEAT` is separately planned and BLOCKED until both `0046-FEAT` and
`0047-FEAT` are formally closed. It evaluates whether modes `0664`/`0750`
are truly required versus fresh-clone modes; it may retire active mode
restoration and `source-modes.json` checks if behavior, security and
idempotence allow. Historical 0047 evidence must remain preserved.

## Final publication and custody

Authoritative feature evidence is under this Diaries parent feature root,
including `evidence/Step 1/`, `evidence/Step 2/`, scripts and source reports.
Move the entire directory from `change-control/in-progress/` to
`change-control/complete/`, then publish exactly the 0047 changes to Diaries
`main`. Verify `origin/main` equals HEAD, feature source path is absent,
final destination exists and the feature path is clean. Historical source
execution failures and corrections remain part of the audit record.

**If the final move, commit or push fails, this feature remains formally
IN PROGRESS even though technical acceptance has passed.** The resulting
closure commit SHA belongs in the terminal evidence and Git history, not in
this not-yet-published report.
