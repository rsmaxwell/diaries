# 0040-FEAT accelerated integration — receiver manager installation

Scope: add default-off receiver snapshot-manager source/config deployment via native Btrfs role on backup. No source snapshot configuration changes, timers, Btrfs operations or deletion enabled.

Opt-in variable: `btrfs_native_receiver_manager_install_enabled: true` must be supplied explicitly for backup after an Ansible `--check --diff` review. The config uses the existing receiver writer lock and received dataset; retention is 48/14/12/24/5 and 30-minute minimum age. Pruning remains unconditionally blocked in the Step 3K manager source even if this installation is enabled.

Required acceptance: review Ansible check/diff; on backup run `sudo btrfs-snapshot-manager --config /etc/btrfs-snapshot-manager.json receiver-plan` after controlled deployment. Current uploaded Playbooks baseline predates the Step 3K modified manager and must be updated before the opt-in deployment.

Not completed: integrated transaction executor, production-safe source-pin lifecycle, live replication verification and deletion. No production deployment authorised by this package.
