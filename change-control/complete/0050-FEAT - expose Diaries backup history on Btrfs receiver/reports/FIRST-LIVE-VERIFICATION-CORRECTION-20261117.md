# 0050 — First live deployment and fixed-root verification correction

**Date:** 17 November 2026. **Status:** implementation correction source-tested; *live re-deployment and full verifier read-back pending*. Do not mark Step 3 CLOSED on the basis of this report.

## Observed live results

- `mango` deployed the receiver 0050 Ansible role: `backup ok=37 changed=2 failed=0`; the new status and history scripts and additive `diaries_history` configuration are installed.
- `backup` discovered 30 distinct verified-manifest Diaries identities in 42 retained received snapshot occurrences, with zero manifest conflicts; `btrfs-backup-status --local-only` was HEALTHY and qgroups stale=0.
- Full verification of `production/20261116-003112Z` in received snapshot `20261116-150008Z` returned 2: `backupId must use UTC YYYYMMDD-HHmmssZ format` and `schema-2 verification failed`.
- These observations show a command-invocation defect, **not** evidence of corrupted backup bytes; actual live full verification remains unaccepted.

## Root cause and minimal correction

`roles/snapshots/files/diaries-backup-history.py` passed the validated receiver-local `backup/pluto/diaries-backup` path to the shared, established `complete-dataset-manifest.py verify --backup-dir PATH` without selecting the verifier's **existing** `--allow-fixed-working-root` mode. Without that flag the verifier derives backupId from the final directory name, which is `diaries-backup`, not a UTC timestamp. The history reader can list identities correctly because it extracts `backupId` from `dataset-manifest.json` and checks against the snapshot marker before invoking full verification.

The patch passes `--allow-fixed-working-root` **only when the selected, containment-checked dataset directory has the canonical name `diaries-backup`**. For historical backupId-named generations it retains the ordinary verifier call. The verifier still validates manifest `backupId` format, schema, identity, database/files inventory, file sizes and SHA-256 content; this does not bypass file-integrity verification. Source and receiver share the same code; the revised test explicitly covers both configurations.

No Btrfs datasets, replication transport, snapshot manager, retention, timers, privileges or received markers are changed.

## Local source acceptance

- 0050 permanent deployment/source contracts: **5 passed** (one new fixed-root contract).
- 0050 receiver fixture tests: **9 passed**, including receiver-only selection and fixed-root CLI dispatch.
- Real production schema-2 fixture: **PASS** for backupId-named generation, real fixed-directory `diaries-backup`, source-mode parity, and tampering that must fail.
- 0049 management regressions: **19 passed**.
- 0041 security regressions: **8 passed**.
- Replication regressions: **25 passed**.
- Existing Diaries history and status regressions: **PASS**.
- Compilation: Python affected files **PASS**.

Results are captured in the two raw test logs under `evidence/Step 3/`. The first multi-suite local invocation completed 0050/0049 before reaching its execution limit; remaining suites were executed separately and passed, with no failed suites silently omitted.

## Controlled follow-up

1. Apply only the new Playbooks reader and its permanent test plus the separate Diaries evidence/test ZIPs, using Beyond Compare 4.
2. From `mango`, validate the existing working-tree change set, rerun 0050 changed tests and reapply `ansible-playbook btrfs-replication.yaml --limit backup --vault-password-file ~/.vault_pass.txt`. Expected changed scope: **only** `/usr/local/sbin/diaries-backup-history`.
3. From `backup`, rerun the same live `diaries-backup-history verify 20261116-003112Z --snapshot 20261116-150008Z` with explicit return-code handling. Independently check status and receiver Btrfs health. Do not rewrite snapshot contents or rerun a full restore.
4. Check `mango` receiver Ansible reapply `changed=0`, inspect `mars` command parity and compare naturally retained IDs if available. Preserve logs and actual Git revisions before final publication and separate formal closure approval.
