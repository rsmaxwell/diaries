# 0028 Step 1 — Produce a private, unapproved review workbook

**Read-only / offline.** This runbook consumes already-frozen evidence; it does not contact the DB, Files root or MQTT. All generated HTML/CSV contains **private diary data** and must stay under the feature's ignored `evidence/Step 1/private/` directory.

## 1. Apply this package and synchronise source

**Windows Cygwin terminal:** apply the `0028-FEAT-step1-review-worksheet-20261118.zip` through Beyond Compare 4 to the Diaries parent working tree, then commit/synchronise the parent Git repository to `mango` through the normal source-control workflow. Do not overwrite unrelated 0042–0044 untracked changes on mango; no submodule update is required for this utility.

```bash
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
git branch --show-current
git rev-parse HEAD
git status --short
git diff --check
```

**mango SSH terminal:** after synchronising, verify the new tool and the frozen evidence.

```bash
cd /home/richard/diaries
FEATURE='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
FROZEN="$FEATURE/evidence/Step 1/private/20261118T093606Z"
DERIVED="$FEATURE/evidence/Step 1/private/20261118T100019Z-0024"

test -f "$FEATURE/tools/step1_make_review.py" && echo 'PASS: reviewer available' || echo 'FAIL: reviewer missing'
python3 -m unittest discover -s "$FEATURE/tests" -p 'test_step1_*.py' -v
```

## 2. Build the private review aids

**Same mango SSH terminal:** use the *existing* evidence directories (no new inventory run required) and a new output directory.

```bash
cd /home/richard/diaries
FEATURE='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
FROZEN="$FEATURE/evidence/Step 1/private/20261118T093606Z"
DERIVED="$FEATURE/evidence/Step 1/private/20261118T100019Z-0024"
REVIEW="$FEATURE/evidence/Step 1/private/$(date -u +%Y%m%dT%H%M%SZ)-review"

if python3 "$FEATURE/tools/step1_make_review.py" \
    --frozen "$FROZEN" \
    --derived "$DERIVED" \
    --output "$REVIEW"; then
    (cd "$REVIEW" && sha256sum -c SHA256SUMS.txt) && \
        echo 'PASS: private review workbook complete' || \
        echo 'FAIL: review checksum verification failed'
else
    echo 'FAIL: no reviewed migration has been authorised'
fi
```

The tool refuses an existing output directory, validates all input files against their hash manifests, and checks that 0024 finished in `dry-run` with successful post-verification. It crosschecks all occurrence identities and hashes before writing. A failure leaves the input evidence unchanged; diagnose rather than deleting or rewriting frozen evidence.

## 3. Inspect the results

**mango via existing WinSCP session:** open or copy the three files under the printed PRIVATE `...-review` directory to a secure local review location on Windows. Never upload them to a public Git repository or ordinary issue tracker.

- `0028-review-worksheet.PRIVATE.csv` — a *non-executable review aid*, one row per `<img>` occurrence, carrying fragment/page/status/image checks and **blank** review disposition/action fields. The presence of fields in this worksheet does not satisfy the formal manifest contract.
- `0028-review-dossier.PRIVATE.html` — static **offline** HTML with escaped original markup and original sources, both shown inertly; no image/script/network resources load. Inspect the source and image association for every row. The dossier is evidence, not an editing UI.
- `0028-review-summary.json`, `SHA256SUMS.txt` — aggregate counts, source hash linkage, review-aid hashes.

Reviewers must explicitly assess suffix matches, missing Page associations, the unresolved ambiguous image, transcription-versus-image-text allocation and the four permitted dispositions. All outputs have **UNREVIEWED** status. This tool performs no conversion, creates no approved manifests and is not a Step 1 closure.

### Do not edit frozen evidence

Keep the original 0028 `.UNREVIEWED.csv` files and 0024 cross-reference unchanged. Any evolving review worksheet should be separately versioned and hashed, and final authorised manifests produced through the Step 2 strict validator with explicit human sign-off. Preserve rollback evidence and private material in the feature directory.
