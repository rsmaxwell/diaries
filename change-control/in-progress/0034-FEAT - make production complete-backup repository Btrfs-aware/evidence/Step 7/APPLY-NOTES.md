# 0034-FEAT Step 7 — apply and acceptance notes

## Apply overlays

Apply the Playbooks overlay at the Playbooks repository root and the Diaries overlay at the Diaries repository root.

No Angular/Java application source changed. **Do not build new Docker images for Step 7.**

## Mango source regression

From `~/playbooks`:

```bash
python3 roles/diaries/tests/verify-production-restore-source-compatibility.py
python3 roles/diaries/tests/verify-complete-dataset-manifest.py
python3 roles/diaries/tests/verify-production-backup-restore-semantics.py
python3 roles/diaries/tests/verify-production-complete-dataset-tooling.py
python3 roles/diaries/tests/verify-production-storage-isolation.py
python3 roles/diaries/tests/verify-production-deployment-contract.py
```

All must pass.

## Deploy the permanent restore tooling to pluto

Use the normal Diaries playbook:

```bash
cd ~/playbooks
./scripts/diaries.sh
```

This deploys scripts/configuration only. It must not invoke a backup or restore.

## Pluto non-destructive live acceptance

From the deployed production scripts directory:

```bash
cd ~/projects/diaries/scripts

./restore-dataset.sh preflight 20261007-145013Z
./restore-dataset.sh preflight diaries-backup
printf 'NO\n' | ./restore-dataset.sh prepare diaries-backup
./status.sh
```

Expected:

1. both preflights pass and report schema-2 complete media for backup ID `20261007-145013Z` (or the same newer ID if the fixed publication has deliberately advanced before the test);
2. the `prepare` attempt reaches the explicit confirmation prompt and fails because the exact `RESTORE` token was not supplied;
3. the responder remains in its prior running state and no destructive restore, safety backup or Files staging occurs;
4. legacy timestamp-ID media remain present and independently preflightable.

Capture the command transcript and return it for formal Step 7 close-out.

## Snapshot-history handoff

Do not wait for or fabricate `diaries-backup-history` in 0034. 0035 owns that command. Its future path output is consumed explicitly:

```bash
SNAPSHOT_PATH="$(diaries-backup-history path BACKUP_ID)"
./restore-dataset.sh preflight "$SNAPSHOT_PATH"
```

The history command is read-only and must never invoke `restore-dataset.sh` itself.

## Acceptance result (2026-10-09)

**Step 7 CLOSED.** The six `mango` regression suites and `pluto` deployment passed. Live `preflight` passed for all three source selectors (historical ID, fixed publication, explicit generation path); all reported no writer stop, no safety backup and no Files staging.

The suggested live `printf 'NO\n' | ... prepare diaries-backup` and `./status.sh` commands were not included in the provided runtime logs. Negative confirmation was proven in the disposable regression, and preflight output independently reported `Responder running: True`. Do not treat those two commands as having been run. See `CLOSEOUT.md`.
