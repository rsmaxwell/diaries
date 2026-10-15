# 0035-FEAT implementation steps

## Step 1 — Freeze the current Snapper state on `mars` and `backup`

Before changing scheduling, capture on both hosts:

```bash
findmnt -t btrfs
sudo btrfs subvolume list /
sudo snapper list-configs
sudo snapper -c root get-config
sudo snapper -c @data get-config
sudo snapper -c root list
sudo snapper -c @data list
systemctl list-timers --all | grep -E 'snapper|btrfs-snapshot'
```

On `mars`, use the appropriate Btrfs mount path (`/media/usb`) for direct Btrfs inspection where required.

Record the exact effective Snapper retention settings, current numeric snapshot inventories and timer states. This evidence establishes the migration baseline and avoids guessing any effective setting supplied by the external Snapper role.

**Complete when:** both hosts have a dated pre-change inventory in 0035 evidence.

---

## Step 2 — Implement the shared native Btrfs snapshot manager

Implement one permanent `roles/snapshots` manager with:

- UTC timestamp naming;
- a separate `@snapshots` Btrfs subvolume;
- `root` and `@data` source definitions;
- read-only native Btrfs snapshots;
- source/repository same-filesystem validation;
- process locking;
- multi-source create rollback;
- list/status commands;
- GFS-style retention;
- dry-run pruning;
- strict timestamp namespace filtering.

Add permanent regression coverage for retention selection and safety boundaries.

**Prepared 2026-10-08.** `btrfs-snapshot-manager.py`, role defaults/templates/tasks/documentation and `verify-btrfs-snapshot-manager.py` are implemented in the supplied Playbooks source. Python compile, regression and YAML parse checks pass.

---

## Step 3 — Wire both Linux backup hosts to the shared role and define migration scheduling

Keep `mars` using the shared role from `local-backup` and replace the duplicate `remote-backup` Snapper implementation with the same role.

Install:

```text
btrfs-snapshot-create.timer
btrfs-snapshot-prune.timer
```

After native-manager `status` preflight succeeds:

```text
disable snapper-timeline.timer
disable snapper-boot.timer
retain snapper-cleanup.timer temporarily
```

Do not delete legacy Snapper configs/snapshots during this step.

**Prepared 2026-10-08.** Both host paths are wired to the shared role; the duplicate active Snapper path has been removed from `remote-backup`; source regression verifies the handover contract.

---

## Step 4 — Deploy and prove `mars`

On `mango`, first run permanent source regression:

```bash
cd ~/playbooks
python3 roles/snapshots/tests/verify-btrfs-snapshot-manager.py
```

Then deploy the snapshot role to `mars`:

```bash
./scripts/snapshots.sh mars
```

On `mars` verify:

```bash
sudo btrfs-snapshot-manager status
sudo btrfs-snapshot-manager list
systemctl status btrfs-snapshot-create.timer --no-pager
systemctl status btrfs-snapshot-prune.timer --no-pager
systemctl is-enabled snapper-timeline.timer
systemctl is-enabled snapper-boot.timer
systemctl is-enabled snapper-cleanup.timer
```

Create a controlled timestamp set and inspect it:

```bash
sudo btrfs-snapshot-manager create
sudo btrfs-snapshot-manager list
sudo btrfs subvolume list /media/usb | grep '@snapshots'
```

Run pruning only as dry-run initially:

```bash
sudo btrfs-snapshot-manager prune --dry-run
```

**Complete when:** `mars` has a valid same-timestamp `root` + `@data` set, native timers are active, new Snapper creation is disabled, legacy cleanup remains active, and no existing backup content changed.

---

## Step 5 — Deploy and prove `backup`

Deploy from `mango`:

```bash
cd ~/playbooks
./scripts/remote-backup.sh
```

On `backup` perform the same checks, using `/@snapshots` and `/@data` paths:

```bash
sudo btrfs-snapshot-manager status
sudo btrfs-snapshot-manager create
sudo btrfs-snapshot-manager list
sudo btrfs-snapshot-manager prune --dry-run
sudo btrfs subvolume list / | grep '@snapshots'
```

Verify timer handover exactly as on `mars`.

**Complete when:** `backup` passes the same creation, listing, dry-run retention and Snapper-handover checks.

---

## Step 6 — Prove retention and deletion safety

Build enough controlled timestamp snapshots to exercise at least two retention buckets without waiting for real calendar ageing. Prefer a disposable Btrfs test area or explicitly controlled test snapshots; do not manufacture fake production timestamps unless the procedure is documented and safe.

Prove:

- dry-run output matches the expected keep/delete plan;
- only manager-owned timestamp names are candidates;
- a numeric directory is ignored;
- a nonmatching directory is ignored;
- deleting an eligible native snapshot does not alter another retained snapshot;
- `root` and `@data` remain readable after prune;
- normal backup/rsync jobs continue to work.

**Complete when:** retention is proven with captured before/after inventories on both Linux hosts or one representative host plus configuration-equivalence evidence for the other.

---

## Step 7 — Observe legacy Snapper retirement and remove the dependency

Allow `snapper-cleanup.timer` to continue applying the existing legacy policy while no new timeline/boot snapshots are created.

Periodically record:

```bash
sudo snapper -c root list
sudo snapper -c @data list
```

When no retained legacy snapshots require Snapper:

- disable `snapper-cleanup.timer`;
- remove obsolete Snapper configs/package if no other host function needs them;
- remove `aisbergg.snapper` from the controller dependency path if unused elsewhere;
- remove obsolete `create_snapper_*` helpers from both old source locations;
- verify rerunning Playbooks is idempotent and does not recreate Snapper configuration.

**Complete when:** `mars` and `backup` have only the native timestamp snapshot manager as their Linux snapshot lifecycle mechanism.

---

## Step 8 — Final documentation and close-out

Record:

- final paths and effective retention values;
- timer schedules;
- operator list/create/prune commands;
- restore/access examples;
- rollback to Snapper procedure;
- relationship to Synology DSM snapshots;
- relationship to 0034 Diaries reflink-aware complete backups.

Run final source regression and host-state checks, classify permanent versus feature-only tooling under the 0032 hygiene rules, and move 0035 from `in-progress` to `complete` only after live evidence is preserved.
