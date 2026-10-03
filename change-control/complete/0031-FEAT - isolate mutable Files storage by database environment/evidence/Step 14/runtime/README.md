# 0031-FEAT — Step 14 runtime evidence index

The console transcripts in `console/` are the exact evidence supplied from the
2026-10-03 production deployment and verification session. They are preserved
without editing.

## Preserved console transcripts

| Transcript | Purpose | Result |
| --- | --- | --- |
| `console/note(20261003-080223).txt` | Initial Ansible `--tags copy` synchronisation | Changed the production Mosquitto configuration, scripts README, and installed `step14-production-deployment.sh` |
| `console/note(20261003-080724).txt` | Step 14 production preflight on `pluto` | PASS; responder remained stopped; preflight evidence `preflight-20261003-090612` |
| `console/note(20261003-081135).txt` | Idempotent Ansible `--tags copy` validation run | PASS; `changed=0`; explicit Files selector/mount and broker queue policy validated |
| `console/note(20261003-081411).txt` | Attempted ad-hoc Ansible systemd restart | Did not run because no vault secret was supplied; no production state change |
| `console/note(20261003-081735).txt` | Local systemd restart and service status on `pluto` | PASS; systemd start script succeeded and all five Diaries containers were healthy |
| `console/note(20261003-082144).txt` | Step 14 production postflight | PASS; Step 12 reconciliation matched baseline; responder returned healthy; deployment declared healthy and non-destructive |

## Authoritative generated evidence locations

The Step 14 helpers generated richer timestamped evidence directly on `pluto`.
Those remote bytes were not part of the supplied source bundle, so this overlay
does not fabricate copies of them. Their authoritative locations are:

```text
/home/richard/projects/diaries/data/0031-step14/preflight-20261003-090612
/home/richard/projects/diaries/data/0031-step14/postflight-20261003-091828
/home/richard/projects/diaries/data/0031-step12/production-20261003-091922
```

The final postflight explicitly reports that the Step 12 production
reconciliation matches the Step 9 semantic baseline and that the Step 14
production deployment is healthy and non-destructive.

## Deployment-order note

The first Ansible copy run installed the Step 14 managed files before the
preflight was executed. The production responder was still stopped at preflight,
and the helper confirmed the frozen production controls were clean. The later
Ansible validation run was idempotent (`changed=0`), so no restart handler fired.
The production stack was therefore activated with:

```text
sudo systemctl restart diaries-compose.service
```

on `pluto`. The successful service-status transcript and the subsequent passing
postflight bracket the activation. The failed ad-hoc Ansible restart attempt is
retained only for audit completeness and made no change.
