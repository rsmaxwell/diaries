# 0040-FEAT — Step 11 status reconciliation (26 October 2026)

## Accepted: historical native `root` snapshots on `mars`

- Exactly **63** UUID/ID-manifested historical native `root` snapshots were deleted on `mars` following explicit operator authorisation.
- Durable receipt reconciliation: one `BEGIN`, 63 `DELETE_INTENT`, 63 `DELETED`, one `COMPLETE`.
- Post-deletion inventory found **zero** historical `root` snapshot directories and zero `@snapshots/root/` Btrfs subvolumes.
- The two historical checkpoint holds remain present; 63 complete managed `@data` timestamp sets and **zero incomplete** at final accepted verification; Diaries schema-2 verification valid.
- Temporary replication masking was removed; the original service definition restored with SHA-256 `2fb648b14860a107bea883c3becbd7594de9cf4ab4196b2f39eebe9befbcfff3`; native push timer active/enabled, next run shown as 27 October 2026 03:30 UTC.
- On `mango`, snapshots and replication Ansible `--check --diff` for `mars` both returned `changed=0`, `failed=0`. `backup` receiver recovery returned `CLEAN`. Receiver pruning remained disabled.
- On-host retirement receipt path: `/media/usb/@snapshots/.0040-step11-root-retirement-receipt.jsonl`; SHA-256 `e75e5c57f5a99524d37dccca2c8c9982a1e22b32e011b9bd95f132901cc8c955`.

## Already absent: numerical Snapper subvolumes on `mars`

The Step 10 historical `mars-retirement-approved-manifest.json` specifies **17** legacy Snapper targets. On 26 October the live `/media/usb/@data/.snapshots` directory was absent and `btrfs subvolume list /media/usb` reported no subvolumes beneath `@data/.snapshots`. Archived `mars-retirement-batch*.txt` and `mars-snapper-final-*.txt` reports are preserved in the Step 10 archive. The present inventory is consistent with completed historical retirement; consult these original logs for the detailed deletion chronology rather than inferring it from absence alone.

## Remaining Step 11 reconciliation — **OPEN**

- On 26 October `mars` still reported installed `snapper` package `0.10.6-1.1build1`, an `/etc/apt/apt.conf.d/80snapper` hook, and residual filter/template files in `/etc/snapper`. No Snapper unit names were reported by the read-only unit-file listing. The displayed APT hook invokes Snapper only when `/etc/snapper/configs/root` is present, and no such active config was listed. Therefore no active writer has been demonstrated, **but permanent retirement of residual software/hooks is not yet accepted**.
- Inspect the established Step 11 requirement to disable retired writers/hooks through Playbooks and decide whether a controlled, idempotent Snapper purge or explicit justified retention is appropriate. Do not blindly reproduce the `backup` purge: it created an unexpected APT snapshot there before the hook was removed.
- Archive the durable `mars` native-root retirement receipt and pertinent execution/verification logs in Step 11 evidence, preserving source checksums and script/manifest revisions.
- Preserve 0039-DEF in `in-progress`: stale qgroups on `mars` were **357** after retirement; separate defect, no qgroup surgery in this step.
- Step 12 receiver-pruning activation remains **OPEN**, separately gated and not authorised by Step 11 successes.

**Decision:** Historical root-snapshot deletion and replication restoration **ACCEPTED**; **overall Step 11 remains OPEN** for residual Snapper lifecycle and durable evidence closure. No new snapshot deletion or off-site restore is requested by this record.
