# 0051 Step 3 — Retained-snapshot decoding correction (20 November 2026)

## Evidence and disposition

- Windows PowerShell 7 integrated smoke run: `20261120T134606Z-129d5f72`.
- Its disposable responder/web candidate build and MQTT barrier succeeded. The runner had already exercised the four IMAGE variants (including desktop/source page and mobile combined variant) before the retained-state assertion failed.
- Error: `SyntaxError: "[object Object]" is not valid JSON` in `tests/step3-isolated-reader-smoke.cjs`, formerly at line 534.
- Cause: `scripts/windows/validation/imagefragment-retained-snapshot.cjs` already parses the retained JSON and returns topic entries as `{ sha256, payload }`. The 0051 test called `JSON.parse()` on that envelope.
- Correction: access the decoded `entry.payload` after checking that a topic is present and carries a SHA-256 hash. Fix all corresponding post-restart and post-deletion assertions, not just the first failure.
- Additional test gap fixed: the 0026 shared snapshot subscribes to `diaries/fragments/+` and `diaries/images/+`, **not** `diaries/marquees/+`. The old absent-Marquee assertion on that snapshot could not prove deletion. A separate QoS-1 replay/barrier probe now verifies that the Marquee topic is retained before deletion and absent after deletion.

## Operational scope

Only the feature-specific `.cjs` smoke runner changes. No application source, database schema, standard Playbooks, production data or shared 0026 snapshot helper changes. Preserve the historical failed-run evidence in `evidence/Step 3/private/integrated-20261120T134606Z-129d5f72/`.

## Verification and acceptance

The ZIP is source-validated with `node --check` and checksum/ZIP-integrity checks. **It has not been rerun against Docker and Chrome/Edge** here. Run the same Step 3 script from Windows PowerShell 7 and review the new generated summary and SHA256SUMS. Steps 1–2 remain CLOSED; Step 3 remains OPEN pending successful integrated browser smoke and separate Angular editor visual acceptance.
