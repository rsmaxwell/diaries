# 0040-FEAT — Step 05 evidence and closure

**Status: CLOSED — 24 October 2026 (accelerated acceptance with explicitly waived coverage).**

## Accepted source revision

Playbooks **`b51a5b0`**: `0040-FEAT: implement snapshot migration and adversarial regressions` (eight files, 262 insertions, six deletions). `git diff --cached --check` succeeded; the post-commit working tree was clean. Evidence: `note(20261024-215639).txt`.

## Executed evidence

`note(20261024-215539).txt` records successful execution on `mango`:

```bash
cd /home/richard/playbooks
sudo python3 roles/snapshots/tests/verify-0040-step05-suite.py
git diff --check
```

The suite reported PASS for mixed paired and `@data`-only history; protection by replication pins and checkpoint holds; incomplete root-only histories; pre-deletion rejection of disappearing candidates; duplicate/unknown/empty source and invalid creation contracts; prohibition of ordinary receiver pruning; dry-run non-mutation. Step 04 migration and receiver-role guard regressions passed. All eight embedded Step 03 coordination scripts passed with root privileges, including the mock two-challenge integration and failure/recovery-state cases. Diff check passed.

## Limitations and residual risk

- The tests were **non-destructive fixtures**; they do not prove live cross-host Btrfs deletion safety.
- The operator explicitly accepted omitting the full cross-host rehearsal on the accelerated path. No PASS is claimed for it.
- Do not infer separately exercised coverage for every original adversarial item (including timing/clock ordering, duplicate timestamps, missing receipts and real deletion failures) beyond the specific logged cases.
- Live `mars` creation remains paired; live `backup` receiver pruning stays disabled. No migration, pruning enablement or legacy retirement is authorised.

**Decision:** Step 05 adversarial source regression acceptance is CLOSED with the stated exceptions. Step 06 runtime retention-plan review and all later rollout/irreversible-retirement gates remain OPEN.

The separate report `reports/STEP05-ACCELERATED-ACCEPTANCE-20261024.md` contains the extended acceptance narrative if applied. The operator logs are referenced by filename, not represented as bundled raw logs.
