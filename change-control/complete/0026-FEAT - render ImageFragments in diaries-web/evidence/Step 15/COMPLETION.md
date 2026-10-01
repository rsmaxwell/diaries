# Step 15 completion record

**Feature:** 0026-FEAT — render ImageFragments in diaries-web  
**Step:** 15 — Deploy reader support with production authoring disabled  
**Decision date:** 2026-10-01  
**Status:** COMPLETE — production deployment verified on Pluto

## Completion basis

The Step 15 release candidate was deployed to `pluto` and is backed by both preserved
pre-deployment and post-deployment evidence.

The authoritative pre-deployment capture is:

```text
step15-pre-pluto-20261001-133538
```

It passed with zero failures and one expected warning because `content.filesPath` was not
yet explicitly present. At that point ImageFragment authoring was already disabled, the
reader ACL was read-only, there were zero production IMAGE Fragment rows and old-reader
rollback was safe.

The authoritative post-deployment capture is:

```text
step15-post-pluto-20261001-170216
```

It passed with zero failures and one non-blocking warning. It verifies:

- the intended release-candidate client/web/responder images are running;
- all five production services are healthy;
- `imageFragmentWritesEnabled=false` remains in force;
- `content.filesPath=files` is deployed;
- the `diaries-web` ACL remains read-only and denies RPC;
- the production Fragment/Image schema remains present;
- there are still zero production IMAGE Fragment rows;
- reader readiness succeeds;
- public reader root and `/about` return HTTP 200;
- an existing MARQUEE reader path returns HTTP 200;
- a catalogued Image is reachable through the public Files route.

The post-capture warning only records that the earlier pre-deployment working directory
was no longer present on Pluto. Because both captures are preserved here, the pre/post
runtime hashes have been compared directly in `pre-post-comparison.txt`. The web config
changed as expected while Compose, responder configuration and Mosquitto ACL hashes
remained unchanged.

## Final decision

Step 15 is complete as an **actual verified production deployment**, superseding the
earlier provisional external-deployment-handoff close-out.
