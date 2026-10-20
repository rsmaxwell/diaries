# 0037-FEAT Step 4 — Read-only inventory and plan mode

Date: 2026-10-19. Status: **CLOSED — deployed and live read-only validation passed (2026-10-19)**.

## Scope

Adds a standalone `legacy-plan` command to Playbooks `roles/snapshots/files/btrfs-snapshot-manager.py`.
Existing scheduled `create`, `run`, `prune` and live deletion paths remain unmodified.
No legacy deletion command is present in this implementation.

Invocation (on the appropriate host with the manager and its existing configuration):

```sh
sudo /usr/local/sbin/btrfs-snapshot-manager --config /etc/btrfs-snapshot-manager.json legacy-plan --legacy-map root=root --legacy-map @data=@data --json
```

Use the actual installed manager path, source names and mapped Snapper config names. This command is read-only with regard to snapshots, but its existing preflight checks require correct installed configuration. Capture its output inside this feature's reports/evidence directory, not production source.

## Safety and handling

* Explicit `SOURCE=CONFIG` mappings required; Snapper `SUBVOLUME` must resolve to the configured native source.
* Reads Snapper's ISO CSV listing; requires schema columns and validates numbered, read-only Btrfs snapshot subvolumes. Refuses missing/malformed metadata rather than guessing.
* Native complete sets, pin and checkpoint state must be readable. Incomplete native sets abort the plan.
* Native retention set calculated exactly as before; retained native representatives win overlapping per-source UTC buckets. Legacy singles with `timeline` cleanup only are eligible for retention calculations.
* Snapshot zero is ignored; other snapshot types receive `EXCLUDED`.
* Newest eligible legacy single remains an anchor; minimum age applies. JSON advertises `authorizes_deletion=false`.
* No code path invoking `snapper delete` or `btrfs subvolume delete` was added to this command.

## Tests

* Existing manager test script `roles/snapshots/tests/verify-btrfs-snapshot-manager.py`: PASS in the bundled source checkout.
* Feature-local `tests/step04-plan-regression.py`: PASS, checking native overlap, historical bucket, newest-legacy anchor and no deletion authorisation.
* `python -m py_compile`: PASS.

## Remaining before Step 4 closure

Verify Snapper ISO CSV layout, current `SUBVOLUME` mappings and command behaviour on `mars` using non-destructive execution; expand adversarial coverage in Step 5. Source-only implementation is not a claim of successful deployment or operational compatibility. No timers, configurations or snapshots changed.

## Live verification and closure

See `STEP04-FORMAL-CLOSURE.md` for tested installation, observed snapshot decisions, corrected compatibility issues and remaining safeguards. Step 4 is closed; later destructive gates are not authorised.
