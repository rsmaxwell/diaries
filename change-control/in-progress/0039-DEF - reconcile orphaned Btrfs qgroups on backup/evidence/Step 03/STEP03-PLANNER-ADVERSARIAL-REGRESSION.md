# Step 3 — Offline investigation planner adversarial regression

Status: **IMPLEMENTED; awaiting execution and acceptance on the Windows Cygwin Diaries repository**. Step 3 and 0039-DEF remain **IN PROGRESS**.

## Scope

`test-plan-qgroup-investigation.py` exercises the installed read-only planner against the previously accepted `backup` (29,571 qgroups) and `mars` (191 qgroups) manifests and assessments. It checks the known classification totals, the maximum ten-row review sample, and the explicit absence of deletion authorization, deletion commands and executable actions.

Twelve adversarial cases use disposable temporary *copies* of the backup evidence, including manifest changes, assessment counts, protected snapshot IDs, authorization flags, injected commands, fingerprint and sample mismatches, missing fields, malformed JSON and identity tampering. A rejected case must return exit status 2 with `PLAN UNAVAILABLE:` on stderr and no plan on stdout. The test also compares SHA256 of all six original evidence inputs before and after execution.

This is an **offline** test. It does not access Btrfs filesystems, run SSH, alter quotas or create deletion commands. It does not prove live-state consistency, production deletion safety or the origin of every historical qgroup. Error-message checks establish rejection at the planner boundary, not independent proof of every internal causal path.

## Execution

**Windows Cygwin**, from the Diaries repository root:

```bash
STEP="change-control/in-progress/0039-DEF - reconcile orphaned Btrfs qgroups on backup/evidence/Step 03"
python3 "$STEP/test-plan-qgroup-investigation.py"
git diff --check
```

Save the resulting original terminal log under `evidence/Step 03/planner-regression/` once verified. Do not mark Step 3 CLOSED without the remaining gates and accepted evidence.
