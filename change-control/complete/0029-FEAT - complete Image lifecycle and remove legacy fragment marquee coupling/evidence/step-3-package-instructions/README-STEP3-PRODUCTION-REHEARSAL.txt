0029-FEAT Step 3 — production-shaped isolated migration rehearsal

Apply the two repository-relative paths using Beyond Compare 4 to the Windows Diaries parent repository; do not replace other local files.

Execute in Windows Cygwin Bash from Diaries root:

bash 'change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling/tools/run-step3-isolated-production-migration-rehearsal.sh'

The script performs only a read-only pg_dump against pluto; SQL modifications occur only in a local --network none disposable PostgreSQL container. Do not run any production deployment yet.
