# 0028 Step 1 — Private offline reviewer and draft checker

**Purpose:** inspect all 72 legacy-image candidates and record explicit,
private review decisions without copying private content into Git or
changing production. Requires Python 3.10+ standard library only.

The primary source package installs only the public script, test and
non-private documentation. An optional separate private reviewer HTML is
created from the supplied source snapshot for local inspection. Treat the
HTML as **sensitive production diary content**.

## Option A — Open the prebuilt private review

Unpack the separately supplied PRIVATE reviewer ZIP on a trusted Windows PC,
outside Git, and open `0028-offline-review.PRIVATE.html` locally in Edge.
Do not post it on a website or open original external links from it (all
are displayed as text). The portal performs no network requests. Save work
periodically with **Export PRIVATE JSON draft**, then use **Import existing
draft** to resume. Browser state is NOT saved between sessions.

## Reviewer convenience defaults (18 November 2026 update)

- **Caption override** is optional. When blank, the portal and checker use the
  caption text extracted from **exactly one** unambiguous `<figcaption>` in the
  frozen, hash-verified original fragment. The resolved caption and its source
  appear in the browser and exported draft as `caption_effective` and
  `caption_source`. For example, Fragment 84 defaults to `Whitley Park`.
  Enter a caption override only when a different caption is intended. Empty or
  ambiguous original captions do not acquire a guessed default; the reviewer
  must acknowledge missing text or explicitly resolve ambiguous markup.
- **Reviewer identity** entered at the top of the portal or in a fragment is
  reused as the default for subsequent fragments. It does not overwrite a
  previously recorded identity. When importing a draft, the most recently
  recorded reviewer identity is restored to the toolbar if it is blank.
- **Review timestamp** is the current UTC time, captured automatically on the
  first substantive edit of a fragment. Revisiting a fragment does not change
  its saved review time. The **Stamp selected row** button deliberately updates
  the selected row's time and reviewer; individual timestamps remain editable.
  Merely displaying or exporting an unreviewed fragment does not stamp it.
- **Draft compatibility:** existing `0028-human-review-v1` exports still import
  without loss of decisions or timestamps. The new caption fields are additive.
  No browser state is saved automatically between sessions; export/import the
  PRIVATE JSON to retain decisions and reviewer identity after closing Edge.
- The caption fallback is a **review/validation contract only**. Step 2 still
  has to implement caption retention in the new IMAGE model, validate client
  and reader rendering, and independently verify Page and Image references.
  It must not silently mutate existing Image catalogue caption metadata.

The generated review file is not executable migration evidence. On completion,
copy the exported `0028-human-review.DRAFT.PRIVATE.json` to the protected
feature `evidence/Step 1/private/` folder on `mango` via WinSCP.

## Option B — Rebuild from the frozen production evidence on mango

In the **mango SSH terminal**, after checking out/synchronising the public
source files, ensure the private proposed-review CSV is present. It can be
copied from your Windows evidence folder via WinSCP if needed, including its
matching `SHA256SUMS.txt` and `0028-proposal-summary.json`. Keep the two
original 2026-11-18 evidence runs unchanged.

```bash
cd /home/richard/diaries
FEATURE='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
PRIVATE="$FEATURE/evidence/Step 1/private"
FROZEN="$PRIVATE/20261118T093606Z"
PROPOSED="$PRIVATE/0028-proposed-review.PRIVATE.csv"
OUT="$PRIVATE/$(date -u +%Y%m%dT%H%M%SZ)-portal"

if python3 -m unittest discover -s "$FEATURE/tests" -p 'test_step1_*.py' -v && \
   python3 "$FEATURE/tools/step1_review_portal.py" build \
      --proposals "$PROPOSED" --frozen "$FROZEN" --output "$OUT" && \
   (cd "$OUT" && sha256sum -c SHA256SUMS.txt); then
    echo 'PASS: protected offline portal generated; decisions are not approved'
else
    echo 'FAIL: portal generation or evidence validation'
fi
```

The portal input is always checksum-checked, including the frozen current
schema inventory. It refuses an already existing destination directory.
Retrieve the resulting private HTML from `mango` using your WinSCP session
and open locally on Windows. Do not put these generated private files into
Playbooks, the public source bundle, or a Git commit.

## Check an exported decision draft

Copy the exported JSON back into the private evidence directory on `mango`.
In the **mango SSH terminal**:

```bash
cd /home/richard/diaries
FEATURE='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
PRIVATE="$FEATURE/evidence/Step 1/private"
FROZEN="$PRIVATE/20261118T093606Z"
PROPOSED="$PRIVATE/0028-proposed-review.PRIVATE.csv"
DECISIONS="$PRIVATE/0028-human-review.DRAFT.PRIVATE.json"
OUT="$PRIVATE/$(date -u +%Y%m%dT%H%M%SZ)-review-check"

if python3 "$FEATURE/tools/step1_review_portal.py" check \
      --proposals "$PROPOSED" --frozen "$FROZEN" \
      --decisions "$DECISIONS" --output "$OUT" && \
   (cd "$OUT" && sha256sum -c SHA256SUMS.txt); then
    echo 'PASS: draft checker executed (NOT migration authorisation)'
    cat "$OUT/0028-review-draft-check.json"
else
    echo 'FAIL: draft checks or evidence identity'
fi
```

The JSON report includes counts and blocker categories only, not private
fragment IDs or URLs. `KEEP_LEGACY` and `DEFER` are no-op outcomes; unresolved
case counts remain visible. A conversion with an image-wrapping hyperlink is
always blocked until equivalent first-class support is implemented and
tested. A conversion without Page provenance, suffix confirmation or text
allocation is also blocked.

**No database, Files-root, MQTT or existing evidence changes** occur.
Even if every draft row passes the checker, `productionApplyAllowed=false`.
Step 1 acceptance and Step 2's actual migration-manifest validation are
separate operations requiring explicit reviewer approval and tests.
