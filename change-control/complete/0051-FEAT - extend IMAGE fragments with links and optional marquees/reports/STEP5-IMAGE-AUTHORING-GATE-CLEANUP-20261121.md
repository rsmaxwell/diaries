# 0051-FEAT — Step 5 permanent IMAGE authoring-gate cleanup

Status: **prepared; not applied/deployed/accepted** (21 November 2026).

## Scope

Retire both rollout-only responder JSON properties `imageFragmentWritesEnabled` and
`imageFragmentExtensionsWritesEnabled`, the Java gate policy classes and checks,
corresponding Playbooks variables/validation/templates, and gate-specific tests.
Normal IMAGE authoring, image-reference mutations, validated links, and same-Page
Marquee attach/edit/remove remain available to authorised Editors. Keep role-based
security, lock/version requirements, URL constraints, Image reference integrity,
PostgreSQL transactions and MQTT retained-topic consistency unchanged.

## Source and packaging

Source baseline: `diaries-sources-20261121-111041.zip` and
`playbook-sources-20261121-111343.zip` (user-uploaded snapshots). There is no Git
metadata inside these source bundles to verify actual checkout branches and dirt;
verify Git status and submodule revisions in each authoritative working copy before
applying the packages. Keep the Diaries and Playbooks packages separate.

The Diaries package contains a deletion manifest for the two retired Java policy
classes and the renamed test source; remove those files **after** overlaying the
package. It does not touch persisted data, NAS files or production Docker state.

## Startup and deployment sequencing

- The cleaned-up Config class uses strict JSON mapping: remove both retired keys
  from local developer `responder.json` and `responder.docker.json` before starting
  the rebuilt responder. Use `tools/remove-retired-image-authoring-config.py`
  with `--check` and then `--apply`; private backups stay beside the JSON files.
- Build and test the responder with the updated source; publish a new responder
  image through the existing Jenkins pipeline. Do not change the client/web images.
- Prepare the Playbooks role cleanup and update `diaries_responder_image_tag`
  to the actual **published** new tag; check the private inventory for overriding
  gate variables or responder image tag values. Deploy the new responder image
  **and** gate-free `config/responder/responder.json` template in one Ansible run.
- The older responder defaults missing keys to disabled writes, while the new
  responder rejects obsolete keys. **Do not deploy template-only or image-only.**
- Verify five production health checks, effective responder config keys absent,
  IMAGE create, image SET/CLEAR, link SET/CLEAR, Marquee attach/move/remove,
  retained publication/replay, legacy MARQUEE behaviour, and logs.
- This maintenance does **not** reverse the 0051 rollback compatibility boundary:
  no pre-0051 writer/reader build may be used against extension-format data.

## Evidence and acceptance

Static checks/targeted configuration tests are supplied. Actual Gradle tests,
Jenkins build, local published-smoke and production verification must be performed
and recorded before Step 5 is CLOSED. 0028 migration, 0029 cleanup and 0052
map replacement are out of scope. Keep 0051 under `in-progress` pending formal
feature closure approval.

## Preparation checks performed in the packaging environment

- PASS — focused `verify-step5-retired-authoring-gates.py` for updated Java sources,
  active disposable reader harness, local environment example and Playbooks role.
- PASS — syntax check for both modified Node smoke-test scripts.
- PASS — PyYAML parsing of modified role defaults, main tasks and copy tasks.
- PASS — Jinja2 rendering and JSON parsing of production responder template,
  confirming no IMAGE authoring keys.
- PASS — disposable fixture check/apply/recheck of local JSON cleanup helper;
  only two named keys removed, all other configuration preserved.
- NOT RUN — Java Gradle compile/tests: this environment has no cached Gradle 9.6.1
  distribution and no internet route to download it (`UnknownHostException`).
- NOT RUN — complete Playbooks deployment-contract script: the uploaded Playbooks
  source bundle omitted the hidden `roles/diaries/templates/.env.j2` file
  required by that broader test. Run against the live Playbooks checkout on mango.
- NOT RUN — disposable Docker/MQTT, Jenkins publication and production operations.

Neither package has been applied to the user's authoritative working copies.
The above are packaging checks, not operational acceptance evidence.
