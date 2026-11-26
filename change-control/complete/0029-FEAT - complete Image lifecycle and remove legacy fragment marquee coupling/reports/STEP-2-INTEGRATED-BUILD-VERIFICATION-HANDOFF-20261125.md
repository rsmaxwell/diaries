# 0029 Step 2 — Integrated development build verification

This helper captures a consolidated compile/test baseline for the **candidate source**, not evidence of an already passing build. It does not run schema SQL, change production, or deploy images.

1. Review and apply the **latest consolidated application candidate** `0029-FEAT-step2-integrated-annual-image-link-review-20261125.zip` using Beyond Compare 4. Do not overlay the older candidate ZIPs. Check and preserve pre-existing uncommitted work in each Git submodule before applying.
2. In **Windows 11 Cygwin**, from the Diaries parent checkout, run `bash "change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling/tools/step2-verify-integrated-builds.sh"`.
3. If Angular dependencies are missing, run `( cd diaries-client && npm ci )` then rerun the script. Review logs before making fixes.

Results and full diagnostic output are saved under `evidence/step-2-build/`. A `PASS` means the invoked command exited zero. The script runs all checks even if an earlier check fails. The database migration is **not approved for execution** by these checks alone.
