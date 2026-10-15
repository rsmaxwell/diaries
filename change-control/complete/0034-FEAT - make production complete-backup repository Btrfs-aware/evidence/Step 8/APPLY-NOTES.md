# 0034-FEAT Step 8 — apply and regression notes

Apply the Playbooks Step 8 overlay to the Playbooks repository on `mango`. Do **not** run the Diaries or local-backup playbooks yet; Step 8 is source/configuration hardening and Step 9 owns production deployment.

From the Playbooks repository root, run each regression separately and capture the complete output:

```bash
python3 roles/diaries/tests/verify-complete-dataset-manifest.py
python3 roles/diaries/tests/verify-complete-dataset-publisher.py
python3 roles/diaries/tests/verify-complete-dataset-replication.py
python3 roles/diaries/tests/verify-production-backup-restore-semantics.py
python3 roles/diaries/tests/verify-production-btrfs-strategy.py
python3 roles/diaries/tests/verify-production-complete-dataset-tooling.py
python3 roles/diaries/tests/verify-production-publication-contract.py
python3 roles/diaries/tests/verify-production-restore-source-compatibility.py
python3 roles/diaries/tests/verify-production-storage-isolation.py
python3 roles/diaries/tests/verify-production-deployment-contract.py
python3 roles/local-backup/tests/verify-diaries-pull.py
```

Expected result: every command exits zero and ends in a PASS summary. `verify-production-btrfs-strategy.py` is intentionally still present and should pass as a **historical legacy-capture compatibility** suite; its continued presence proves the old test was not silently deleted when the reflink publication design was superseded.

Optional source sanity checks:

```bash
python3 -m py_compile \
  roles/diaries/files/sync/scripts/production-complete-dataset.py \
  roles/diaries/tests/verify-production-publication-contract.py \
  roles/local-backup/files/backup-machine/diaries-pull.py \
  roles/local-backup/tests/verify-diaries-pull.py
```

Return the transcript for Step 8 close-out. No Docker image build is required: Step 8 changes Playbooks Python/YAML/Markdown only, not Java or Angular application sources.
