# 0034 Step 4 — Design ratification

**Status: CLOSED — design/contract only, 2026-10-08.** No runtime script, Playbooks configuration, or deployed data changed by this step.

- `PUBLICATION-AND-REPLICATION-CONTRACT.md`: frozen stable relative name, chosen symlink+immutable-generation+shared-lock publication scheme, sender/receiver contract, migration and acceptance gates.
- `STEP-3-SUPERSESSION.md`: preserves successful original Step 3 evidence while documenting why source reflink work is retired.
- The actual live rsync paths, commands, identities and timing remain **unverified in the available source archive**; discovery is a mandatory prerequisite to production replication changes in Step 6. The proposed absolute published path requires deployment validation in Steps 5/8/9.

Next: Step 5 — implement and test the publisher on disposable ext4, including controlled concurrency and failure injection. Do not deploy 0035 snapshot timers yet.
