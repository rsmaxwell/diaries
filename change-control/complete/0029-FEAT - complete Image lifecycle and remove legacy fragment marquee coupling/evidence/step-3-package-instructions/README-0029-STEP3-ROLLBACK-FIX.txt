0029 Step 3 — repair isolated production rollback failure, 26 November 2026

Apply using Beyond Compare 4 at the Windows Diaries repository root.
Only two feature files: the existing rollback SQL and a new failure/correction report.
Preserve unrelated modifications. The test runner and forward SQL are unchanged.

Then rerun from the Windows 11 Cygwin terminal (Diaries parent root):

  bash 'change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling/tools/run-step3-isolated-production-migration-rehearsal.sh'

The runner reads production only using pg_dump, performs schema changes only
in a local container with --network none, and saves evidence under the feature.
Do not apply the rollback SQL directly to production.
