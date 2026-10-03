# 0032 Step 7 documentation changes

## Purpose

Make the 0032 tooling-cleanup policy permanent so later features do not leave migration, evidence-capture or step-specific verification helpers in normal live script directories.

## Diaries change-control guidance

Updated `change-control/README.md` so the reusable change template and completion workflow now require every script introduced by a change to be classified as one of:

```text
permanent operational/admin tooling
permanent regression/safety tooling
historical feature tooling
```

The permanent close-out rule requires historical feature tooling to be archived/removed from live script directories and, where applicable, requires evidence that deployed copies were also removed.

The guidance now states the production lifecycle explicitly:

```text
temporary feature-only production helper
    -> explicitly deploy for the feature
    -> explicitly remove during feature close-out
    -> verify deployed absence when source removal is insufficient
```

Temporary production helpers should not be left indefinitely in an always-synchronized production tree.

## Windows operating and validation guidance

Updated:

```text
scripts/windows/README.md
scripts/windows/validation/README.md
```

The documentation now distinguishes permanent live tooling from historical feature tooling, documents the recurrence guard, explains the exact-path exception mechanism for a deliberately permanent historical-looking name, and records that the new guard is executed by the normal `verify-dataset-pair-guard.py` regression path.

## Playbooks production guidance

Updated:

```text
roles/diaries/README.md
roles/diaries/files/sync/scripts/README.md
```

The production synchronized `scripts/` source is documented as a small permanent allow-list. A temporary feature-only helper must be explicitly deployed and explicitly removed rather than silently becoming part of the permanent synchronized surface.

A same-day refinement makes the deployed production `scripts/` directory a dedicated managed tree. The wider project-root synchronization excludes `scripts/`; a separate scripts synchronization uses `--delete` and `--delete-excluded`, protects the known permanent templated scripts, and removes any other unmanaged destination entry. This makes forgotten deployed feature helpers self-cleaning on the next normal copy deployment while preserving the safety rule that deletion must never be applied to the whole Diaries project tree.

`roles/diaries/tests/verify-production-deployment-contract.py` verifies the documented lifecycle, the separate synchronization boundary, the two delete options, the protected template set, and the continued absence of project-root `--delete`.

## Guard policy notes

The Windows guard explicitly recognizes the existing empty `scripts/windows/remote-deployment/` directory as a supported top-level area; Step 7 does not remove or repurpose it.

Neither documentation changes nor the source guards modify PostgreSQL, mutable Files bytes, MQTT retained state, Docker services or deployed production files.
