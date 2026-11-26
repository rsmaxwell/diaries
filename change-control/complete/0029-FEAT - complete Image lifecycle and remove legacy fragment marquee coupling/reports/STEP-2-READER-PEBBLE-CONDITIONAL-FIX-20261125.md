# Step 2 — Reader Pebble list-conditional correction (2026-11-25)

## Evidence

Windows reader JUnit XML diagnostics show HTTP 500 for month render caused by `io.pebbletemplates.pebble.error.PebbleException: Unsupported value type ListN. Expected Boolean, String, Number in "if" statement (month-reader.peb:70)`.

## Correction

Use Pebble `is not empty` tests on `annualPreamble` and `annualPostamble` instead of passing Java lists directly to `if`. The existing six HTTP and five MQTT tests should exercise the resulting rendering; the separate `RenderingSafetyTest` adjustment was supplied in the prior overlay. No SQL or production changes.

## Verification status

Source comparison and ZIP integrity verified in authoring environment. Full Java reader test run must be completed on Windows.

## Windows Cygwin command

From the Diaries parent root: `./gradlew :diaries-web:test --console=plain`
