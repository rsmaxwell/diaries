# 0040-FEAT Step 11 — mars root retirement and operational cutover acceptance

**Date:** 26 October 2026  
**Decision:** **ACCEPTED — mars historical root snapshot retirement and @data-only cutover**. Overall Step 11 remains **OPEN** until the other planned legacy targets are explicitly reconciled and the evidence is archived. Steps 12–14 remain separate.

## Scope and authorisation

The operator explicitly authorised irreversible deletion of **63** UUID-identified, read-only historical root snapshots from `/media/usb/@snapshots/root/` on `mars` after the fixed manifest, offline tests, production preview, empty-content assessment and effective replication isolation had passed. This approval did **not** authorise removal of `@data` snapshots, checkpoint holds, backup receiver snapshots or further legacy targets. `backup` legacy Snapper retirement is covered by `STEP11-BACKUP-RETIREMENT-ACCEPTANCE-20261025.md`.

## @data-only operational cutover

- The two historical checkpoint holds (`20261013-171228Z`, `20261018-165453Z`) were migrated to `@data` UUIDs with the original hold state preserved as `/media/usb/@snapshots/.checkpoint-holds.0040-step11-before.json`. Original SHA-256 `185dd32d0b3f05a0a9ffd24515faf4956f41b69ff01234e9b5c260e6643988f3`; migrated SHA-256 `f9a57ddc8603be247c456784e589cb31aaf74daff17964f0873ac37a2d6766c2`.
- The `mars` snapshot-manager config was deployed as **only** `@data` (`/media/usb/@data`, `required=true`, `creation=true`, `prune=true`). Ansible applied one expected change; live status showed 74 complete and zero incomplete sets, verified Diaries backup `20261026-003102Z`.
- Controlled `@data` pruning deleted **11** retention-eligible sets; no checkpoint-held, replication-protected, or historical root snapshot was deleted by this operation. The subsequent scheduled pruning deleted **0** sets, exited successfully and respected the protected stamps. Both snapshot timers were subsequently active.
- The source manager and native replication Playbooks check/diff after restoration both reported **changed=0, failed=0** on `mars`.

## Immutable root retirement acceptance

- Frozen manifest: `roles/snapshots/tests/0040-step11/root-retirement-manifest.json` in the **live Playbooks tree** (not present in the older 25 October source ZIP). The planner and offline regressions live alongside it. Source revision and manifest checksum must be captured from `mango` before final archive.
- Production preview: **63/63** matching timestamp, Btrfs subvolume ID, UUID and read-only flags; no unexpected root entries or nested root subvolumes. The hardened preview under isolated native replication passed without deletion.
- Root-content inspection of all 63 found empty placeholder directories. A single extra but **empty** `diaries-0036-rehearsal` directory occurred in root snapshot `20261016-230026Z`; it was assessed and accepted.
- `btrfs-native-push` source endpoint uses `/media/usb/@snapshots/@data`, and receiver recovery was `CLEAN`. The original source service SHA-256 was `2fb648b14860a107bea883c3becbd7594de9cf4ab4196b2f39eebe9befbcfff3`.
- Runtime masking alone proved ineffective because `/etc/systemd/system/btrfs-native-push.service` outranked `/run/systemd/system/`. Original unit was preserved under `/etc/systemd/system/btrfs-native-push.service.0040-step11-before` and `/home/richard/btrfs-native-push.service.0040-step11-before`; a temporary effective persistent mask was verified `LoadState=masked`, `ActiveState=inactive`, `UnitFileState=masked` with replication timer stopped and normal source creation/prune timers active.
- Authorised production commit reported all **63** `DELETED` events and `COMMIT COMPLETE`. Independent reconciliation found one `BEGIN`, **63** `DELETE_INTENT`, **63** `DELETED` and one `COMPLETE` record; timestamp sequences matched; no historical root directories or subvolume entries remained. Permanent receipt on `mars`: `/media/usb/@snapshots/.0040-step11-root-retirement-receipt.jsonl`, SHA-256 **`e75e5c57f5a99524d37dccca2c8c9982a1e22b32e011b9bd95f132901cc8c955`**. Do not remove or rerun this receipt-driven commit.
- Restored original systemd source unit checksum matched baseline, temporary runtime mask removed, replication timer active/enabled with next 03:30 UTC execution; two snapshot timers active.

## Final operational acceptance (26 October 2026)

| Check | Accepted observation |
| --- | --- |
| Snapshot Playbooks `--check --diff` (activation skipped) | `changed=0`, `failed=0` |
| Native replication Playbooks `--check --diff` | `changed=0`, `failed=0` |
| Historical root snapshot directories | `0` |
| Native root Btrfs snapshot paths (immediately post-delete) | `0` |
| Manager `@data` sets | `63` complete; `0` incomplete |
| Diaries verification | valid, backupId `20261026-003102Z` |
| Two historical checkpoint holds | retained |
| `mars` source creation, prune and native push timers | all active; native push enabled |
| `backup` receiver recovery | `CLEAN` |
| Native replication after root retirement | **Not yet observed**; next scheduled 27 October 2026 at 03:30 UTC |
| Receiver pruning | **Remains disabled**, Step 12 separate gate |
| Btrfs stale qgroups on mars | `357` warning; deferred to 0039-DEF |

## Evidence / outstanding close-out

This report interprets operator-supplied terminal logs `note(20261026-074748)` through `note(20261026-115518)`; raw output is **not bundled** here. Preserve original logs, approved preview, explicit operator authorisation, manifest, regression source/results, source revision, the durable receipt and service-restore evidence in `evidence/Step 11/`. Avoid claiming an off-site incremental has succeeded *after* retirement until the unattended 27 October run is checked. No repeat full restore is justified by the accepted evidence.

**Overall Step 11 remains OPEN** pending inventory/reconciliation of any remaining approved `mars` legacy Snapper/live paths and actual archiving of original evidence; do not silently infer they are absent. The 0040 feature directory remains under `in-progress` until later steps and feature closure are accepted.
