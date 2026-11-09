# Step 12.3 — Repeat-cycle acknowledgement implementation (2026-11-01)

Status: IMPLEMENTED IN CHANGE PACKAGE; NOT DEPLOYED; STEP OPEN.

Previous live A->B recovered and independently verified; sender and receiver both established B (20261030-170009Z) with previous A (20261030-030033Z). Existing native backup timer active. A, B and newer native 20261101-140039Z verified readonly on both; received UUIDs match.

Source-level implementation adds explicit manual sender --acknowledge-previous and fixed receiver --acknowledge-previous/--previous-readback. Receiver-first ordering; sender holds existing native push and manager locks; receiver holds existing manager and writer locks. Sender requires source A/B identities, committed receiver receipt, exact receiver promoted state or independently confirmed already-cleared receiver state; verifies receiver durable clear before writing source state. Receiver independently verifies committed receipt before clearing previous. No operation releases/deletes any Btrfs snapshot, alters native pin registry, timer, or recovery holds.

Offline tests added: 4 sender recovery/negative checks, 4 receiver idempotence/negative checks; 8/8 PASS in source working copy. Existing sender workflow and runtime manifest suites PASS (on uploaded baseline). Full consolidated mango and integration tests still pending. Source baseline is the uploaded 2026-11-01 19:13 Playbooks bundle. The later sender-promotion-runtime correction was NOT included in this ZIP and must be preserved on mango.

Deployment gate: confirm mango Git status, preserve uncommitted work, apply Playbooks ZIP with Beyond Compare, run new and existing regressions, --check and standard Ansible deployment. Test installed source and receiver CLI --help and source/receiver states, then invoke sender --acknowledge-previous once, review result and both durable states. Do not invoke until current native protections and runtime compatibility are reviewed. No snapshot transfer is required for this acknowledgement.

Acceptance target: both machines established B; pending null; previous null; independent Btrfs readonly/received UUID identity; native checkpoint and original recovery holds preserved; native timer active. A remains protected by independent holds, if any, and no automatic release is authorized. Next-candidate preparation is separate and untested.
