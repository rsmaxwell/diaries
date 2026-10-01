# Step 15 production deployment runbook — Pluto

This runbook applies the 0026 reader release candidate while keeping ImageFragment
authoring disabled.

## Release candidate

- Git commit: `e5aa410bcf83e73f83bf81cb5aee9571ccba2755`
- `rsmaxwell/diaries-client:0.0.9-build-74`
- `rsmaxwell/diaries-web:0.0.9-build-7`
- `rsmaxwell/diaries-responder:0.0.9-build-82`
- production target: `pluto`

The Playbooks source prepared for this deployment must generate:

```json
// config/responder/responder.json
"imageFragmentWritesEnabled": false
```

and:

```json
// config/web/diaries-web.json
"content": {
  "publicResponderBaseUrl": "https://pluto.rsmaxwell.co.uk/diaries-responder",
  "diariesPath": "diaries",
  "filesPath": "files"
}
```

The `diaries-web` Mosquitto ACL must remain reader-only, including:

```text
user diaries-web
topic deny diaries/rpc/#
topic read diaries/diaries/+
topic read diaries/pages/+
topic read diaries/fragments/+
topic read diaries/marquees/+
topic read diaries/images/+
```

## 1. Capture the pre-deployment rollback state

Copy `step15-production-evidence.sh` to Pluto, or pipe it over SSH, and run:

```bash
bash step15-production-evidence.sh pre
```

Keep the resulting evidence directory. It records the currently running image
references/IDs, relevant generated configuration checksums, database schema readiness,
IMAGE Fragment count and the disabled authoring gate. It does not record passwords or
other secret environment values.

If the reported IMAGE Fragment count is non-zero, an old reader which hides IMAGE
Fragments is **not** a safe rollback target. Preserve the old image identities as
forensic/rollback evidence, but plan a compatible forward fix or reader-compatible
rollback instead.

## 2. Apply the Playbooks change on the controller

Use the normal production workflow from the Playbooks repository:

```bash
cd ~/playbooks
./scripts/diaries.sh
```

Before accepting the run, inspect inventory/group/host overrides for the three image-tag
variables. Role defaults are intentionally low precedence, so a stale override can
otherwise defeat the release-candidate tags.

The role's normal `start.sh` path validates Compose, pulls configured images, starts with
`--wait`, then activates/reloads the shared Nginx route only after the Diaries services
are healthy.

## 3. Capture post-deployment evidence

On Pluto run:

```bash
bash step15-production-evidence.sh post
```

The post-deployment mode requires all three running image references to match the release
candidate, requires `imageFragmentWritesEnabled=false`, requires `content.filesPath=files`,
checks the read-only Image ACL, verifies the 0025 fragment/image schema, checks the web
readiness endpoint, and performs production HTTP smoke checks.

The HTTP smoke checks include:

- the deployed reader root;
- one existing MARQUEE Fragment month view when a suitable production row exists;
- one catalogued Image through the configured public Files route when an Image row exists.

No production IMAGE fixture is created by this script. The controlled mixed IMAGE/MARQUEE
proof remains the Step 13/14 evidence produced with the identical release-candidate web
artifact.

## 4. Preserve the evidence

Copy the pre- and post-deployment output directories beneath this Step 15 evidence
directory. Do not copy decrypted vault data, `.env`, full `docker inspect` output, or
configuration containing credentials.

For an actual production-deployment close-out, retain a passing post-deployment capture
against Pluto and the running artifact/configuration identities here.

This evidence directory now contains both the authoritative pre-deployment capture
`step15-pre-pluto-20261001-133538` and the passing post-deployment capture
`step15-post-pluto-20261001-170216`. Step 15 is therefore closed using the actual
production-deployment verification path. The earlier external-deployment-handoff close-out
wording is superseded by the preserved post-deployment evidence.
