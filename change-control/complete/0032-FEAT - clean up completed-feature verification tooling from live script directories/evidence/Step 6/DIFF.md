# 0032 Step 6 production cleanup diff

## Result

**PASS**

## Verified observations

- Fresh pre-deployment script filenames exactly match the Step 1 baseline.
- Fresh pre-deployment script hashes exactly match the Step 1 baseline.
- Post-deployment script names exactly match the approved permanent production set.
- All eight approved retired production helpers are absent after deployment.
- The deployment removed exactly the eight allow-listed obsolete helpers.
- All retained operational scripts are owner-executable.
- All five retained synchronized operational helpers match the approved Step 5 source hashes.
- Production .env, compose.yaml and responder.json fingerprints are unchanged.
- Non-secret production database/Files selectors and contract lines are unchanged.
- Controlled Playbooks deployment completed successfully with failed=0, unreachable=0 and exit code 0.
- All five required Diaries services are running and healthy after deployment.

## Removed by deployment

- `scripts/migration0024ImageCatalogue.sh`
- `scripts/step12-compare-reconciliation.py`
- `scripts/step12-reconcile-production.sh`
- `scripts/step13-capture-production-control.sh`
- `scripts/step14-production-deployment.sh`
- `scripts/step8-capture-production-database-backup.sh`
- `scripts/step8-freeze-writes.sh`
- `scripts/step9-reconcile-production.sh`

## Post-deployment script set

- `scripts/README.md` — mode `664`, owner `richard:richard`
- `scripts/backup-db-to-binary.sh` — mode `755`, owner `richard:richard`
- `scripts/backup-db-to-sql.sh` — mode `755`, owner `richard:richard`
- `scripts/dataset-backup-manifest.py` — mode `755`, owner `richard:richard`
- `scripts/logs.sh` — mode `744`, owner `richard:richard`
- `scripts/restore-db-from-binary.sh` — mode `755`, owner `richard:richard`
- `scripts/restore-db-from-sql.sh` — mode `755`, owner `richard:richard`
- `scripts/shell-prompt-client.sh` — mode `744`, owner `richard:richard`
- `scripts/shell-prompt-database.sh` — mode `744`, owner `richard:richard`
- `scripts/shell-prompt-mosquitto.sh` — mode `744`, owner `richard:richard`
- `scripts/shell-prompt-nginx.sh` — mode `744`, owner `richard:richard`
- `scripts/shell-prompt-responder.sh` — mode `744`, owner `richard:richard`
- `scripts/start.sh` — mode `744`, owner `richard:richard`
- `scripts/status.sh` — mode `744`, owner `richard:richard`
- `scripts/stop.sh` — mode `744`, owner `richard:richard`

## Configuration fingerprint

- `.env` — `f0b0c2222d65d5cf31e500255b8d72279ae356d9597f7f513335aaf506dfd960` (unchanged)
- `compose.yaml` — `312ce03f36442a2afafe4c744e27acd0df90c54adc7798262ed3ee20a5bfddab` (unchanged)
- `config/responder/responder.json` — `8d4cc6752b5abe4dd72e538c8b6b544635ab2614cd29becd6b1e4a9173e22e1f` (unchanged)

## Conclusion

The production cleanup removed exactly the approved historical tooling, retained supported operational tooling, preserved the production database/Files/responder configuration fingerprints, and left the Diaries application healthy.
