# 0034-FEAT Step 9 — apply and production acceptance notes

Apply the accompanying Playbooks overlay on `mango` first. Do not deploy to `pluto` until the source regressions below pass.

## 1. `mango` source regression

```bash
cd ~/playbooks
python3 roles/diaries/tests/verify-complete-dataset-manifest.py
python3 roles/diaries/tests/verify-complete-dataset-publisher.py
python3 roles/diaries/tests/verify-complete-dataset-replication.py
python3 roles/diaries/tests/verify-production-backup-restore-semantics.py
python3 roles/diaries/tests/verify-production-btrfs-strategy.py
python3 roles/diaries/tests/verify-production-complete-dataset-tooling.py
python3 roles/diaries/tests/verify-production-publication-contract.py
python3 roles/diaries/tests/verify-production-publication-wiring.py
python3 roles/diaries/tests/verify-production-restore-source-compatibility.py
python3 roles/diaries/tests/verify-production-storage-isolation.py
python3 roles/diaries/tests/verify-production-deployment-contract.py
python3 roles/local-backup/tests/verify-diaries-pull.py

python3 -m py_compile \
  roles/diaries/files/sync/scripts/production-complete-dataset.py \
  roles/diaries/tests/verify-production-publication-wiring.py \
  verification/0034-step9/verify-pluto-rsync-lock.py
```

Expected: all twelve suites and syntax compilation pass.

## 2. Capture `pluto` predeploy state

Read-only first:

```bash
ansible-playbook verification/0034-step9/capture-predeploy.yaml
```

Then save the private on-host safety capture:

```bash
ansible-playbook verification/0034-step9/capture-predeploy.yaml -e step9_capture=true
```

Copy the reported path into your shell, for example:

```bash
STEP9_SAFETY_DIR=/home/richard/projects/diaries/data/0034-step9-safety/20261009-160000Z
```

Do **not** copy its saved `.env` into Git or the change-control evidence directory.

## 3. Normal Diaries deployment

```bash
./scripts/diaries.sh
```

Capture the complete Ansible output. Deployment must not run a backup/publication automatically.

## 4. Immediate postdeploy preservation check

Before any new backup:

```bash
ansible-playbook verification/0034-step9/verify-postdeploy.yaml \
  -e step9_safety_dir="$STEP9_SAFETY_DIR"
```

Stop if the legacy timestamp-ID inventory changed.

## 5. First final-path publication on `pluto`

```bash
ssh pluto
cd ~/projects/diaries
./scripts/backup-dataset.sh publish-preflight
./scripts/backup-dataset.sh publish
FIRST_ID="$(./scripts/complete-dataset-publisher.py --published-root "$PWD/data/diaries-backup" show-current-id)"
echo "FIRST_ID=$FIRST_ID"
./scripts/complete-dataset-publisher.py --published-root "$PWD/data/diaries-backup" verify-current
./scripts/restore-dataset.sh preflight diaries-backup
test -d "$PWD/data/dataset-backups/production/$FIRST_ID"
```

Return the transcript containing `FIRST_ID`.

## 6. Second complete capture, not yet published

```bash
./scripts/backup-dataset.sh preflight
./scripts/backup-dataset.sh
ls -1dt "$PWD"/data/dataset-backups/production/20??????-??????Z | head
./scripts/complete-dataset-publisher.py --published-root "$PWD/data/diaries-backup" show-current-id
```

Identify the new backup as `SECOND_ID`; confirm it differs from `FIRST_ID` and the stable current ID is still `FIRST_ID`.

## 7. Live rsync/shared-lock proof and second publication

Back on `mango`:

```bash
ansible-playbook verification/0034-step9/run-rsync-lock-proof.yaml \
  -e step9_run=true \
  -e step9_candidate_id="$SECOND_ID"
```

Expected PASS lines state that the publisher remained blocked while rsync held the shared lock, rsync received exactly `FIRST_ID`, publication then advanced to `SECOND_ID`, the previous generation remained retained, and disposable scratch was removed.

## 8. Final non-destructive restore-source acceptance

On `pluto`:

```bash
cd ~/projects/diaries
./scripts/complete-dataset-publisher.py --published-root "$PWD/data/diaries-backup" verify-current
./scripts/complete-dataset-publisher.py --published-root "$PWD/data/diaries-backup" show-current-id
./scripts/restore-dataset.sh preflight diaries-backup
./scripts/restore-dataset.sh preflight "$FIRST_ID"
./scripts/restore-dataset.sh preflight "$SECOND_ID"
```

Return these transcripts together with the Ansible deployment/postdeploy output. They are the evidence needed to formally close Step 9.

No Docker images should be built for this step.
