# Step 08 — Formal feature close-out (21 October 2026)

**Decision: Step 08 CLOSED; 0038-FEAT CLOSED.** Acceptance is based on previously reviewed operator transcripts, not re-executed tests in this documentation package.

## Source provenance

| Repository | Committed revision | State | Evidence |
|---|---|---|---|
| Diaries | `e69e08b2ff100b7d2afcf8458e9cb9204bc6be5a` | main, clean, synchronized with origin/main | `note(20261021-073700).txt` |
| Playbooks | `fc8233da3464aa114d69a2e34bd8990f96daf281` | main, clean, synchronized with origin/main | `note(20261021-074040).txt` |

The Playbooks commit message was amended to `0038-FEAT - Step 8`, then pushed successfully with `--force-with-lease`. Former SHA `908509ec57e06f972b4412fae8f98b7a4f4edc1f` is superseded. The eventual Git commit containing this archival move will have a *newer* Diaries revision and should be recorded after committing; the revision above is the accepted pre-archive baseline.

## Accepted feature evidence

| Gate | Evidence / outcome |
|---|---|
| Steps 1–4 | Baseline, rollback design and SHA-256 matching, source safety, approved `--check --diff` target `backup` with `changed=5` |
| Step 5 | Real controlled deployment `changed=5 failed=0`; manager status repaired; 14 original received Btrfs snapshot IDs retained; three timers disabled/inactive |
| Step 6 | Installed Python programs valid; overnight increment `20261021-030006Z` receipt matches Btrfs Received UUID `c0ad8538-dc61-bc48-8922-6c37eaf1a902`, subvolume ID 55805, `readonly`, send/receive exit 0, 15 received snapshots |
| Step 7 | Source and installed negative tests passed; actual repeat `./scripts/remote-backup.sh --apply`: `ok=26 changed=0 failed=0` |
| Step 8 | Both Git revisions verified; rollback retention explicitly accepted; evidence indexed; remaining diagnostic deferred; archive move authorized |

Consult acceptance records in `evidence/Step 01/` through `evidence/Step 07/` for full scope and evidence references.

## Rollback and exclusions

The four root-owned copies at `/root/remote-backup-pre-reconcile/` on `backup` are retained deliberately for manual emergency recovery; no automatic expiry, deletion or restoration is authorized by this feature. Their Step 2 baseline SHA-256 identities remain the recorded recovery reference.

The optional `qgroups_status=unavailable;reason=unexpected_output` is a deferred non-blocking parsing diagnostic. No qgroup data-corruption finding is claimed. No new restore, native send, snapshot pruning/deletion, replication retention or scheduling modification, or local timer activation is part of this close-out.

## Archival / operator action

Archive the whole directory via `git mv` from `change-control/in-progress/` to `change-control/complete/`, then overlay the feature-local documentation edits in this delivery. Verify `git diff --check`, inspect renames, commit and push the archive update. The final archive-commit SHA is not known in this evidence and must not be fabricated. The closure decision is accepted; Git archival persistence follows the operator applying the package.
