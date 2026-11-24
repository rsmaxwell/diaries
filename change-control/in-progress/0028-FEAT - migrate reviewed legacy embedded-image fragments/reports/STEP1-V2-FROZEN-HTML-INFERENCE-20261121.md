# 0028 Step 1 — Frozen-HTML inference for v2 reviewer (21 November 2026)

## Scope and input precedence

Feature-specific, offline reviewer-only change, based on the previously delivered 0028 v2 original-HTML package (21 November 2026), retaining the earlier safe-source-field logic. The 21 November user-exported private v2 draft with Fragment 1564's signed `DEFER` record was used as non-shipped acceptance input. No Diaries application, responder, Playbooks, production database, MQTT or image file was modified. The 0028 feature remains **IN PROGRESS / Step 1 OPEN**.

## Inference design

- Reuse SHA256-verified frozen original HTML, source image occurrence identity, original `<a href>` link identity, catalogue/file reconciliation, fragment date/sequence, existing Page association and historical v1 review hints.
- The two existing fill buttons now suggest `CONVERT_TO_IMAGE` / `REMOVE_AS_IMAGE` **only** when the entire original HTML is a single image with an optional simple `<figure>`, `<figcaption>` and exact linked `<a>` wrapper; its catalogue/file match is confirmed, the link is unambiguous and safe, the source has no Marquee and no live source drift is reported. Any independent text, stray punctuation, complex markup, comments, multiple images, unknown image attributes, or existing Marquee means manual conversion review.
- Existing `NOT_PRESENT`/`PRESERVE` link and exact decoded URL suggestions and absent/complete-Marquee handling remain. In particular, never suggest link clearing or Marquee deletion.
- Show `imgNNNN` **filename hint** and historical proposed Page ID as hints, **not verified Page ownership**. The frozen snapshot does not contain authoritative Page-name-to-Page-ID records. Draft `page_provenance` explicitly states the original Page relationship and what still requires verification. **Never automatically fill `approved_page_id` or `suffix_verified`.**
- For clean one-image sources, draft `text_allocation` specifies the original caption (or no caption), source date, source sequence, link preservation, and absence of independent narrative. Only fill blanks and preserve other choices. A conflicting existing disposition/action prevents automated conversion fields.
- Preserve `review_note`, `reviewed_by`, `reviewed_at`, `v2_review_confirmed`, both destructive-operation confirmations, private source identities/fingerprints, draft JSON schema and import/export behaviour. Material changes to a previously signed row still clear its timestamp, as before. No suggestion authorises migration.

## Automated verification (local, private)

- 31 Python `test_step4_0051*.py` tests passed (23 existing tests + 8 new inference tests).
- Independently enumerated all 72 frozen HTML previews from the sealed 2026-11-18 snapshot; 47 met conservative single-image inference, 25 required manual conversion decisions.
- Actual Chromium UI acceptance on the 72-row draft passed: import/export of signed Fragment 1564 unchanged, Fragment 84 suggested conversion plus standard source/chronology/Page text, Fragment 96 withheld conversion due to stray quote, Fragment 1251 retained exact original link and Marquee, bulk fill produced 47 unapproved conversion suggestions and **zero** `v2_review_confirmed` approvals; no external requests or JavaScript page errors.
- The latest signed Fragment 1564 review remained unchanged after bulk prefill. No evidence or user JSON was modified. This is **tooling verification**, not Step 1 acceptance or permission to migrate.

## Windows review procedure

Apply the small repository-relative ZIP at the Windows Diaries repository root using Beyond Compare 4; inspect differences against local uncommitted work. Then, in the **Windows PC / Cygwin terminal**:

```bash
cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries
feature='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
python3 -m unittest discover -s "$feature/tests" -p 'test_step4_0051*.py' -v
v2="$feature/evidence/Step 1/private/20261121T122838Z-post0051-v2"
python3 "$feature/tools/step1_refresh_0051_portal_offline.py" \
  "$v2/0028-0051-review-v2.DRAFT.PRIVATE.json"
cygstart "$v2/0028-0051-review-v2.SOURCE-SUGGESTIONS.PRIVATE.html"
```

Import the latest *exported* `0028-0051-review-v2.DRAFT.PRIVATE(2).json` from browser Downloads. Inspect suggested values before stamping each review. The original sealed v2 JSON and its SHA256SUMS remain unchanged; the script refuses to replace an already existing source-suggestions HTML file. Export the new private draft periodically. Do not place private HTML/JSON/source CSV into a public Git commit or ZIP package.

## Pending gates

Step 1 still needs review of every occurrence, independent Page/image reconciliation, 0022/0024 evidence and the 141 structural exceptions, followed by explicit acceptance. Later migration/rehearsal/production steps remain independently gated.
