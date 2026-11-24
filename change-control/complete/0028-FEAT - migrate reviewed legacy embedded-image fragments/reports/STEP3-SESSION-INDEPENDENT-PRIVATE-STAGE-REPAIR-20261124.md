# 0028 — Session-independent private staging repair (24 November 2026)

## Trigger and evidence

At 18:15 UTC the owner-approved `probe` failed with `Missing approved transient stage`. The JAR/manifest staging script previously succeeded at about 16:58 UTC, but its path was `/run/user/<uid>/0028-production-migration-input`, an SSH-session-lifetime location potentially removed by `systemd-logind` at logout. No migration dry-run or apply took place. Writer isolation remained active and the exact pre-conversion dataset `production/20261124-172811Z` was held on `mars` and `backup` as snapshot `20261124-173416Z`.

## Corrective action

Both the Cygwin staging helper and the `pluto` Java dry-run launcher now use exactly `/run/diaries-0028-production-migration-input`, outside `/run/user/<uid>`. The helper checks nonexistence, uses `sudo -n install -d` for the initial owner-only directory, creates a private reviewed-input directory, uploads the pinned JAR and reviewed manifests, and verifies the JAR SHA-256 from a **new SSH session**. It refuses to overwrite an existing stage. It neither changes PostgreSQL nor alters running services. The Python runner still verifies the pinned SHA-256, prepared manifest checksums, a private owner-only stage, read-only Files mounts and the active writer-isolation contract before `probe` or `run`. Its modes remain `preflight`, `probe`, `run`; `apply` is unavailable.

## Maintenance resumption

Under the existing owner's limited approval, re-apply this small source-only package using Beyond Compare, run the corrected dry-run test, stage once, then `probe`, then `run` with the already pinned artifact SHA-256. Do not repeat the completed fixed backup, pull, holds, or replication; verify the isolation status and independent NAS writers first. Do not execute an unreviewed cleanup of the old `/run/user` stage. Copy result files into private feature evidence and verify the 71 conversions / Fragment 1564 deferred / 30 links / 22 Marquees. **No production migration apply is authorised.**

### Cleanup

The new stage is under tmpfs `/run` and persists across SSH sessions until reboot. After privately capturing and accepting evidence, remove only this exact stage with a separately reviewed command (not bundled here), preserving all backups and release receipts. If the stage disappears due to host reboot, stop and re-evaluate isolation and live state before restaging.
