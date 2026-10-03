# 0032 Step 6 close-out — Deploy the production cleanup non-destructively and verify `pluto`

## Status

**COMPLETE — 2026-10-03**

## Objective

Apply the Step 5 production-tooling cleanup to `pluto` through the normal controlled Diaries deployment path, remove only the approved completed-feature helpers, and prove that supported production tooling, production configuration and service health remain intact.

## Evidence sequence

1. A fresh read-only pre-deployment capture on `pluto` created `PLUTO-SCRIPTS-PRE.txt` and `PRODUCTION-CONFIG-PRE.txt`.
2. The guarded deployment wrapper on `mango` reran the three permanent Playbooks validators successfully before invoking the normal Diaries deployment.
3. Ansible explicitly removed the eight approved completed-feature production helpers and did not use unrestricted `rsync --delete`.
4. The play completed successfully with `failed=0`, `unreachable=0`, exit code `0`.
5. A read-only post-deployment capture on `pluto` created `PLUTO-SCRIPTS-POST.txt`, `PRODUCTION-CONFIG-POST.txt` and `PRODUCTION-STATUS.txt`.
6. `verify-step6-evidence.bat` compared the complete evidence set and generated `DIFF.md` and `VERIFICATION-OUTPUT.txt`.

## Approved removal set

Exactly these eight files were removed from the deployed production scripts directory:

```text
migration0024ImageCatalogue.sh
step8-freeze-writes.sh
step8-capture-production-database-backup.sh
step9-reconcile-production.sh
step12-compare-reconciliation.py
step12-reconcile-production.sh
step13-capture-production-control.sh
step14-production-deployment.sh
```

No other production script removal is accepted by this step.

## Final verification result

The final verifier reported PASS for every required condition:

- fresh pre-deployment filenames exactly matched the Step 1 baseline;
- fresh pre-deployment hashes exactly matched the Step 1 baseline;
- post-deployment names exactly matched the approved permanent production set;
- all eight approved retired helpers were absent;
- the deployment removed exactly the eight allow-listed helpers;
- retained operational scripts were owner-executable;
- all five retained synchronized operational helpers matched approved Step 5 source hashes;
- production `.env`, `compose.yaml` and responder configuration fingerprints were unchanged;
- non-secret database/Files selectors and contract lines were unchanged;
- the controlled Playbooks deployment completed with `failed=0`, `unreachable=0`, exit code `0`; and
- all five required Diaries services were running and healthy.

Final result:

```text
PASS: Step 6 production cleanup evidence verified.
```

## Safety conclusion

The cleanup was non-destructive with respect to Diaries application data and runtime configuration. The evidence shows no change to the production database/Files selection contract or responder configuration fingerprints, and the application remained healthy after deployment.

No database restore, database-row mutation, schema change, mutable Files mutation, Image lifecycle mutation or retained-MQTT cleanup was part of this step.

## Completion decision

Step 6 satisfies its completion rule: `pluto` contains no approved retired helpers, supported permanent operational tooling remains intact, and production health/status checks pass.

**Step 6 is closed.**

## Next step

Proceed to **Step 7 — Add permanent anti-accumulation guards and feature-close-out guidance**.
