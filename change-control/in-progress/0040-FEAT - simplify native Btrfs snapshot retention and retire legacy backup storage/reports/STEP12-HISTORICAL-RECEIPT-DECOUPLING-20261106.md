# 0040-FEAT Step 12 — historical receipt decoupling for controlled cutover

Date: 6 November 2026. Status: **PREPARED, NOT DEPLOYED**. Step 12 remains OPEN.

## Observed failure and rationale

Windows preflight on 6 November at 15:34 UTC exited 1 during receiver audit with `Completed candidate receipt source_filesystem_uuid mismatch`. Source Btrfs snapshot `20261101-140039Z` (UUID `69ef9a57-50ff-9a4e-92ed-8f10560ab1f2`) was independently read-only on mars and received with matching UUID on backup in the earlier accepted audits. The legacy pending journal SHA-256 is `e11483fe05c482894c2db6fc15ffa63164f6b9c3da831508e0a2990123b9f3f2`. Historical candidate `20261030-170009Z` was found as a read-only received Btrfs subvolume; a private staging object and sidecar were absent.

The historical receipt's filesystem metadata **does not pass the old receiver's acceptance contract**; its actual source-filesystem value and reason for divergence are not established by the preflight log. Do not recategorise this receipt as valid. The old code creates receipts as SSH user `richard` (with private 0600 permissions); a root-only ownership requirement would falsely reject genuine legacy receipts.

The simplified replication bootstrap and subsequent transfer do not consume any historical receipt. Therefore requiring this obsolete, inconsistent artifact to meet the old protocol confuses two separate questions: whether the historical transfer can be accepted (no evidence it can), and whether a **separate newer common Btrfs snapshot** is safe to adopt for new replication (established by independent Btrfs checks).

## One coherent change

1. Treat the historical candidate receipt as opaque evidence. Require a safe 0600 regular file owned by root or the old SSH receiver user, one hardlink, bounded size and an exact SHA-256 pin; retain its content unchanged. Log any source filesystem mismatch as historical, not a new-parent validation failure. No receipt metadata is trusted for the new protocol.
2. Independently verify the journal parent and candidate actual received UUIDs and read-only flags, plus the exact newer common-parent received UUID. Refuse if an associated private stage, sidecar, additional legacy marker or changed journal exists.
3. Preserve all existing no-snapshot-deletion, locked journal-only archive, fail-closed execute, timer stop, receiver pruning disabled and initial-parent bootstrapping protections.
4. Update the controlled-cutover runbook to seek `Candidate Btrfs identity: VERIFIED` rather than falsely claiming the old receipt was accepted.

This does not perform reconciliation of the old transfer, rewrite a historical receipt, prune received snapshots or relax the permanent legacy receiver. The only permitted cutover mutation to legacy history remains the exact pending-journal rename after the preflight and locked guards succeed.

## Local verification and next acceptance gate

- Fixture tests: 24 PASS, including inconsistent source filesystem, false success, wrong received receipt UUID, malformed receipt preservation, changed receipt hash, wrong actual Btrfs candidate/parent UUID, wrong new common-parent UUID, missing receipt/candidate, symlink, invalid mode, and nonce stage/secondary-marker refusals.
- `python3 -m py_compile` of migration script: PASS.
- `bash -n` of controlled cutover: PASS.
- No real SSH, Btrfs, systemd or Ansible execution was performed for this package.

Apply only to the authoritative Windows Diaries repo using Beyond Compare 4. Run the feature-local `step12-controlled-cutover.sh preflight`, and inspect PASS plus its full log. Only after the complete preflight passes may `execute` be invoked. After successful manual cycle, use separate Playbooks preview/activation and state readback; Step 12 remains OPEN until acceptance.
