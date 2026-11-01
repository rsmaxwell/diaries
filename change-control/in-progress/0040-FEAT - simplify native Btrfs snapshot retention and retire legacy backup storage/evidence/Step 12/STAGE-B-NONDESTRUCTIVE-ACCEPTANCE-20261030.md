# 0040-FEAT Step 12.3 — Stage B non-destructive operational acceptance

**Evidence date:** 2026-10-29–2026-10-30 UTC  
**Decision:** Non-destructive operational verification **PASS**. First receiver-only deletion **NOT TESTED**; unattended receiver pruning **NOT ENABLED**; overall Stage B operational closure **OPEN**.

## Evidence and observations

Evidence consists of operator command outputs supplied in the 0040-FEAT conversation. These observations should be archived with the original dated terminal logs where possible.

| Evidence | Command / observation | Result |
|---|---|---|
| 2026-10-29 20:20 | `btrfs filesystem show /media/usb`; `btrfs subvolume show .../20261029-030003Z` | Both successful, elapsed 0.00s and 0.01s; source UUID `3a2cc82d-a9ab-964f-af85-f073dd45f0a4`, readonly |
| 2026-10-29 20:21 | Nonblocking source manager-lock probe | PASS; 0.00s |
| 2026-10-29 20:23 | `btrfs-native-endpoint --role protect-prune-source --snapshot 20261029-030003Z` | PASS; 0.75s; source protection may update protection JSON |
| 2026-10-30 09:09 | `lsusb -t` after shutdown and moving drive from USB 2 to USB 3 port | USB mass storage attached at `5000M` using `usb-storage` |
| 2026-10-30 09:11 | `findmnt /media/usb`, current-boot kernel log, Btrfs device stats | `/dev/sdb1` Btrfs mounted rw; SuperSpeed connection; no USB reset in sampled log; all five Btrfs device error counters zero |
| 2026-10-30 11:05 | Current-boot journal filter and snapshot-create service status | No matched USB reset/disconnect/I/O error; snapshot-create service succeeded at 11:00:04 UTC |
| 2026-10-30 11:06 | `/usr/local/bin/btrfs-native-push --protected-prune-plan` on mars | EXIT 0; `receiver_verified_under_lock=true`, `source_pinned=true`, protected snapshot `20261030-030033Z`, source UUID `d901ddd2-66c7-0b42-b26c-ab6886273b7a`, `total=26`, `retained=26`, `candidates=[]`, `authorizes_prune=false`, `deletion_executed=false` |
| 2026-10-30 11:08 | Receiver snapshot-manager `status` | `managed_snapshots=26`; complete sets 26; incomplete 0; qgroups total 29, stale 0, under deletion 0, status ok; retention hourly 48 / daily 14 / weekly 12 / monthly 24 / yearly 5, minimum age 30m |
| 2026-10-30 11:08 | `/usr/local/sbin/btrfs-receiver-prune --verify-boundary` on backup | PASS: privileged receiver boundary checked; no deletion permitted |

## Interpretation and limits

The previous 20-second source-protection subprocess timeout was not reproduced during the 0.75-second direct invocation or later protected plan. The cause remains unproven. Changing USB ports restored the expected 5Gb/s negotiated USB link and coincided with a stable sampled interval, but does not prove long-term USB reliability.

The protected prune plan identified **zero** eligible receiver deletion candidates. This validates the conservative empty-set behaviour, not a live deletion transaction. The boundary command does not itself authorise deletion. Preserve both source protection and receiver checkpoint holds.

## Deferred acceptance gates

1. Wait for a naturally eligible receiver-only deletion candidate; do not manufacture eligibility or delete a retained snapshot for testing.
2. Review fresh source and receiver inventories, protected common parent, UUID lineage, protected holds, and actual dry-run eligibility under locks.
3. Explicitly approve one candidate and conduct one guarded sender-initiated receiver-only deletion; verify the corresponding source snapshot still exists with unchanged UUID, receiver count decreases by exactly one, protected parent/holds remain, and receiver qgroups and journals are healthy.
4. Re-run source regressions, Ansible `--check --diff`, scoped controlled deployment if any code/config changes become necessary, then runtime and idempotency checks.
5. Only after acceptance and an explicit separate gate should unattended receiver pruning be considered for enablement.

## Repository provenance caveat

This evidence note is an **additive** change-control artifact, based on observed logs. The supplied Diaries/Playbooks source archives are dated **2026-10-26**, earlier than these live verification results and subsequent Stage B code changes. This note deliberately does not overwrite later change-control files or claim to be a source-of-truth snapshot of the current Playbooks checkout. Compare with the live repositories before commit.
