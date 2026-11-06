# 0040-FEAT — Step 12 legacy journal transition; completed candidate revision

**Revised:** 6 November 2026. **Operational execution:** NOT PERFORMED. **Status:** Step 12 OPEN.

## 6 November evidence: first read-only production audits

Both receiver/source audits passed. The agreed parent `20261101-140039Z` was confirmed read-only on mars and backup, with matching source UUID / received UUID, and both new simplified records absent. Legacy journal `.agreed-parent-transfer-pending.json` is root-owned `0600`, sha256 `e11483fe05c482894c2db6fc15ffa63164f6b9c3da831508e0a2990123b9f3f2`, last modified `2026-11-01T19:39:39.159265+00:00`. It describes parent `20261030-030033Z` and candidate `20261030-170009Z`. The candidate is already a read-only received Btrfs subvolume; a legacy receipt exists, and no nonce-bound stage or sidecar exists. No other legacy marker was found. The first audit did **not** validate the receipt content.

The first-version archive would correctly refuse this case; it was deliberately designed only for an absent candidate/receipt. The revised feature-local utility instead permits this *historically completed* candidate case with explicit `--allow-completed-candidate` and a pinned receipt SHA, after read-only receipt validation against legacy accepted-receipt fields and exact journal parent lineage. It still refuses an incomplete or mismatched candidate, active staging, other legacy marker, changed journal or receipt, or concurrent receiver lock.

## Review and local verification

The revised tool matches the legacy receiver's accepted receipt contract in the uploaded Playbooks bundle, and independently verifies the Btrfs read-only received UUID. It does not reconstruct/complete the old transaction. Both legacy data and receipt remain in place; **only the journal is moved** into a root-only archive with hash readback. No permanent Playbooks role/code is changed.

17 isolated fixture regression tests passed in the current local environment, including the normal absent-candidate path and positive/negative completed-candidate paths. No production actions or other previously accepted end-to-end tests were repeated during preparation. Latest source bundle's simplified executable hash equals accepted install-only SHA `9be64295a6b6807df0fcd33d924b7a6549959f2a03dcab2953dcf0ac77fa6297`.

## Remaining operational gates

1. Apply updated ZIP to authoritative Windows Diaries repository.
2. Rerun revised **receiver-only** read-only audit to validate the published candidate's receipt and capture its digest. Reuse accepted B identity evidence.
3. Check noninteractive sender-to-receiver SSH/sudo, receiver prune disablement and installed executable hashes; stop source service/timer for controlled cutover.
4. If validation passes, guarded archive of journal only, preserving the candidate and receipt.
5. Bootstrap simplified agreed parent B and read back both records; run one manual sender cycle and reconcile parent/prior identities.
6. Preview and activate Playbooks opt-in without changing 03:30 UTC scheduling; receiver pruning remains disabled pending independent acceptance.

Never mark Step 12 CLOSED until full operational acceptance evidence is recorded. See `tools/README-STEP12-LEGACY-JOURNAL-TRANSITION.md` for exact host/terminal commands and rollback.
