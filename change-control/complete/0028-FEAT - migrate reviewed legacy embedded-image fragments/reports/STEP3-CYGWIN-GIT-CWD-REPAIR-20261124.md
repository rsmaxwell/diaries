# 0028 Step 3 — Git working-directory compatibility correction (2026-11-24)

## Observation

The user ran `repair-0028-gradle-diff.py --apply` from Windows Cygwin; its first
Git operation failed with `fatal: cannot change to /cygdrive/c/.../diaries-responder`.
The repair failed before writing or staging `build.gradle`; the 1083-line diff remains.

## Cause and correction

The script used `git -C /cygdrive/c/...`, but Git resolves to a native Windows
executable that does not interpret Cygwin `/cygdrive` paths. The repair helper
now executes Git with `cwd=<responder directory>` and omits `-C`. The OS
establishes the working directory natively for the spawned Git process.

No migration code, Gradle task content, release policy, or backup and production
files are changed by this package. The original script still refuses unrelated
Gradle edits, saves pre-change evidence, and verifies exactly 31 insertions
and zero deletions before reporting success.

## Follow-up

Apply this ZIP into the Diaries parent checkout, then run:

```bash
python3 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tools/repair-0028-gradle-diff.py' --apply
git -C diaries-responder diff --cached --check
git -C diaries-responder diff --cached --stat
```

Do not commit if the repaired `build.gradle` diff is not 31 insertions, zero deletions.
Production apply remains unauthorised.
