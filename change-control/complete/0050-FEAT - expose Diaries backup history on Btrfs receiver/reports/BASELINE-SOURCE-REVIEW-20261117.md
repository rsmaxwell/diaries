# 0050 — Initial source review (17 November 2026)

**Review state:** Source and accepted logs inspected; no `mango` or live host commands were executed for 0050, no code changes deployed, and no acceptance gate accepted.

## Source basis

- `playbook-sources-20261116-113514.zip`, captured from Ansible-controller Playbooks before 0049 implementation.
- Accepted 0049 repository-relative Playbooks implementation ZIP and subsequent naming/status correction ZIPs, corresponding to published Playbooks commit `a2508ad61f479c1b2bc20cb39896006c1f2906e1` based on accepted 0049 Git logs. This does not substitute for re-reading today's live checkout.
- Diaries source bundle `diaries-sources-20261116-113517.zip` and accepted 0049 closure log, published at Diaries commit `19dcaba94616152738fda1f93c504d77da888f63`.
- Snapshot inventory and receiver-root behaviour from accepted 0049 read-backs. Actual current snapshot counts, Git status and inventory values require new live capture before deployment.

## Findings

1. `roles/btrfs-replication/tasks/simplified-runtime.yaml` installs `diaries-backup-status` only if `btrfs_native_endpoint_role == 'source'`; no corresponding receiver install. The `snapshots` role's `installed-files.yaml` installs `diaries-backup-history` and schema-2 verifier for source usage; the receiver btrfs-replication role does not install them.
2. `roles/btrfs-replication/templates/btrfs-receiver-manager.json.j2` sets `mode=receiver`, snapshot root `/@data/mars-received`, `@data` snapshot directory `/@data/mars-received/@data`, and `verification.required=false`.
3. `roles/snapshots/files/btrfs-snapshot-manager.py` explicitly **rejects source verification being enabled in receiver mode**. Receiver discovery therefore needs an independent *reader-only* config namespace, not a change to Btrfs manager's `verification.required`.
4. `roles/snapshots/files/diaries-backup-history.py` currently requires `verification.required=true` to load its reader config and expects `sources[].path`. Apart from this config coupling, the reader already validates marker state, dataset path, manifest fields and SHA-256, groups occurrences and detects manifest conflicts, and supports `list`, `--all`, `show`, `path`, `verify` and JSON output.
5. `roles/snapshots/files/diaries-backup-status.py` invokes history using `--json list`, returns healthy/degraded/error with 0/1/2, and displays grouped retained backup history without claiming full content verification. Its header currently does not label the host and its docstring currently names `mars`.
6. `roles/backup-collection/defaults/main.yaml` describes embedded paths `backup/pluto/diaries-backup` and `backup/.diaries-snapshot-verified.json`; these are correct relative paths **within the received @data snapshot**, not at repository root.
7. `roles/diaries/files/sync/scripts/complete-dataset-manifest.py` is the existing schema-2 integrity verifier; the receiver must have an installed copy and permissions to read all required dataset files.

## Decision for the feature plan

Add a read-only `diaries_history` receiver metadata section to the existing receiver manager JSON, extend the shared history reader to consume it without affecting Btrfs-manager semantics, and provision the two commands plus verifier through the normal `btrfs-replication` role. No new SSH permissions, cross-host dependency or destruction of retained snapshots.

## Unverified assumptions to resolve in Step 1

- Actual `/etc/btrfs-snapshot-manager.json` on `backup` and current deployed installed-file hashes match the accepted 0049 implementation.
- Actual received marker, manifest, file permissions and schema-2 verifier requirements permit read-only traversal on `backup`.
- The installed manager tolerates an additive unknown `diaries_history` key (source suggests it parses known keys, but live syntax/manager status should confirm).
- Existing Playbooks Git HEAD, inventory activation state and pristine baseline must be checked before packaging operational changes.
- A genuinely receiver-only backup may not exist at the moment of deployment; fixture verification is mandatory and must not rely on deleting source backups to manufacture a case.

**Not claimed:** completion of feature code, deployment, test pass, source/receiver history parity, or actual retained unique backup on the live receiver.
