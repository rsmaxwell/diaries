# 0032 Step 7 close-out — Add permanent anti-accumulation guards and feature-close-out guidance

## Status

**COMPLETE — 2026-10-03**

## Objective

Prevent a recurrence of the completed-feature tooling accumulation that required 0032, without turning historical feature/step names into a simplistic global ban.

## Implemented guard model

### Windows / Diaries

Added the permanent source guard:

```text
scripts/windows/validation/verify-live-script-policy.py
```

It combines:

- a small explicit allow-list of supported `scripts/windows` top-level areas;
- detection of feature/step-shaped helper names such as `NNNN-step*`, `verify-NNNN-*`, `stepN-*` and `migrationNNNN*`; and
- an exact-path exception map for a deliberately classified permanent tool whose name legitimately looks historical.

The existing empty `scripts/windows/remote-deployment/` directory is explicitly classified as a supported top-level area; it was not removed by this step.

The guard includes non-destructive synthetic self-tests proving that an accumulated feature directory, feature-numbered validator and step-numbered helper are rejected, while an exact explicitly classified exception is allowed.

`verify-dataset-pair-guard.py` now runs the live-script guard, so the recurrence check is part of an established normal local safety-regression entry point rather than an isolated one-off check.

### Production / Playbooks

Strengthened:

```text
roles/diaries/tests/verify-production-deployment-contract.py
```

The permanent production regression retains the exact supported synchronized script set and now also:

- rejects unclassified feature/step-shaped production helper names;
- provides an explicit exception mechanism for a genuinely permanent historical-looking command;
- contains a synthetic `step99-*` case proving the recurrence policy would detect the same class of accumulation; and
- verifies that production operator documentation contains the explicit deploy/remove lifecycle for temporary feature helpers.

The original Step 5/6 evidence remains the historical record of the explicit eight-file production cleanup. A same-day Step 7 refinement now replaces that ever-growing one-off removal model for future deployments: the project-root synchronize task excludes `scripts/`, and a dedicated managed-script synchronize task targets only `{{ diaries_project_dir }}/scripts/` with `--delete` and `--delete-excluded`. The nine permanent templated scripts are protected during the static sync and rendered immediately afterwards. This gives production a narrowly scoped anti-accumulation safety net without applying deletion semantics to the wider project tree.

The obsolete-script `state: absent` loops are therefore removed from current Playbooks source. This refinement does not itself deploy anything to `pluto`; the next normal Diaries copy deployment will enforce the managed scripts directory.

## Permanent close-out guidance

Updated the reusable Diaries change-control guidance so future close-out requires every feature-introduced script to be classified as:

```text
permanent operational/admin tooling
permanent regression/safety tooling
historical feature tooling
```

Historical tooling must be archived/removed from live script directories and deployed copies must also be removed and verified where source deletion alone is insufficient.

Production documentation now states that a temporary feature-only production helper must be explicitly deployed for the feature and explicitly removed during feature close-out instead of being left indefinitely in the always-synchronized production tree.

## Verification

`GUARD-TESTS.txt` records successful execution of:

- the new Windows guard with all synthetic negative/exception cases;
- the normal `verify-dataset-pair-guard.py` entry point with the new guard integrated;
- the permanent production deployment-contract regression with its synthetic recurrence case;
- the remaining portable Windows storage/configuration regressions;
- the other two permanent Playbooks production regressions;
- Python compilation of all Step 7 Python sources;
- the original stored Playbooks Step 7 patch applying cleanly to the uploaded Step 6 baseline;
- the same-day managed-scripts refinement regression, including YAML parsing of `copy.yaml`;
- an actual rsync smoke test proving `--delete --delete-excluded` removes stale files/directories while `protect` rules preserve templated permanent scripts; and
- the incremental managed-scripts patch applying cleanly to the uploaded Playbooks source baseline.

Final refinement result:

```text
PASS: managed production scripts refinement validated.
```

## Data and deployment safety

Step 7 is source, regression and documentation work only. It does not restore or mutate PostgreSQL, change schema, modify mutable Files content, publish/delete retained MQTT state, restart Docker services, or deploy to `pluto`. The managed-directory refinement changes what a future normal `--tags copy` deployment will do under the production `scripts/` directory: unmanaged entries will be removed there, and nowhere else by this deletion policy.

## Completion decision

The Step 7 completion rule is satisfied: the accumulation pattern that caused 0032 is detectable in both the Windows and production live tooling source trees, the Windows guard participates in a normal permanent regression entry point, future feature close-out guidance explicitly requires classification/archive/removal, and the production scripts deployment is now self-cleaning within a deliberately narrow managed-directory boundary.

**Step 7 is closed.**

## Next step

Proceed to **Step 8 — Run final regression, compare before/after inventories and close 0032**.
