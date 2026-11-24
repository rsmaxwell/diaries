# 0028-FEAT — Step 2 Reader HTTP connection refusal and isolated gateway repair

Date: 2026-11-23. Status: **PATCH PREPARED; live retry pending**.

## Observed evidence

The 19:55 MQTT rehearsal generated private evidence at
`evidence/Step 2/private/20261123T195519Z-mqtt-reader-replay`.
It validated 71/71 Fragment retained topics and all 22 retained Marquee topics.
The actual Reader started Javalin on container port 8082, connected to the isolated broker,
and published projection generation 1 (2,331 Fragments, 2,270 Marquees, 85 Images).
However, both Edge and the host curl readiness check received connection refusal on
`127.0.0.1:58082`. This is not evidence of failed MQTT replay.

## Root cause and correction

The runner started responder and Reader on a Docker **internal-only** bridge while
requesting `-p 127.0.0.1:58081/58082` bindings. Docker Engine 29 can accept those
options without activating the published host ports because internal-only
networks have no external default gateway. The Reader's `/health/ready` endpoint
is implemented correctly in `diaries-web`.

A small **labelled nginx gateway** is now the *only* dual-network container:
- Original `diaries-0028-replay-net` remains `--internal`, containing database,
  broker, responder and Reader. None of those services joins the new frontend.
- New `diaries-0028-replay-http-front` is a separate standard bridge used **only**
  by the nginx proxy. Its only host bindings are `127.0.0.1:58081:8081` and
  `127.0.0.1:58082:8082`.
- The nginx container proxies HTTP traffic back to the existing responder and Reader
  on the internal network; the broker still has no host MQTT port.
- The proxy can access the Docker frontend, but neither the application containers
  nor the isolated database acquires an external network route.

## Execution on Windows PC, Cygwin

Apply the ZIP in Beyond Compare 4, then execute from the authoritative Diaries
parent checkout:

```bash
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
bash 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tools/rehearse-0028-step2-mqtt-reader.sh' \
  --resume-http 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/evidence/Step 2/private/20261123T195519Z-mqtt-reader-replay'
```

This command revalidates the captured retained MQTT messages, checks the
existing labelled containers and migration journal, starts or reuses only
its own labelled proxy, waits for Reader readiness, checks representative
routes and image URLs, and verifies the Marquee/journal fingerprints.
It does **not** rebuild images, restore or change the database, restart MQTT,
or repeat the 71 conversions. It records successful `RESULT.txt` only if all
checks pass, while preserving private logs on failure.

The existing cleanup command now includes the proxy and frontend bridge,
with label checks, while retaining the restored database and evidence.

Remaining gates: isolated page scan and Editor GUI acceptance; Step 1/2 owner
acceptance; separate explicit production migration approval. **No production
apply, image publication or deployment is authorised.**
