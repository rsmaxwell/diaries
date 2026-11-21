# 0051 — Next read-only validation (after applying ZIP)

Step 1 static source checks passed in the assistant's extracted bundle. The remaining **live production baseline** is a read-only command executed from the **Windows 11 Cygwin terminal**; the command runs a separately launched non-interactive Bash process on **pluto**. It records metadata into the existing ignored feature-private evidence directory on the Windows repository. It does not transfer a script, mutate production, restart containers or change the DB.

```bash
if cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries; then
  feature='change-control/in-progress/0051-FEAT - extend IMAGE fragments with links and optional marquees'
  mkdir -p "$feature/evidence/Step 1/private"
  if ssh pluto 'bash -s' < "$feature/tools/step1-readonly-production-baseline.sh" > "$feature/evidence/Step 1/private/live-production-baseline.log" 2>&1; then
    echo 'PASS: 0051 production baseline captured'
  else
    echo 'FAIL: 0051 production baseline capture — diagnostic output follows'
    tail -100 "$feature/evidence/Step 1/private/live-production-baseline.log"
  fi
else
  echo 'FAIL: Windows Diaries repository not found'
fi
```

The command safely reports failures without changing your interactive shell's error handling. The output is private evidence, not suitable for inclusion in public change-control ZIPs.

**Separate Windows Cygwin check** of the local baseline source (no production access):

```bash
cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries
python3 'change-control/in-progress/0051-FEAT - extend IMAGE fragments with links and optional marquees/tests/step1-static-baseline.py'
```

Compare the live images/gate/schema with the frozen source versions in `evidence/Step 1/local-source-baseline.json` and the Step 1 contract. Application runtime baseline checks still require a genuinely isolated local DB/MQTT/Files mode and were not performed by these read-only checks. No 0028 production conversion is permitted by this run.
