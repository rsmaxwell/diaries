# 0032 Step 2 — Approved archive layout

## Status

**FROZEN — 2026-10-03.**

This layout is the destination contract for Step 3. Step 3 may create these directories and copy approved historical tooling into them; Step 2 itself does not move live files.

## 0031 archive

```text
change-control/complete/
  0031-FEAT - isolate mutable Files storage by database environment/
    evidence/
      tooling/
        windows/
          step8/
          step9/
          step10/
          step11/
          step12/
          step13/
          step16/
        production/
        validation/
          diaries/
          playbooks/
```

Rules:

- `windows/stepN/` preserves the source files from `scripts/windows/0031-stepN/` without flattening unrelated steps;
- `production/` preserves the seven 0031 production `stepN-*` helpers from the Playbooks sync tree;
- `validation/diaries/` and `validation/playbooks/` are separate so identically named validators from the two repositories cannot collide;
- mixed validators being split during promotion (`verify-0031-step11.py` and Playbooks `verify-0031-step14.py`) get a byte-identical historical copy here before their feature-neutral successors replace them;
- runtime evidence already stored under existing feature step evidence is **not** duplicated here.

## 0026 archive

```text
change-control/complete/
  0026-FEAT - render ImageFragments in diaries-web/
    evidence/
      tooling/
        validation/
```

This receives the historical Step 14 artifact-verifier files:

```text
test-verify-0026-step14.py
verify-0026-step14.ps1
verify-0026-step14.py
```

The Step 13 ImageFragment smoke workflow is not archived wholesale because it remains valuable regression coverage; it is promoted to behaviour-oriented names in the live validation directory.

## 0024 archive

```text
change-control/complete/
  0024-FEAT - introduce reusable persistent Image catalogue/
    evidence/
      tooling/
        production/
          migration0024ImageCatalogue.sh
```

The production wrapper belongs to 0024 rather than 0031 because its durable historical meaning is the completed Image catalogue migration. The 0031 production reconciliation/deployment helpers that happened to call it remain archived under 0031. This avoids duplicating the same wrapper under both feature archives.

## Archive metadata required in Step 3

Step 3 must create an archive manifest recording, for every archived file:

```text
original repository
original path
source identity/commit if available
SHA-256
archived path
final classification
reason
```

The archive copy must be created and fingerprinted **before** the live source is removed or renamed.
