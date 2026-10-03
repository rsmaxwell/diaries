# 0032 Step 1 close-out — Freeze the live tooling inventory and find every reference

## Status

**COMPLETE — 2026-10-03**

## Scope completed

Step 1 froze the current tooling inventory without changing live tooling and established the reference/disposition baseline needed by later cleanup steps.

The evidence now covers:

```text
scripts/windows/
scripts/windows/validation/
roles/diaries/files/sync/scripts/
roles/diaries/tests/
roles/diaries/tasks/
pluto:/home/richard/projects/diaries/scripts/
```

## Results

- **60** feature/step-specific cleanup candidates were catalogued.
- Initial classification remains **40 `ARCHIVE`**, **19 `PROMOTE/RENAME`**, and **1 `PENDING`**.
- The sole `PENDING` item remains `migration0024ImageCatalogue.sh`, by design.
- Cross-repository callers and documentation references are recorded in `REFERENCE-MAP.md`.
- Active dependency clusters that prevent blind archival are explicitly identified.
- The production runtime inventory contains **23** files and has no unexplained deployed-only filename.
- All **7** 0031 production step helpers are deployed and byte-identical to the frozen Playbooks source.
- `migration0024ImageCatalogue.sh` is also deployed and byte-identical to source.
- The **9** deployed files absent from the sync-script directory are all explained by Ansible template deployment.
- `scripts/README.md` differs between Playbooks source and `pluto`; this is recorded as non-executable documentation drift and does not block Step 1 closure.

## Safety statement

Step 1 did **not** move, rename, delete or modify any live script, validation test, Playbooks task, deployed production script, application data, database content, Files data or retained MQTT state.

## Evidence

- `WINDOWS-SCRIPTS-BEFORE.txt`
- `WINDOWS-VALIDATION-BEFORE.txt`
- `PLAYBOOKS-SCRIPTS-BEFORE.txt`
- `PLAYBOOKS-TESTS-BEFORE.txt`
- `PLAYBOOKS-TASKS-BEFORE.txt`
- `PLUTO-SCRIPTS-BEFORE.txt`
- `PLUTO-RECONCILIATION.md`
- `REFERENCE-MAP.md`
- `INITIAL-DISPOSITION.csv`
- `PLUTO-CAPTURE-COMMAND.txt`

## Handoff to Step 2

Step 2 can now freeze the final disposition for every candidate. It should pay particular attention to:

1. the ImageFragment smoke helper dependency cluster;
2. the 0031 final-regression/validation aggregation chain;
3. the production Step 14 → Step 12 → 0024 migration helper chain;
4. the explicit final disposition of `migration0024ImageCatalogue.sh`;
5. behaviour-oriented permanent names for the 19 `PROMOTE/RENAME` candidates.

No cleanup action should occur until Step 2 replaces all provisional classifications with the approved final disposition.
