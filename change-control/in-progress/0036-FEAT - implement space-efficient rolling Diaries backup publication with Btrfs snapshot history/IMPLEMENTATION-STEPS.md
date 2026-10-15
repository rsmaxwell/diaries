# 0036-FEAT — IMPLEMENTATION-STEPS

**Status: NOT STARTED.** Begin only after the final 0034/0035 operational evidence and feature closure is accepted.

| Step | Work | Evidence / completion gate |
|---|---|---|
| 1 | Freeze current 0033–0035 contracts and live `pluto`, `mars`, `backup` storage inventory | Git revisions, exact paths, Btrfs subvolumes, existing generations, receipts, timers, usable recovery checkpoint and measured baseline; no changes |
| 2 | Decide stable-source and atomic publication layout on ext4 | Document symlink/pointer commit, fsync/durability, bounded staging, rollback retention, locking, source content immutability, file identity and crash cases |
| 3 | Decide Btrfs candidate/accepted-state and extent-sharing protocol on `mars` | Confirm actual `@data` snapshot/send boundaries; prove candidate COW/reflink strategy, atomic promotion, scoped deletion, verified marker and crash recovery with prototype |
| 4 | Define publication/pull compatibility and migration contract | Freeze schema-2 layout, backup IDs and manifest verification, history lookup, idempotent retries, rollback rejection, stable-path rsync/SSH permissions, source acknowledgement |
| 5 | Implement opt-in rolling publisher on `pluto` | Source-level regression: unchanged/changed/removed photo, coherent DB dump, manifest, locks, partial failure, hard-link safety if used, rollback and non-destructive default |
| 6 | Implement opt-in transactional verified rolling pull on `mars` | Source-level regression: unchanged extents, selective data transfer, independently verified candidate, pointer switch, idempotency, absent/conflicting IDs, delete protections |
| 7 | Adapt history/status/restore/discovery to snapshot-based versions | Regression across old timestamped generations, new current dataset, historical Btrfs snapshot and receiver; avoid 0035 history-verification bypass |
| 8 | Integrate 0035 snapshot management and 0034 native push unchanged in intent | Prove snapshot verified-state barriers, protected parent retention, incremental native send parent identity, off-site receipt and failed receive isolation |
| 9 | Disposable end-to-end storage-efficiency rehearsal | At least two unchanged-photo logical backups plus changed/add/delete case; quantify `btrfs filesystem du`/extent sharing, rsync byte counts, restore both historical points |
| 10 | Controlled non-destructive production shadow deployment | Install default OFF; back up configuration, leave schedules unchanged; independently verify old and new paths in shadow on `pluto` and `mars` |
| 11 | Authorised production cutover and recovery tests | Pin known-good checkpoint; freeze relevant timers; perform single full controlled rolling publication/pull, verify, re-enable schedules; failed-mid-transfer and rollback rehearsal; confirm offsite incremental receipt |
| 12 | Unattended acceptance, monitoring and cleanup approval | Observe at least two successive unattended cycles, unchanged-photo efficiency, valid snapshots and remote receive; prune old generations only after signed-off rollback window |
| 13 | Documentation, source/regression evidence and closure | Record exact deployed commits, before/after space and transfer data, operational commands, test evidence, unresolved limitations, sign-off; mark CLOSED |

## Safety gates applying to every implementation step

- No deletion of accepted backup, snapshots, held checkpoints, replication parents or rollback media without operator-authorised irreversible-action gate.
- All changes must retain schema-2 restore compatibility and distinct logical backup IDs.
- Partial or invalid input must not alter published/accepted current pointers.
- `mars` initiates the pull from `pluto` and native off-site push to `backup`; no inbound home networking introduced.
- No Docker image rebuild expected for backup-only scripts unless implementation later touches container code; determine build requirement at each step.
- Capture both positive and negative tests and preserve source-versus-live evidence distinctions.
