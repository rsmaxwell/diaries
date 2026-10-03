# 0031-FEAT — Step 14 close-out

**Decision:** COMPLETE — 2026-10-03

Step 14 — **Deploy the explicit production configuration non-destructively** — is closed.

The production configuration is now explicit and active while retaining the
same intended production database/Files pairing. The production broker is
running the retained-snapshot flow-control policy carried forward from Step 13,
and the post-deployment controls prove that the deployment did not alter the
production Image catalogue, production mutable Files dataset, or independent
non-production Files roots.

## Production configuration deployed

The production Diaries deployment retains the explicit mutable Files selector:

```text
DIARIES_FILES_DIR=files
```

with the responder-facing mount remaining at stable `/data/files` and the NAS
subpath remaining:

```text
nancy-and-ronald-maxwell/documents/sea-captains-chest/diaries-content/files
```

The production Mosquitto flow-control policy is now:

```text
max_inflight_messages 20
max_queued_messages 0
```

The second Ansible copy/validation run confirmed both the explicit Files
selector/mount contract and those broker values before activation.

`max_queued_messages 0` remains the interim retained-snapshot correctness
safeguard identified in Step 13; the later bounded-snapshot design follow-up is
unchanged by this close-out.

## Preflight control

The authoritative preflight is:

```text
/home/richard/projects/diaries/data/0031-step14/preflight-20261003-090612
```

It reported:

```text
PASS: Step 14 production preflight is clean.
Production responder remains stopped for the normal Ansible deployment.
```

This established the frozen production control immediately before service
activation and confirmed that the Step 13 responder write freeze was still in
force.

## Deployment execution and activation

The first `--tags copy` run synchronised the Step 14 managed production files,
including:

```text
config/mosquitto/mosquitto.conf
scripts/README.md
scripts/step14-production-deployment.sh
```

That copy happened before the preflight, but the responder remained stopped, so
no responder writes were enabled by the file synchronisation itself.

After preflight, the normal Diaries `--tags copy` wrapper was run again. It was
fully idempotent:

```text
pluto : ok=22 changed=0 unreachable=0 failed=0 skipped=5 rescued=0 ignored=0
```

and explicitly validated:

```text
DIARIES_FILES_DIR / mutable Files mount: PASS
max_inflight_messages 20: PASS
max_queued_messages 0: PASS
```

Because the second run had no changes, no Ansible restart handler fired. An
attempted ad-hoc Ansible systemd restart then failed before execution because no
vault secret was supplied. That attempt made no production change.

Activation was therefore performed locally on `pluto` using the installed
systemd unit:

```text
sudo systemctl restart diaries-compose.service
```

The unit completed successfully through the normal `start.sh` path. Shared
Nginx configuration validation passed, the Diaries route was activated, and all
five application containers were healthy:

```text
diaries-client      healthy
diaries-mosquitto   healthy
diaries-postgres    healthy
diaries-responder   healthy
diaries-web         healthy
```

## Postflight proof

The authoritative postflight is:

```text
/home/richard/projects/diaries/data/0031-step14/postflight-20261003-091828
```

The run first proved responder retained-tree startup synchronisation, then
stopped only `diaries-responder` for deterministic read-only verification.

It reran the production Step 12 reconciliation against the Step 9 semantic
baseline using:

```text
Files selector: files
NAS subpath: nancy-and-ronald-maxwell/documents/sea-captains-chest/diaries-content/files
```

and generated:

```text
/home/richard/projects/diaries/data/0031-step12/production-20261003-091922
```

The reconciliation reported:

```text
Step 12 comparison PASS: production
PASS: Step 12 production reconciliation matches the Step 9 semantic baseline.
```

After all deterministic controls passed, the responder was restarted, returned
healthy, and again completed retained-tree startup synchronisation successfully.
The Step 14 helper then reported:

```text
PASS: Step 14 production deployment is healthy and non-destructive.
```

## Non-destructive conclusion

Step 14 is complete because the preserved evidence proves that:

- the production responder remained stopped through the frozen preflight;
- the explicit production Files selector remained `files`;
- the responder-facing mutable mount remained stable at `/data/files`;
- no local override file was introduced into production deployment;
- the production broker loaded `max_inflight_messages 20` and `max_queued_messages 0`;
- the production stack restarted successfully through its installed systemd unit;
- all application services were healthy after activation;
- responder retained-tree synchronisation completed successfully;
- the postflight durable-state comparisons passed;
- independent non-production Files roots remained unchanged;
- the existing production `/files` route proof passed inside the postflight;
- the Step 12 production reconciliation still matched the Step 9 semantic baseline; and
- the responder was restarted and healthy after deterministic verification.

No production Image upload, delete, replacement, direct SQL mutation, or manual
Files mutation was required to obtain the proof.

## Preserved evidence

Exact console transcripts supplied from the deployment session are retained
under:

```text
evidence/Step 14/runtime/console/
```

with an index in `runtime/README.md`.

The timestamped helper-generated directories remain authoritative on `pluto` at
the paths recorded in `LATEST-PREFLIGHT.txt`, `LATEST-POSTFLIGHT.txt`, and
`LATEST-RECONCILIATION.txt`. Their bytes were not supplied in the source bundle,
so this close-out overlay records their exact identities rather than fabricating
copies.

## Handoff

Step 14 no longer blocks normal production operation. The production responder
has been restarted successfully and the explicit production storage
configuration has been proven non-destructive.

The remaining 0031 work, if any, is determined by the other implementation-step
statuses; this close-out changes only Step 14 from runtime-pending to complete.
