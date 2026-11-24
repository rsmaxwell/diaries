# 0028 Step 3 — responder Gradle diff repair (2026-11-24)

The source-control inspection on Windows showed that `diaries-responder/build.gradle` had 1,083 changed lines (1,669 insertions and 526 deletions across 14 staged files). The 0028 CLI requires one added Gradle task, not reordering the existing versioning helpers, 0022/0024 migration tasks or publishing configuration.

## Non-production remedy

Run `python3 "change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tools/repair-0028-gradle-diff.py"` from the Windows Diaries parent repository to check without writing. Use `--apply` after that check to reconstruct **only** `build.gradle` from the `diaries-responder` HEAD and insert the exact reviewed 0028 task immediately before the existing 0024 task. The tool checks the entire remaining non-0028 line multiset against HEAD; it refuses to discard any changed nonblank content. It backs up the previous working version in feature-private evidence and stages only `build.gradle`.

The 13 staged Java/SQL/test files remain unchanged. Inspect the new staged diff before committing the disposable 0028 CLI. No responder builds, migrations, Git commits, pushes, backup operations or production service changes are performed by this tool.

After staging a minimal diff, commit the intended files in `diaries-responder`, then rerun the existing release-artifact preparation script; formal production gates remain OPEN.
