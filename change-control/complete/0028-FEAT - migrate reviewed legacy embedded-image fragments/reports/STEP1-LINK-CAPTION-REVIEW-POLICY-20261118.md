# 0028 Step 1 — Review policy: external links, captions and Page ownership

**Status: proposed review policy / implementation prerequisite, not a signed approval.**
**Basis:** `diaries-sources-20261118-112949.zip`, the frozen 09:36 UTC
production snapshot, verified 0024 reconciliation, 11:02 UTC triage,
and separately generated 72-row unapproved content proposals. Original review
hashes passed on `mango` at 12:03 UTC on 18 November 2026. No production
DB/MQTT change has been executed for 0028.

## Confirmed current-state constraints

- All 72 old `<img>`-bearing source Fragments have `type=NULL` (intentional
  historical 0022 state); 71 match an existing Image through the
  **UNIQUE_LOCAL_SUFFIX** fallback and one is ambiguous. Suffix matching is
  **not** an approval of the Image ID/path/checksum.
- Of 72, **22 have agreeing direct and Marquee Page IDs**, all 22 with
  clickable external links wrapping their images. The other **50 have no
  Page or Marquee**; 36 have one same-date Page *hint* and 14 have multiple.
- **30** contain a hyperlink *around the image*; migration to current IMAGE
  display **does not preserve that click target**. The current
  `diaries-web` templates render IMAGE media separately and link the
  fallback to the local media URL, not the original external target.
  Do not treat a preserved URL in documentation or separate text as
  preservation of the original image-click behaviour.
- **69** contain `<figcaption>` content and **3** contain a bare image.
  The existing Image catalogue snapshot records ID/path/checksum/MIME/dimensions,
  **not the original figure caption**. Reader media caption and alt-text
  currently derive from Image metadata. A conversion must explicitly plan
  where original caption HTML, links and text live and verify the resulting
  client and reader display. Two figures contain stray quotation-mark text;
  one ambiguous candidate additionally contains substantial narrative prose.
- `diaries-web` currently omits fragments lacking an associated Page from its
  Page-based projection. Assigning one can alter public visibility. This is
  a substantive publication decision, not a mere FK repair.

## Proposed fail-closed decision rules for 0028

1. **Image hyperlink:** Do **not** convert any of the 30 image-wrapped links
   using the current IMAGE presentation. Reviewer may explicitly choose
   `KEEP_LEGACY` (compatibility exception) or `DEFER` (open work). To convert
   these later, first design, implement and test *equivalent clickable-image
   behaviour* across client and reader, then obtain approval for the expanded
   contract. This change is **not** part of the current 0028 Step 1 package.
2. **Unowned Page:** An adjacent same-date Page is a hint only. For any
   mutation, require a confirmed existing Page ID plus independent provenance;
   validate that Page against fresh DB state in Step 2 preflight. If ownership
   cannot be verified, choose `DEFER` with a reason. Do not make Page-less
   content public by guesswork.
3. **Suffix Image match:** The 71 matches need reviewer-confirmed canonical
   path, Image ID, checksum and file identity. Do not infer authorisation from
   `MATCHED_ONE_IMAGE` or a checksum alone.
4. **Caption/text:** Preserve original captions, links and stray markup
   in a reviewed text allocation, with source-to-output HTML diff and
   postflight client/reader screenshot/DOM assertions. The three bare-image
   cases require explicit acknowledgement of missing caption/text. This
   package does not perform HTML transforms.
5. **Marquee:** Do not remove a real Marquee without explicit geometry/source
   review. A split is appropriate only if there is genuine retained
   transcription. Never create a redundant empty Marquee or silently alter
   chronology.
6. **No-ops:** `KEEP_LEGACY` and `DEFER` do not alter HTML, Page, type,
   Marquee, Image, visibility or chronology. They remain explicit exceptions
   to be tracked in 0029. All 72 decisions need reviewer identity, timestamp,
   reason and stable source hashes.

**Consequence:** There are **currently zero unconditionally safe automatic
conversions**. Of the 41 unlinked/unowned unique-image candidates, individual
conversions may become eligible after authoritative Page determination,
independent image verification and text/presentation review. The 30 linked
cases cannot be converted without preserving hyperlink semantics. The one
ambiguous-image case should remain deferred until independently resolved.

## Review tool

`tools/step1_review_portal.py` builds an entirely local private HTML review
portal from the verified frozen input and proposal CSV. It does **not** load
any source image or HTML as executable markup. It offers searchable evidence,
manual decision fields, private JSON draft export/import, and an offline
`check` operation with source identity and review-policy gates. No default
choices are populated. A reviewer may explicitly record no-op decisions.
The checker is **not** an 0028 manifest validator, cannot sign approvals, does
not verify live Page existence, and always sets `productionApplyAllowed=false`.

The private portal and JSON drafts must remain in
`evidence/Step 1/private/` or another protected local copy. They must not be
committed to Git, included in the public Diaries package or published on
`pluto`. Do not alter original historical checksum manifests.

## Remaining work / formal Step 1 gate

A human must review every candidate and occurrence, resolve or expressly
acknowledge remaining deferrals, decide whether 0028's scope should add linked
IMAGE support, and approve the exact 0028 manifests before any apply.
Step 2 must implement the production migration validator and lossless
transformation before any dry-run is executable. Until then **Step 1 OPEN**.
