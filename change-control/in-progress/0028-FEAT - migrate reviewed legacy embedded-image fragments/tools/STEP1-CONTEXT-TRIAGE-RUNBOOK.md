# 0028 Step 1 — Read-only Page context and historical review triage

**Purpose:** use the **already verified** 0028 production inventory, 0024 dry-run and 72-row private review worksheet to prepare a human triage order. No live database query, no mutation, no status approval.

The historical `0022-static-baseline-20260911/review-ledger.json` is an *earlier source import review*, not an approved 0028 migration manifest. It has 42 decisions in the source bundle; only uniquely corroborated identities/date/HTML hashes are shown as hints. A historical `IMAGE` choice must **never** be copied blindly to a 0028 disposition.

## 1. Apply the repository-relative ZIP

**Windows 11:** compare/apply the ZIP against the Windows Diaries **parent** repository with Beyond Compare. This package adds only the files under the existing 0028 feature directory. It does not change either application submodule, Playbooks, existing private evidence, or the old review worksheet.

**Windows Cygwin terminal:**

```bash
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
git branch --show-current
git rev-parse HEAD
git status --short
git submodule status
git diff --check
```

Commit/push the new 0028 files from Windows after review, and synchronize the **parent checkout** to `mango` using your existing Git procedure. Check the `mango` branch/status and preserve the unrelated untracked feature directories. No submodule checkout is necessary for the offline tool.

## 2. Run all existing Step 1 tests and the triage

**mango SSH terminal:**

```bash
cd /home/richard/diaries
FEATURE='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
FROZEN="$FEATURE/evidence/Step 1/private/20261118T093606Z"
DERIVED="$FEATURE/evidence/Step 1/private/20261118T100019Z-0024"
REVIEW="$FEATURE/evidence/Step 1/private/20261118T101501Z-review"
LEDGER='change-control/complete/0022-FEAT - migrate fragments to explicit page ownership and type/0022-static-baseline-20260911/review-ledger.json'
TRIAGE="$FEATURE/evidence/Step 1/private/$(date -u +%Y%m%dT%H%M%SZ)-triage"

git branch --show-current
git rev-parse HEAD
git status --short

if python3 -m unittest discover -s "$FEATURE/tests" -p 'test_step1_*.py' -v && \
   python3 "$FEATURE/tools/step1_triage_context.py" \
       --frozen "$FROZEN" \
       --derived "$DERIVED" \
       --review "$REVIEW" \
       --ledger "$LEDGER" \
       --output "$TRIAGE" && \
   (cd "$TRIAGE" && sha256sum -c SHA256SUMS.txt); then
    echo 'PASS: Step 1 offline triage and evidence integrity'
else
    echo 'FAIL: Step 1 triage did not complete cleanly; inspect output'
fi
```

**No `set -e` is applied to the interactive terminal.** Inputs remain frozen and protected by their existing hash manifests; the collector also checks the review summary's binding to those inputs. Output directory must be new and inside the existing ignored/private Step 1 evidence directory. If an input changed, the tool stops before creating output.

## 3. Inspect the private results

Use your existing WinSCP connection to `mango` to open the new `...-triage` directory securely. It contains:

- `0028-context-triage.PRIVATE.csv`: the **existing 72 unapproved worksheet rows**, sorted by risk, with extra columns. **All review fields are blank**. Same-date Page IDs, nearest neighbours and historical 0022 hints are advisory only.
- `0028-context-summary.json`: aggregate triage and history-link counts, with input evidence hashes.
- `SHA256SUMS.txt`: local output integrity check.

Keep the older `20261118T101501Z-review/0028-review-dossier.PRIVATE.html` alongside it: use that dossier to inspect original HTML and source references *as inert text*. A `P0` row should be addressed first because its image cannot currently be uniquely mapped. For unowned rows, use contextual evidence only to help a person investigate; check the real Page/diary identity before any approval. `P4` means Page/Marquee agree, **not** that the Page FK or suffix mapping is approved.

### Triage priorities (not dispositions)

| Priority | Meaning |
|---|---|
| `P0_IMAGE_AMBIGUOUS_OR_INVALID` | 0024 match missing/ambiguous or catalogue/file verification failed: resolve explicitly or DEFER |
| `P1_UNOWNED_NO_DATE_PAGE_HINT` | No direct Page, and no unambiguous Page anchor among other fragments on date |
| `P2_UNOWNED_DATE_CONTEXT_HINT_ONLY` | No direct Page, but other fragments on same date suggest candidate Page IDs; never assign automatically |
| `P3_PAGE_RELATIONSHIP_REVIEW` | Unexpected Page/Marquee shape needs manual interpretation |
| `P4_PAGE_AGREES_BUT_SUFFIX_UNREVIEWED` | Direct and Marquee Page IDs agree; independent Page FK, image suffix and disposition review still needed |

**Important:** do not fill the final `0028-dispositions.csv` or `0028-image-decisions.csv` from this tool. The migration needs full human-approved decisions for every Fragment/occurrence, including `KEEP_LEGACY` and `DEFER`, plus Step 2 manifest validation, dry-run and replay. The 50 currently unowned fragments are not safe to convert without explicitly validated Page assignment.

## 4. What to return for further planning

Send the **console aggregate output** only; it prints no private fragment IDs or paths. The private CSV and HTML should remain on `mango`/your secured Windows workstation. After examining the counts, review human decisions in the private dossier; Step 1 stays **OPEN** until signed-off dispositions and matching evidence are ready.
