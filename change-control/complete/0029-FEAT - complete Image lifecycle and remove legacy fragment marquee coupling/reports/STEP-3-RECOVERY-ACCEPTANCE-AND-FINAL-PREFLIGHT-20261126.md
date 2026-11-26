# 0029-FEAT — Step 3 recovery acceptance and final production preflight handoff

Date: 2026-11-26. **Step 3 OPEN; production cutover not authorised.**

## Operator-confirmed completed acceptance

- Source release: Client `cc826a8254b0e6d989755dc880d3023dae9e3416`, Responder `a49c6abd0ce005d58eb516770f6515313e40cdf6`, Reader `363ca8f425b811eeedff47486092b1f63c403ab0`; parent `216413468fbaae21dbfbfe36e92c05cd87cba907`.
- Published images: Client `0.0.9-build-81`, Responder `0.0.9-build-87`, Reader `0.0.9-build-10`; all five local published-smoke containers healthy; all six Editor/Reader browser checks operator-reported PASS. Development dataset only.
- Playbooks release `e1273b48b1cea2e175ea098a0a82ff8b0b184851` published, controller pointer commit `29c562f` published. Annual MQTT ACL source and new image role defaults included; **not deployed**. Controller `enter.sh` and Playbooks `scripts/diaries.sh` local modifications preserved.
- Existing isolated production migration forward/rollback/reapply and independent PostgreSQL backup restoration previously passed. Do not repeat expensive accepted rehearsals without new cause.
- On mars, `sudo -n diaries-backup-status` reported **HEALTHY**, 24 distinct backup IDs, 83 retained occurrences and zero manifest-identity conflicts. This is **manifest-level** status, not exhaustive content validation.
- Backup `production/20261126-003058Z` at Btrfs snapshot `20261126-150001Z`, path `/media/usb/@snapshots/@data/20261126-150001Z/backup/pluto/diaries-backup`. Root size approximately 99 MiB, of which Files approximately 98 MiB. The selected complete Files directory was copied with `cp -a` into a disposable `/var/tmp/0029-files-restore.*` folder on mars; `diff -qr` returned no differences; source/restored file counts both **128**; script emitted **PASS**. No complete disaster recovery on another host was exercised. Cleanup was configured by EXIT trap but not independently logged.

## Current release gate

1. Use the existing read-only 0029 tool `tools/run-step3-production-readonly-gate.sh` to check live PostgreSQL guarded baseline. This is read-only against pluto but writes the diagnostic log under this feature evidence folder in the Windows repository. Do not proceed if its `GATE=PASS` is absent.
2. Use `tools/run-step3-production-release-metadata-audit.sh` to collect current production image identities, installed ACL and timers, while checking effective inventory and committed role defaults. The tool's final 'metadata collection PASS' is not a release go-ahead.
3. Confirm a **fresh consistent database and Files recovery point during the approved production freeze**, before any migrations. The 00:30 UTC snapshot is not by itself a pre-cutover recovery point for writes made later in the day.
4. Freeze writers, perform the rehearsed hybrid ownership SQL then Marquee `page_id` retirement, deploy coordinated Client/Responder/Reader image tags and MQTT years ACL, validate topic-tree reconciliation and run production browser/postflight checks. Keep documented rollback image tags `80/86/9` and the previously tested reverse SQL order; if post-cutover edits occur, do not assume reverse SQL is safe without restore review.
5. Obtain explicit user approval before any production mutation or Ansible deployment. Record gate outputs and results under this feature directory; close Step 3 only following accepted evidence, and close the feature only upon formal acceptance.

## Evidence references

- Operator terminal `note(20261126-151247).txt`: sudo backup status successful.
- Operator terminal `note(20261126-151404).txt`: latest backup path and retained snapshots.
- Operator terminal `note(20261126-151452).txt`: Files location and size.
- Operator terminal `note(20261126-164843).txt`: 128/128 Files restored, complete copy comparison PASS.
- Operator terminal `note(20261126-150941).txt`: Playbooks release push PASS.
- Operator terminal `note(20261126-151035).txt`: controller pointer push PASS.

**Boundary:** Evidence is operator-supplied terminal output, not rerun from this document. Do not report production deployment or freshness gate as complete until performed and accepted.
