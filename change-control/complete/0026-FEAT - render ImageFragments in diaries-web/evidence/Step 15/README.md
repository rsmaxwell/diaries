# Step 15 — Deploy reader support with production authoring disabled

## Status

**COMPLETE — production deployment to Pluto verified.**

Step 15 was deployed to the production target `pluto` on 2026-10-01 and the preserved
post-deployment evidence verifies the required reader configuration, production safety
controls and reader smoke paths.

This supersedes the earlier close-out wording which recorded Step 15 only as an external
deployment handoff. The actual production deployment has now taken place and is evidenced
here.

## Release candidate deployed

```text
Git commit: e5aa410bcf83e73f83bf81cb5aee9571ccba2755
Target:     pluto

rsmaxwell/diaries-client:0.0.9-build-74
rsmaxwell/diaries-web:0.0.9-build-7
rsmaxwell/diaries-responder:0.0.9-build-82
```

The post-deployment capture confirms that these exact three application image tags are
running on Pluto and that the application services are healthy.

## Authoritative pre-deployment evidence

The authoritative pre-deployment capture is:

```text
step15-pre-pluto-20261001-133538
```

Its `result.json` records:

```text
host:                     pluto
mode:                     pre
failures:                 0
warnings:                 1
passed:                   true
imageFragmentWritesEnabled=false
content.filesPath:        <missing>
IMAGE Fragment rows:      0
MARQUEE Fragment rows:    2329
catalogued Images:        85
old-reader rollback safe: true
```

Every file listed in this capture's `SHA256SUMS.txt`, including `console.txt`, verifies
successfully.

The single warning was expected: before deployment the web configuration did not contain
an explicit `content.filesPath`.

## Authoritative post-deployment evidence

The production post-deployment capture is:

```text
step15-post-pluto-20261001-170216
```

Its `result.json` records:

```text
host:                     pluto
mode:                     post
failures:                 0
warnings:                 1
passed:                   true
imageFragmentWritesEnabled=false
content.filesPath:        files
IMAGE Fragment rows:      0
MARQUEE Fragment rows:    2329
catalogued Images:        85
old-reader rollback safe: true
```

Every file listed in the post-deployment capture's `SHA256SUMS.txt`, including
`console.txt`, verifies successfully.

The post-deployment verification also passed all required runtime checks:

- Docker Compose configuration is valid;
- the expected client, web and responder release-candidate images are running;
- all five production services are running and healthy;
- ImageFragment authoring remains explicitly disabled;
- `diaries-web` now has `content.filesPath=files`;
- the `diaries-web` MQTT ACL denies RPC, permits canonical Image reads and contains no
  write/readwrite rule;
- the Fragment/Image production schema is present;
- the reader readiness endpoint succeeds;
- the public reader root returns HTTP 200;
- the public reader `/about` route returns HTTP 200;
- an existing MARQUEE month/fragment reader smoke URL returns HTTP 200;
- a catalogued Image is reachable through the configured public Files route.

The one post-deployment warning states that the original pre-deployment working directory
was no longer present on Pluto, so the capture script could not compare hashes in place.
This is non-blocking because the authoritative pre-deployment evidence had already been
preserved in this evidence directory. `pre-post-comparison.txt` reconstructs that
comparison from the two preserved captures.

## Pre/post configuration comparison

The preserved runtime hashes show:

```text
compose.yaml              unchanged
responder.json            unchanged
mosquitto/aclfile.txt     unchanged
diaries-web.json          changed
```

The web configuration hash changed from:

```text
42c1c074e968ba30217ef8d02b04d24890b0a617426ae440abaae4191d8b1272
```

to:

```text
79b6e7fe8d1b3e42f98216f639ab9291353566aac1b3a5a371df36d5b2b35460
```

and the preserved JSON confirms that the material configuration change is the addition of:

```json
"filesPath": "files"
```

while the responder authoring gate and Mosquitto ACL remain unchanged and safe.

## Evidence-capture tooling

The exact scripts used to collect the authoritative Pluto evidence are preserved under
`scripts/` as part of this Step 15 evidence record:

```text
scripts/step15-capture-pre-deployment-pluto.sh
scripts/step15-capture-post-deployment-pluto.sh
```

The pre-deployment script produced the authoritative
`step15-pre-pluto-20261001-133538` capture. The post-deployment script produced the
authoritative `step15-post-pluto-20261001-170216` capture. Preserving these scripts
alongside their outputs makes the evidence self-contained and records exactly how the
production state was collected and verified. Both scripts are covered by the Step 15
top-level `SHA256SUMS.txt`.

## Superseded first pre-deployment capture

`step15-pre-pluto-20261001-132408` is retained only as historical evidence. Its first
version of the capture script calculated the checksum for `console.txt` before the
transcript had finished writing. It was repeated with corrected capture logic;
`step15-pre-pluto-20261001-133538` is the authoritative pre-deployment run.

## Close-out decision

Step 15 is **complete**. The evidence now demonstrates both sides of the production
change:

- a clean, rollback-safe pre-deployment state;
- the exact release candidate deployed to Pluto;
- production ImageFragment authoring disabled before and after deployment;
- reader-only MQTT access preserved;
- the required Files route configuration introduced;
- production schema readiness retained;
- core reader, MARQUEE and catalogued-Image smoke checks passing after deployment.

No remaining Step 15 production-deployment action is identified by this evidence.
