# 0028 Step 3 — Native Windows JAR membership check correction (24 November 2026)

## Observed

- Responder source commit `7aa6296` succeeded with the 14 intended files; responder working tree clean.
- Gradle 9.6.1 `:diaries-responder:shadowJar` completed successfully (4 actionable tasks), but the source release script then said `FAIL: built JAR does not include reviewed migration CLI`.
- Root cause **suspected, not yet confirmed against the actual built JAR**: native Windows `jar tf` uses CRLF record delimiters, while Cygwin `grep -Fx` expects an exact line without the trailing carriage return. This can make a present class appear absent.

## Correction

Replace text matching of `jar tf` output with direct archive inspection through Python standard-library `zipfile`. Fail closed if the exact migration class and SQL resource do not each appear once, are empty, or are unreadable/CRC-invalid. Preserve all prior source identity, clean-tree, checksum, private evidence and no-production safeguards. This is a release-script-only fix: **do not modify the already committed Java source or rebuild production images**.

The fat JAR's ordinary `Main-Class` is the normal responder. The disposable migration main must be invoked explicitly with `java -cp <fat-JAR> com.rsmaxwell.diaries.responder.migration.migration0028.Migration0028ReviewedFragments ...` in a separately approved runner, **not** using `java -jar` or by restarting the responder.

## Follow-up

Apply the ZIP at the Diaries parent root using Beyond Compare 4. On Windows Cygwin:

```bash
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
python3 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tests/test_step3_jar_verifier.py'
bash 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tools/prepare-0028-step3-release-artifact.sh'
```

If the same class truly is missing, the new error lists related migration entries instead of misreporting a line-ending mismatch. Keep the release gate OPEN and inspect the Gradle outputs, without deploying or applying the migration.
