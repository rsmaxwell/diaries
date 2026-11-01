# 0040-FEAT — Step 12.3b authority-storage acceptance (27 October 2026)

**Decision: Step 12.3b authority-storage increment ACCEPTED. Overall Step 12 and Step 12.3 remain OPEN. Receiver pruning is disabled.**

## Scope and authoritative sources

This increment provisions directories for a future root-held, one-time receiver-prune approval/consumption protocol. No approval or consumed marker was created; no receiver deletion execution, sudoers change, service/timer change or enablement was authorised. Playbooks repository on `mango`: commit `b53ebf5` (`0040-FEAT Step 12.3b root-owned prune authority storage`), synchronized with `origin/main` as observed in `note(20261027-130951).txt`. The regression file was already tracked; the commit adds 48 lines to `roles/btrfs-replication/tasks/native.yaml`.

## Acceptance evidence

| Gate | Observed outcome | Raw evidence |
|---|---|---|
| Source regression and whitespace check | `verify-0040-step12-3-authority-storage.py` passed; `git diff --check` passed; 48 insertions, no deletions | `raw-logs/note(20261027-130151).txt` |
| Targeted Ansible preview | `btrfs-replication.yaml --limit backup --tags native-btrfs-prune-authority --check --diff`; 3 absent directories proposed, recap `ok=3 changed=1 failed=0 unreachable=0` | `raw-logs/note(20261027-130324).txt` |
| Controlled deployment | Same target/tag with `--diff` and without `--check`; 3 directories created, recap `ok=3 changed=1 failed=0 unreachable=0` | `raw-logs/note(20261027-130440).txt` |
| Runtime owner/mode | All three paths `root:root`, mode `0700` | `raw-logs/note(20261027-130613).txt` |
| Root approval files/consumed records | `find ... -mindepth 1 -type f` produced no entries (at inspection time) | `raw-logs/note(20261027-130613).txt` |
| Prior replication-state directory | `/@data/mars-received/.replication-state` remained `richard:richard`, mode `0700` at verification | `raw-logs/note(20261027-130613).txt` |
| Pruning gate | Manager config `mode: receiver`, `receiver_prune_enabled: False` | `raw-logs/note(20261027-130613).txt` |
| Repeat targeted check | All three safety assertions passed; recap `ok=4 changed=0 failed=0 unreachable=0` | `raw-logs/note(20261027-130613).txt` |
| Git source commit | `b53ebf5`, synchronized local/remote tracking; the only untracked file reported was temporary authority-storage `.patch` | `raw-logs/note(20261027-130800).txt`, `raw-logs/note(20261027-130951).txt` |

## Created directories on backup

- `/etc/btrfs-receiver-prune` — `root:root 0700`, intended approval authority storage.
- `/var/lib/btrfs-receiver-prune` — `root:root 0700`, intended protected state.
- `/var/lib/btrfs-receiver-prune/consumed` — `root:root 0700`, intended durable one-time consumption markers.

## Residual gates

The root-owned directory layout **does not itself provide authenticated deletion authority**. Step 12.3c privileged gateway and source-held remote transaction wiring still require independent source review, adversarial tests, Ansible preview, controlled deployment and rollback proof. Cross-host production deletion has **not** been authorised or claimed tested. Keep `receiver_prune_enabled: False` until separately accepted. The `0041-FEAT` dedicated-principal design is outside this increment; do not change the existing `richard` sudo/SSH rights here.

## Evidence integrity and constraints

These raw logs were captured from the operator's 27 October 2026 terminal notes, not regenerated. Some pasted terminal command echoes were garbled in the runtime/idempotency log, but its outputs and Ansible recap are visible. A `changed=0` **Ansible check-mode** recap is recorded; do not mislabel it as a second live apply run. The empty-file check inspects regular files, not a comprehensive scan for all possible non-regular children.
