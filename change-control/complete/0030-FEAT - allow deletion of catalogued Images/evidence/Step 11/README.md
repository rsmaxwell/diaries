# 0030 Step 11 — Production deployment

Recorded 2026-09-27 from Richard's deployment report and pasted status output. Step 11 completed on 2026-09-27 based on the supplied deployment, controlled-deletion evidence and explicit backup/UI confirmations. This record does not claim independent SSH, registry or running-image digest verification.

## Deployment reported

Richard reports that all Diaries projects were checked into Git, the client and responder rebuilt, and the Diaries playbook run to deploy the following images to **pluto**.

Top-level Diaries Git commit: `a8e70962898f52ac5db8baaab2e951b2bb884c36` (user-reported production checkout).

| Component | Deployed image reported and shown by status | Docker Hub reference supplied |
| --- | --- | --- |
| Client | `rsmaxwell/diaries-client:0.0.9-build-72` | [0.0.9-build-72](https://hub.docker.com/repository/docker/rsmaxwell/diaries-client/tags/0.0.9-build-72/sha256-044e2edf1d78ce6f82b6eef3cf2771977a33c5b270dd8aee22c85a9bd317fa11) |
| Responder | `rsmaxwell/diaries-responder:0.0.9-build-80` | [0.0.9-build-80](https://hub.docker.com/repository/docker/rsmaxwell/diaries-responder/tags/0.0.9-build-80/sha256-16da0624becc9280bd2623232af5db3aa830a1bb24e299a9e8cc4dbd736519ef) |
| Web | `rsmaxwell/diaries-web:0.0.9-build-5` | [0.0.9-build-5](https://hub.docker.com/repository/docker/rsmaxwell/diaries-web/tags/0.0.9-build-5/sha256-d925b2c50fa19ebf4d22954e9829ac9b4f4dbdf2adcd2fd577262d7d35ba5820) |

SHA-256 identifiers supplied in those registry URLs (not independently matched to running container digests):

- Client: `044e2edf1d78ce6f82b6eef3cf2771977a33c5b270dd8aee22c85a9bd317fa11`
- Responder: `16da0624becc9280bd2623232af5db3aa830a1bb24e299a9e8cc4dbd736519ef`
- Web: `d925b2c50fa19ebf4d22954e9829ac9b4f4dbdf2adcd2fd577262d7d35ba5820`

## Observed in supplied status output

Command: `./status.sh` from `/home/richard/projects/diaries/scripts` as `richard@pluto`.

- Project directory: `/home/richard/projects/diaries`
- Compose file: `/home/richard/projects/diaries/compose.yaml`
- Environment file: `/home/richard/projects/diaries/.env`
- Frontend mode: `shared`
- Client, responder, web, Mosquitto and PostgreSQL: all shown up for 12 minutes and healthy.
- Shared network: `infrastructure_shared`
- Shared nginx: `infra-nginx`, shown up for 4 weeks.
- Route source: `/home/richard/projects/infrastructure/nginx/config/files/diaries.conf`
- Active route: `/home/richard/projects/infrastructure/nginx/config/conf.d/locations/diaries.conf` -> `../../files/diaries.conf`

See [status-user-supplied.txt](status-user-supplied.txt) for the transcribed terminal output. Relative times are preserved as reported; an exact capture/deployment timestamp was not supplied. Healthy container status establishes the reported deployment state, not successful image deletion across file/database/MQTT layers. Deployment ordering (responder before client) was not evidenced by this output.

## Pre-delete baseline recorded

Richard supplied the Image 84 baseline on 2026-09-27 before the controlled deletion: img2230.jpg at the image root, its database record and retained MQTT payload. These are preserved in [pre-delete-image-84](pre-delete-image-84/README.md), together with the query and original source location. The database and MQTT metadata agree. File bytes and backups have not been independently verified.

## Post-delete outcome recorded

Richard reports that Image 84's physical file, database record and MQTT topic are absent and the Files list refreshed correctly. The supplied console note records deleteImage returning 200 OK followed by listFiles returning 200 OK. See [post-delete-image-84](post-delete-image-84/README.md) for the production file location, request correlations and preserved console evidence.

## Step 11 completion

Deployment and the controlled deletion outcome have been recorded. Richard has now explicitly confirmed that Files-root backups were confirmed before deletion and that he saw and accepted the deletion dialog; see [his follow-up](post-delete-image-84/user-confirmation.md). Richard subsequently confirmed that the database backup was also confirmed before deletion. Step 11 is now complete on this evidence basis; no repeat deletion is needed. Step 12 close-out subsequently completed on 2026-09-27; feature 0030 is archived under complete. The previously noted lack of independent production inspection and deployment-order evidence remains a provenance limitation, not an assertion that those checks were performed by the assistant.
