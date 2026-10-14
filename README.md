# ansible-playbooks

## Btrfs snapshots

`mars` and `backup` use the shared `roles/snapshots` role. New snapshots are native read-only Btrfs subvolume snapshots named with UTC timestamps (`YYYYMMDD-HHmmssZ`) under a dedicated `@snapshots` subvolume. The role installs separate systemd timers for hourly creation and retention pruning.

During migration from Snapper, new Snapper timeline/boot creation is disabled while `snapper-cleanup.timer` is deliberately left active so legacy numeric-ID snapshots can age out naturally. See `roles/snapshots/README.md` for the layout, retention policy, commands and safety boundaries.
