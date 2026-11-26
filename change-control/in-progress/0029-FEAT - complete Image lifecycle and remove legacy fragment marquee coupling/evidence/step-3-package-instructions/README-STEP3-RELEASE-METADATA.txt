0029 Step 3 release metadata audit — 2026-11-26

Apply the repository-relative change-control/ files to the Windows Diaries parent repository with Beyond Compare 4.

Windows 11 Cygwin terminal:
  cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries
  bash 'change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling/tools/run-step3-production-release-metadata-audit.sh'

Read-only audit; production deployment NOT authorised. Inspect the evidence log and report any FAIL checks. Do not paste secret-bearing ansible-inventory output.
