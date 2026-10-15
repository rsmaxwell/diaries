# 0034-FEAT — Step 11.1: Freeze final production baseline

**State:** EVIDENCE CAPTURE PREPARED — live capture and final sign-off PENDING.  
**Date:** 2026-10-13 (UTC).  
**Scope:** Read-only evidence, no changes to deployed services, storage or application backup schemas.

## Frozen known-good reference points (from operator evidence)

| Item | Verified reference point | Basis |
|---|---|---|
| Playbooks Git revision | `5d3b2b3` on `main`, pushed; clean working tree following commit | `note(20261013-195000).txt` |
| `mars` → `backup` native push receiver | `10.254.22.1:39263`, user `richard`, source initiated | Live incremental preflight/receive logs |
| Latest accepted incremental parent | `20261013-180016Z`, source UUID `0048afd8-59ec-7547-9247-e36893331838` | Receiver ACCEPTED and `mars` protection log |
| Held pre-cleanup checkpoint | `20261013-171228Z`, source UUID `340674cc-d02c-244e-b7ec-e3ea5a6b151f` | Receiver receipt and contents; `hold-list` and scheduled prune |
| Durable hold | `CHECKPOINT-HELD: ['20261013-171228Z']` | 19:15:18 UTC scheduled prune on 2026-10-13 |
| Active source parent | `REPLICATION-PROTECTED: ['20261013-180016Z']` | Same scheduled prune |
| Receiver receipt | `20261013-180016Z.json` present; `20261013-171228Z.json` previously verified | Host checks |
| Legacy pull installations | `/usr/local/bin/btrfs-native-pull` and `/usr/local/libexec/whole-backup-pull.py` absent | Final `backup` host checks |
| Snapshot pruning | Hourly timer active; latest witnessed 19:15:18 UTC, 1 complete timestamp set deleted safely | Scheduled service log |
| Receiver data | `/@data/mars-received/@data/<timestamp>` (read-only) | Btrfs subvolume show + receipts |
| Machine backup content | `mango` Playbooks and `mars` backup scripts present inside held snapshot and on receiver | On-host file checks |
| 0033 schema-2 | Contract unchanged by native replication cleanup | Source scope; **not a substitute for Step 11 restore validation** |

The historic full seed `20261012-100003Z` was accepted; historical snapshots/receipts are not to be removed. The cleanup commit `5d3b2b3` contains **97 files**, including unrelated ongoing work, due to `git add -A`; do not describe it as a cleanup-only commit.

## Capture now to finish 11.1

Copy `capture-step-11-1.sh` to each host (or run it from a reviewed local location), then on each of `mango`, `pluto`, `mars`, `backup` run:

```bash
bash ./capture-step-11-1.sh
```

Run under the normal administrative account. The script is **read-only** except for creating a local evidence directory in the caller's home directory. It uses `sudo -n` for privileged reads; if access fails, the evidence directory's `ERRORS.txt` identifies the gap. Do not use its results as proof of success unless `ERRORS.txt` is absent and the expected files are populated. Secrets may appear in captured config/diagnostics; inspect before transferring or committing evidence, and keep raw output private. Share redacted output.

The per-host output contains a SHA256 manifest of captured text files. Retain raw evidence outside Git if it exposes private topology or operational details; put a sanitized evidence index and relevant checksums in change control.

**Important:** Do not run `btrfs-native-push`, `btrfs-snapshot-manager create/prune` (without `--dry-run`), restore scripts, or any deployment as part of 11.1.

### Additional human verification required

1. Establish actual on-disk current `pluto` complete-backup generations and schema-2 manifests. The read-only generic discovery command is only a starting point; their location was not confidently resolved from the available static source.
2. Record Diaries repository Git SHA and cleanliness from the actual authoritative checkout (including whether there are local uncommitted changes). Do not assume Playbooks SHA covers Diaries code.
3. Compare expected and observed Btrfs filesystem UUIDs and mounts before signing; check that receiver `Received UUID` matches accepted source UUID.
4. Record schedule owners separately for `pluto` backup production, `mars` collection, `mars` timestamp snapshot creation/prune, and `mars` off-site replication (currently operator-initiated, not proven scheduled).
5. Check 0034/0035 historical rollback datasets remain present and accessible; do **not** delete anything in Step 11.1.

## Acceptance checklist

- [x] Known-good accepted snapshots, held checkpoint, parent state, deployment history and pushed Git revision documented from existing logs.
- [ ] Read-only capture from four hosts recorded and cross-checked.
- [ ] `pluto` current backup-generation identifiers/manifest(s) captured.
- [ ] Diaries source SHA and working tree state captured.
- [ ] Live mount, snapshot metadata, receipt, and configuration reconciled with frozen references.
- [ ] Relevant schedule ownership and unscheduled/manual choices documented.
- [ ] Operator accepts baseline; mark 11.1 CLOSED before beginning 11.2.

**Conclusion:** baseline definition is prepared; **11.1 is not CLOSED** on document generation alone.
