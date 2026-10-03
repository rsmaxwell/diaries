# 0032 Step 1 evidence - live tooling inventory and reference freeze

## Status

**COMPLETE — 2026-10-03.**

No live script, validation file, Playbooks helper, task, test or deployed production file was moved, renamed or deleted by Step 1.

## Source snapshots

- `diaries-sources-20261003-120114.zip` — SHA-256 `75e91b5c3f22a60a32c5e64e81ded06bf519d6252b6591b916dd2ae9632c7d82`
- `playbook-sources-20261003-115130.zip` — SHA-256 `0cacf4845e3b55aa3189d39eee0556929304d0a3863cc76684ef5bbf3c3638e6`

These are the authoritative inputs for the source-side inventory/reference scan.

The deployed production inventory was captured independently on `pluto` at `2026-10-03T12:39:30+01:00` and is preserved verbatim in `PLUTO-SCRIPTS-BEFORE.txt`.

## Evidence created

- `WINDOWS-SCRIPTS-BEFORE.txt` — exact recursive Windows script tree with file sizes and SHA-256.
- `WINDOWS-VALIDATION-BEFORE.txt` — exact validation subtree with file sizes and SHA-256.
- `PLAYBOOKS-SCRIPTS-BEFORE.txt` — exact role sync-script source inventory.
- `PLAYBOOKS-TESTS-BEFORE.txt` — exact Diaries role test inventory.
- `PLAYBOOKS-TASKS-BEFORE.txt` — exact Diaries role task inventory, included because Step 1 explicitly requires task/reference review.
- `PLUTO-SCRIPTS-BEFORE.txt` — exact read-only deployed production scripts inventory captured on `pluto`.
- `PLUTO-RECONCILIATION.md` — source/deployment reconciliation and stale-file check.
- `REFERENCE-MAP.md` — cross-repository reference scan distinguishing active callers, live documentation, historical records, 0032 records and package metadata.
- `INITIAL-DISPOSITION.csv` — one row per feature/step-specific cleanup candidate with purpose, callers, initial classification, proposed location and risk notes.
- `PLUTO-CAPTURE-COMMAND.txt` — the read-only command used to capture the production inventory.
- `STEP-1-CLOSE-OUT.md` — closure decision and Step 2 handoff.

## Source-side findings

The scan found **60 feature/step-specific candidate files** across the requested live Windows and Playbooks areas. The initial disposition is **40 `ARCHIVE`**, **19 `PROMOTE/RENAME`**, and **1 `PENDING`**. The sole pending decision is `migration0024ImageCatalogue.sh`, exactly as required by the feature plan.

The main dependency findings are:

1. the current generic ImageFragment smoke runner imports three `step13-*` helper modules, so those helpers need promotion/renaming or an atomic caller update rather than blind archival;
2. the 0026 Step 13 wrapper still runs the helper regression tests;
3. the production Step 14 helper calls Step 12 reconciliation, which calls the 0024 migration wrapper and Step 12 comparator;
4. current 0031 final-regression tooling aggregates earlier 0031 validators, explaining several otherwise surprising source references;
5. the Playbooks synchronize task has no unrestricted deletion, so the runtime inventory had to be captured rather than inferred from source.

All source-side active callers found by the scan are explained in `REFERENCE-MAP.md`; none is being silently ignored.

## `pluto` reconciliation

The production capture contains **23 files**.

- all **14** files from the Playbooks sync-script inventory are present;
- **13/14** have identical size and SHA-256;
- the only differing synchronized file is `README.md` (documented source/deployment drift);
- the remaining **9** files are exactly the expected template-generated operational scripts (`start`, `stop`, `status`, `logs`, and five shell-prompt helpers);
- there are **no unexplained deployed-only filenames**;
- all seven 0031 production `stepN-*` helpers are deployed and byte-identical to source;
- `migration0024ImageCatalogue.sh` is deployed and byte-identical to source.

See `PLUTO-RECONCILIATION.md` for the full comparison.

## Closure

The Step 1 completion criterion is satisfied: every cleanup candidate has known references and an initial classification, the exact production deployment has been reconciled, and there are no unexplained active callers or deployed files.

**Step 1 is closed.**
