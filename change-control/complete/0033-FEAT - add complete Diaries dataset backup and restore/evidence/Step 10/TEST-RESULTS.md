# Step 10 permanent regression results

Date: 2026-10-07
Result: **PASS**

The first combined invocation exceeded the execution harness time limit after the local backup/finalisation tests had passed. The remaining suites were then run in smaller groups; each completed with exit status 0. No test reported a failure.

## Diaries local

```text
python scripts/windows/validation/verify-live-script-policy.py
python scripts/windows/validation/verify-complete-dataset-manifest.py
python scripts/windows/validation/verify-local-backup-restore-semantics.py
python scripts/windows/validation/verify-local-complete-dataset-backup-engine.py
python scripts/windows/validation/verify-local-complete-dataset-finalisation.py
python scripts/windows/validation/verify-local-complete-dataset-restore-preparation.py
python scripts/windows/validation/verify-local-complete-dataset-restore-apply.py
python scripts/windows/validation/verify-local-complete-dataset-restore-postflight.py
```

All completed successfully. The live-script guard reported only explicitly supported live areas and no unclassified feature/step-shaped tooling.

## Playbooks production

```text
python roles/diaries/tests/verify-complete-dataset-manifest.py
python roles/diaries/tests/verify-production-backup-restore-semantics.py
python roles/diaries/tests/verify-production-complete-dataset-tooling.py
python roles/diaries/tests/verify-production-deployment-contract.py
python roles/diaries/tests/verify-production-storage-isolation.py
```

All completed successfully. The deployment-contract regression confirmed the approved production script set, managed-directory deletion policy, Python cache exclusion, protected templated scripts and absence of unclassified feature/step-shaped helpers.
