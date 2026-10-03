# 0032 Step 3 close-out — Preserve completed-feature tooling before live cleanup

## Result

**COMPLETE — 2026-10-03.**

All **45** source versions with an approved `archive path` in the frozen Step 2 disposition have verified historical copies at their approved completed-feature evidence paths: 43 final `ARCHIVE` candidates plus the original versions of two mixed `PROMOTE/RENAME` validators. No archive candidate remains dependent on Git history alone.

## Preserved groups

- 0031 Windows Step 8–16 historical migration/evidence tooling;
- 0031 historical Diaries validation helpers;
- 0031 historical Playbooks production and validation helpers;
- 0026 Step 14 artifact-verifier tooling;
- 0024 `migration0024ImageCatalogue.sh`.

The archive contains source/tooling only. Existing bulky runtime evidence was deliberately not duplicated.

## Provenance and integrity

Each archived source file is recorded in `ARCHIVE-MANIFEST.csv` with:

- original repository and path;
- exact supplied source-bundle identity and SHA-256;
- source commit/status availability;
- per-file SHA-256;
- archived path;
- final classification and decision rationale.

All 45 source/archive pairs were compared by SHA-256 and match exactly. `ARCHIVE-SHA256SUMS.txt` provides a stable checksum inventory of the historical copies.

## Historical-documentation rule

New `evidence/tooling/README.md` files under completed 0031, 0026 and 0024 explain that these are later archive locations created by 0032. The original feature evidence was not rewritten to pretend those paths existed during the original implementation.

## Safety statement

Step 3 only created historical archive/evidence copies and updated 0032 progress documentation. It did **not** move, rename, edit or delete any live Windows script, Playbooks sync script or validation test, and it did not touch deployed `pluto`, databases, Files roots, MQTT retained state or running services.

## Handoff to Step 4

The historical preservation prerequisite is now satisfied. Step 4 may remove the archived `scripts/windows/0031-step*` directories from the live Windows script tree according to the frozen Step 2 disposition, while leaving the permanent promotion/rename candidates for their dedicated cleanup step.
