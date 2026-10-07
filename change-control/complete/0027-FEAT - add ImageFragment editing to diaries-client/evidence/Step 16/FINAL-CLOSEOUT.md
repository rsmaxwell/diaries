# 0027-FEAT final close-out

0027 is complete as of 2026-10-07.

The Angular editor now treats IMAGE as a first-class Fragment authoring type alongside MARQUEE while retaining one common Page/date/sequence/lock/version model. Image identity uses persisted catalogue IDs; retained MQTT distributes Image metadata; HTTP/static Files routing serves image bytes. Ordinary Fragment edits preserve an existing Image relationship by omitting `imageId`, while explicit replace and clear operations use positive-ID and null mutations respectively.

Deletion boundaries are intentionally non-cascading: deleting an IMAGE Fragment does not delete its reusable Image, and deleting an Image remains blocked while referenced. The responder authoring gate remains the authoritative emergency/rollback control. After successful 0027 production verification, the shared Ansible role defaults it to enabled (`true`); setting it to `false` is the tested non-destructive authoring stop.

The final production lifecycle on `pluto` used client `0.0.9-build-76`, responder `0.0.9-build-84` and reader `0.0.9-build-8`. It proved disabled-gate behavior, deliberate enablement, create/edit/replace/clear/reattach, delete guard, restart/replay, cross-layer agreement and cleanup. The two rollout defects (catalogue-list timeout and missing production client Image-topic ACL) were corrected and reverified before closure.

Step 16 updates durable documentation, reconciles the Playbooks role to the completed-feature default (`true`) while retaining `false` as rollback, inventories final evidence and classifies feature tooling. No database migration, Files migration or new Docker image is required for this documentation/close-out step.
