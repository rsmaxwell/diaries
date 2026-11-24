# 0028 — Step 1 exact migration-input preparation after 0052

**Prepared:** 2026-11-23. **Step 1 OPEN; production migration NOT authorised.**

## Actual read-only evidence received

The Windows Cygwin command `verify-0028-step1-post0052-readonly.sh` was run at `20261123T143827Z`, with the terminal log uploaded as `note(20261123-143854).txt`. Observed results:

- Five regression tests PASS.
- Fresh production inventory: 2331 Fragments, 72 legacy candidates/embedded occurrences, 141 broader structural exceptions.
- All 72 recovered V2 decisions checked against frozen and fresh production sources; **zero blockers**.
- 71 `CONVERT_TO_IMAGE`, one explicit `DEFER` (Fragment 1564).
- Catalogue reconciliation PASS; 0052 metadata changes confined to Image IDs **3** and **18**.
- No production migration authorised and no database changes made by that validation.

The 141 broader structural exceptions are not newly cleared or silently excluded from the source evidence. They need explicit treatment in the migration plan and final acceptance where relevant. Prior 0022/0024 historical generated CSV availability must not be invented.

## New preparation utility (no production writes)

`tools/step1_prepare_reviewed_manifest.py` combines the **actual** read-only post-0052 production snapshot, V2 compatibility check, post-0052 Image mapping and recovered reviewer draft into a reproducible Step 2 input set. It verifies the review/snapshot SHA-256 against the successful reconciliation and fails closed if source HTML, versions, Image ID/checksum, Page decisions or reviewed link/Marquee policy differ. It deliberately disallows any destructive clear/remove operation in this reviewed set and checks that 30 links and 22 Marquees are explicitly preserved.

Inside a fresh ignored `evidence/Step 1/private/<UTC>-reviewed-manifest-prepared/`, it writes:

- `0028-dispositions.csv` — one original Fragment preimage row per 72 reviewed sources, original Page separate from approved destination Page.
- `0028-image-decisions.csv` — one source-image occurrence row per 72 reviewed occurrences with current, exact Image checksum for 71 approved conversions; the deferred occurrence remains unresolved.
- `0028-v2-preservation-decisions.PRIVATE.csv` — additional 0051-era **explicit link, Marquee, approved destination Page, exact approval/identity, caption and text-allocation policy** not represented by the older CSV templates.
- `PREPARATION-RESULT.json`, `SHA256SUMS.txt`, `git-and-input-identity.txt` — hashes, counts, input identities and source-control information.

**Important:** `PREPARED_NOT_APPROVED` means these are the exact *candidate* migration inputs, not a signed-off apply plan. Java `validate-manifest` and `dry-run` must consume/enforce the supplementary V2 contract or equivalent exact V2 fields. It must not silently ignore the 30 linked occurrences or 22 preserved Marquees. The old `UNIQUE_LOCAL_SUFFIX` matching is only a reviewed matching provenance, not permission to use basename inference in apply.

## Execute — Windows PC, Cygwin terminal

From the authoritative Windows Diaries parent working copy after applying the ZIP with Beyond Compare:

```bash
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'

bash 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tools/prepare-0028-step1-reviewed-manifest.sh'
```

No SSH, Docker, database mutation, MQTT operation or File-root write occurs in this preparation command. It uses the already accepted 23 November production snapshot rather than collecting another expensive inventory. The tool requires Python 3 and the ignored private review/evidence files, and writes only a new private feature evidence directory.

## Acceptance boundary

After this preparation succeeds, record owner acceptance of the exact input hashes and explain the 0022/0024/141-exception scope. **Step 1 stays OPEN until its acceptance gate is accepted.** Then implement the coherent Step 2 Java workflow in `diaries-responder` with strict manifest and V2 policy parsing, source-preserving conversion, date transactions, journal/idempotency, dry-run/postflight and tests. No production apply before disposable restored rehearsal and separate approval.
