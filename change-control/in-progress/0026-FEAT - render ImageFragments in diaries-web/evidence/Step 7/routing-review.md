# Step 7 runtime routing review

Reviewed 2026-09-29 against the current Diaries bundle plus `playbook-sources-20260928-155031.zip`.

| Mode | Server-side responder base | Browser-visible responder base | Files route | Observation |
| --- | --- | --- | --- | --- |
| development-infrastructure / directly run web | normally local responder (`http://localhost:8081`) | must be whichever route the browser can actually reach; direct local use normally needs `http://localhost:8081`, while a proxy may use `/diaries-responder` | `files` by default | Do not replace the public base with Docker/internal DNS. The committed example is a template and must be adjusted to the actual browser route. |
| local-docker-build | `http://diaries-responder:8081` | `http://localhost:8081` in `diaries-web.docker.json` | explicit `files` after Step 7 | Responder port is published to the host; browser URL remains host-visible while server-side URL remains service DNS. |
| local-published-smoke | `http://diaries-responder:8081` | `http://localhost:8081` in the same Docker JSON | explicit `files` after Step 7 | Same routing contract as local-docker-build; only image provenance differs. |
| production shared frontend | `http://diaries-responder:8081` | `https://{{ diaries_hostname }}/diaries-responder` | currently omitted in Ansible JSON, therefore Step-7 default `files` | Shared Nginx rewrites `/diaries-responder/<rest>` to responder `/<rest>`, so catalogue URLs become `/diaries-responder/files/<relativePath>`. |
| production standalone frontend | `http://diaries-responder:8081` | same Ansible public responder base | currently omitted in Ansible JSON, therefore Step-7 default `files` | Standalone Nginx has `/diaries-responder/` proxying with trailing-slash semantics, so the same `/diaries-responder/files/<relativePath>` browser route is valid. Its current location file does not expose a `/diaries-web` route; that pre-existing deployment concern belongs to the later production deployment review rather than this URL-builder step. |

## Strict-decoder rollout order

The production Ansible `diaries-web.json.j2` currently has only `responderBaseUrl`, `publicResponderBaseUrl` and `diariesPath`. This Step-7 implementation intentionally remains compatible with that generated file by defaulting an absent `filesPath` to `files`.

Because older `diaries-web` binaries use strict JSON decoding, the safe production order is:

1. install/deploy a binary that understands/defaults `filesPath`;
2. verify it with the existing JSON which omits the property;
3. only then, as part of the coordinated deployment step, add explicit `"filesPath": "files"` (or another reviewed route) to the Ansible template and redeploy/reload configuration.

This prevents a configuration-first rollout from making an older reader fail at startup.
