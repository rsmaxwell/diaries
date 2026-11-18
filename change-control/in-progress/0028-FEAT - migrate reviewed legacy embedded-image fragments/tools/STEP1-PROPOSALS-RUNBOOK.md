# 0028 Step 1 — Offline proposal generation

Use only the frozen/current schema, 0024 dry-run, triage and unmodified working CSV. This script produces **private, unapproved suggestions**, not a migration manifest. No production access or mutation.

The analysis in `reports/STEP1-CONTENT-REVIEW-20261118.md` was performed using the uploaded 2026-11-18 source snapshot. Its private proposed-review CSV is provided separately; do **not** apply that file to your Git repository.

## Optional regeneration on mango

From the **mango SSH terminal**, after synchronising the feature's new tool/tests to `/home/richard/diaries`:

```bash
cd /home/richard/diaries
FEATURE='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
PRIVATE="$FEATURE/evidence/Step 1/private"
OUT="$PRIVATE/$(date -u +%Y%m%dT%H%M%SZ)-proposals"

if python3 -m unittest discover -s "$FEATURE/tests" -p 'test_step1_propose_content_review.py' -v && \
   python3 "$FEATURE/tools/step1_propose_content_review.py" \
     --frozen "$PRIVATE/20261118T093606Z" \
     --derived "$PRIVATE/20261118T100019Z-0024" \
     --review "$PRIVATE/20261118T101501Z-review" \
     --triage "$PRIVATE/20261118T110212Z-triage" \
     --working "$PRIVATE/20261118T110212Z-working-review/0028-decisions.WORKING.csv" \
     --output "$OUT" && \
   (cd "$OUT" && sha256sum -c SHA256SUMS.txt); then
    echo 'PASS: read-only 0028 proposals created and hashes verified'
else
    echo 'FAIL: proposals not accepted; examine diagnostics'
fi
```

The script rejects edited working review rows, stale evidence and existing output directories. Deliberate reviews and approvals must be recorded in distinct files and reviewed independently; proposals must **never** overwrite a reviewer’s choices.

## Check the dossier exception on mango (no writes)

```bash
cd /home/richard/diaries
FEATURE='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
REVIEW="$FEATURE/evidence/Step 1/private/20261118T101501Z-review"
(cd "$REVIEW" && sha256sum -c SHA256SUMS.txt) && \
    echo 'PASS: canonical mango review evidence matches' || \
    echo 'FAIL: canonical mango dossier checksum differs; investigate before Step 1 closure'
```

If `mango` passes, the mismatch is confined to the exported source ZIP and its export/transfer path should be investigated. If `mango` fails, preserve the evidence exactly as-is and use the existing read-only `step1_make_review.py` to regenerate a **new, separately hashed review directory** from frozen inputs; do not silently overwrite historical evidence or edit hashes.
