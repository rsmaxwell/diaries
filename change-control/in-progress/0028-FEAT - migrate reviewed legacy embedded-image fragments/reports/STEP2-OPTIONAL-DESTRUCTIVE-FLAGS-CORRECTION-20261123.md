# 0028 Step 2 — Optional no-destruction flags compatibility correction (2026-11-23)

## Evidence and cause

Windows Cygwin run `20261123T153212Z-java-check` completed the full responder Gradle build and JUnit suite, but `validate-manifest` failed on Fragment 725 with `Destructive operation is outside reviewed scope 725`.

The recovered, approved-for-review V2 JSON has 72 occurrences, 71 `CONVERT_TO_IMAGE` and one `DEFER`. The optional fields `review_clear_confirmed` and `review_remove_marquee_confirmed` contain `NO` for 46 occurrences and are **absent for 26** earlier reviewed occurrences (including Fragment 725). The Step 1 generator represents absent optional fields as empty CSV strings. The original Step 2 Java reader incorrectly required the literal `NO` for every conversion.

There is no indication of an authorisation to delete a Marquee or clear a link in the reviewed source. Both no-authorisation representations are valid **only** when the operation preserves all reviewed links and Marquees.

## Narrow fix

- Accept `""` (blank) or `"NO"` as an absence of permission for either destructive operation.
- Reject `YES`, null or any other value. This is **not** approval to perform deletion or clearing.
- Preserve separate `PRESERVE`/`NOT_PRESENT` link validation and `PRESERVE`/`NOT_APPLICABLE` Marquee validation, the 30/22 source checks, hash-pinned manifest identity, no-apply receipt, and database/source guards.
- Leave all manifest and Step 1 evidence files unchanged. No database operation is part of this correction.

## Verification

Add `ReviewedInputsTest` covering blank/NO acceptance and explicit/malformed/null rejection. Re-run `verify-0028-step2-local.sh` in the authoritative Windows checkout to test the real responder and the exact prepared 72-row manifest. A full Windows Gradle run remains pending; local Java compilation is only a supporting check.

## Status

0028 Step 2 local verification remains OPEN until the rerun passes. Step 1 evidence remains as recorded. Production migration and its apply authority remain NOT APPROVED.
