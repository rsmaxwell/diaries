# 0032 Step 6 — Deploy the production cleanup non-destructively and verify `pluto`

## Status

**COMPLETE — 2026-10-03**

Step 5 has already made the Playbooks source authoritative. Step 6 applies that narrowly-scoped cleanup to `pluto` and proves that production remains healthy and that no durable application data/configuration contract was changed.

## Safety boundary

The Step 6 tooling does not contain database restore, SQL mutation, Image lifecycle, Files mutation or retained-MQTT cleanup commands.

The Playbooks deployment remains restricted to the existing `copy` tag. The source role removes only these eight explicit stale filenames:

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

The role continues to avoid unrestricted `rsync --delete`.

## Execution sequence

### 1. Fresh pre-deployment capture on `pluto`

Copy `scripts/capture-step6-pluto.sh` to a temporary location on `pluto` (for example `/tmp/capture-step6-pluto.sh`) rather than putting verification tooling back into the live Diaries `scripts/` directory.

Run:

```bash
chmod +x /tmp/capture-step6-pluto.sh
rm -rf /tmp/0032-step6
/tmp/capture-step6-pluto.sh pre
```

Copy these generated files back into this evidence directory:

```text
PLUTO-SCRIPTS-PRE.txt
PRODUCTION-CONFIG-PRE.txt
```

Do not deploy until that pre-capture succeeds.

### 2. Controlled deployment from `mango`

Copy `scripts/run-step6-deployment-on-mango.sh` to a temporary location on `mango`, then run:

```bash
chmod +x /tmp/run-step6-deployment-on-mango.sh
/tmp/run-step6-deployment-on-mango.sh /home/richard/playbooks
```

The wrapper:

1. refuses to run unless `scripts/diaries.sh` is restricted to `--tags copy`;
2. reruns all three permanent Step 5 production validators with `python3`;
3. invokes the normal `./scripts/diaries.sh` controlled deployment;
4. records `/tmp/0032-step6/PLAYBOOK-OUTPUT.txt` and an additional source-validation transcript.

Copy `PLAYBOOK-OUTPUT.txt` back into this evidence directory. `PLAYBOOK-SOURCE-VALIDATION.txt` may also be retained as supporting evidence.

### 3. Post-deployment capture and health check on `pluto`

Run the same temporary capture helper:

```bash
/tmp/capture-step6-pluto.sh post
```

Copy these generated files back into this evidence directory:

```text
PLUTO-SCRIPTS-POST.txt
PRODUCTION-CONFIG-POST.txt
PRODUCTION-STATUS.txt
```

The post capture executes normal `scripts/status.sh` and verifies that `diaries-db`, `diaries-mqtt`, `diaries-responder`, `diaries-client` and `diaries-web` are all `running` and `healthy`.

### 4. Generate the Step 6 comparison

From the Diaries checkout on Windows run:

```bat
"change-control\in-progress\0032-FEAT - clean up completed-feature verification tooling from live script directories\evidence\Step 6\scripts\verify-step6-evidence.bat"
```

That creates:

```text
DIFF.md
VERIFICATION-OUTPUT.txt
```

The verifier compares:

- Step 1 production baseline vs fresh Step 6 pre-deployment capture;
- pre-deployment vs post-deployment script names/hashes;
- the exact eight-name removal set;
- retained operational executable modes;
- deployed backup/restore/manifest hashes vs approved Step 5 source hashes;
- SHA-256 fingerprints for `.env`, `compose.yaml` and `config/responder/responder.json` before/after;
- non-secret database/Files selectors/contracts before/after;
- Ansible recap / deployment exit code;
- post-deployment service health.

## Required close-out evidence

The implementation-step-required files are:

```text
PLUTO-SCRIPTS-PRE.txt
PLAYBOOK-OUTPUT.txt
PLUTO-SCRIPTS-POST.txt
PRODUCTION-STATUS.txt
DIFF.md
```

Step 6 additionally captures:

```text
PRODUCTION-CONFIG-PRE.txt
PRODUCTION-CONFIG-POST.txt
VERIFICATION-OUTPUT.txt
PLAYBOOK-SOURCE-VALIDATION.txt   # optional supporting transcript
```

## Completion rule

Do not mark Step 6 complete until `verify-step6-evidence.py` reports:

```text
PASS: Step 6 production cleanup evidence verified.
```

and `DIFF.md` reports `PASS`.

## Close-out result

Step 6 was executed against the real production path on 2026-10-03 and is complete.

The accepted evidence proves:

- the fresh pre-deployment `pluto` inventory matched the Step 1 baseline by filename and SHA-256;
- the three permanent Playbooks validators passed immediately before deployment;
- deployment used the normal controlled Diaries path and finished with `failed=0`, `unreachable=0`, exit code `0`;
- exactly the eight approved obsolete helpers were removed;
- the post-deployment script inventory exactly matches the approved permanent production set;
- retained operational scripts remain executable and the five synchronized operational helpers match their approved Step 5 source hashes;
- production `.env`, `compose.yaml` and `config/responder/responder.json` fingerprints are unchanged;
- non-secret database/Files selectors and contract lines are unchanged; and
- `diaries-db`, `diaries-mqtt`, `diaries-responder`, `diaries-client` and `diaries-web` are all running and healthy.

The final verifier reported:

```text
PASS: Step 6 production cleanup evidence verified.
```

See `STEP-6-CLOSE-OUT.md` for the formal closure record.
