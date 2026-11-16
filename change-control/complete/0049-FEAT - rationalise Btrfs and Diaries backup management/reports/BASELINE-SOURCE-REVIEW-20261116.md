# 0049 — Source review supporting the proposed feature

**Review date:** 2026-11-16. **This is source-bundle review, not live-host verification.** The 2026-11-12 supplied Playbooks and Diaries source bundles are the most recent files available for this review; actual installed host state and the 0041 closure changes must be recaptured at Step 1.

## Bundles inspected

- `playbook-sources-20261112-193409.zip` — SHA256 `1eafff3cef3606dcc53a4f9f15578f0ce3a5fff4bcb1f227bf8c0cc3a742be75`.
- `diaries-sources-20261112-194755.zip` — SHA256 `98f6c3ba7237f9e93a9b9f1c9f306550f962bb6b990ec6de420b1e88f595882c`.
- Latest Diaries bundle includes complete feature directories through 0047 and `in-progress/0048-FEAT - evaluate backup collection permissions and simplify tooling`. **0049 is the next available ID in that bundle**, not independent proof that no later local feature has been allocated.

## Observations grounded in reviewed source

| File (path relative to Playbooks) | Finding relevant to 0049 |
| --- | --- |
| `roles/snapshots/files/diaries-backup-status.py` | Current report reads snapshot-manager status, Diaries history, current receiving marker and `btrfs-simplified-replication sender status`. It prints `SNAPSHOT HEALTH`, `LAST VERIFIED PULL`, `LAST ACCEPTED OFF-SITE REPLICATION`, `NEXT SIMPLIFIED PUSH PREFLIGHT` and an unaligned recent-history list. `--json` already uses `indent=2`. Overall return is 0 unless a top-level configuration error, even if a subordinate check fails. |
| `roles/snapshots/files/diaries-backup-history.py` | `list` and `list --all` already have partial fixed-width table headers; output includes `verified`/`conflict` statuses, not necessarily a contemporaneous full-content verification. JSON list/show is currently compact (`sort_keys=True` without `indent`). `show` occurrences are one-line key/value fields; `path` prints an unadorned path. |
| `roles/snapshots/files/btrfs-snapshot-manager.py` | `show_status` prints qgroup/retention/snapshot data **and Diaries verification presentation**. Source `prune` supports `--dry-run` and optional `--max-delete`; receiver uses `receiver-simple-plan`/`receiver-simple-prune`, while an older separate `receiver-prune --approval-file` exists. Manager has distinct guards for receiver mode and writer locks. |
| `roles/btrfs-replication/files/btrfs-simplified-replication.py` | Operator `sender status` prints compact one-line JSON; source/receiver persistent files use `.simple-agreed-parent.json`; sender/receiver protocol also uses JSON, and not every JSON line can safely be changed without caller audit. |
| `roles/btrfs-replication/templates/btrfs-native-push.service.j2` | Source service unit named `btrfs-native-push`; its template refers to the simplified replication executable in the 2026-11-12 bundle, which predates the confirmed 0041 service-account cutover. Do not deploy this older template over the accepted current service context. |
| `roles/btrfs-replication/templates/btrfs-receiver-simple-prune.service.j2` | Receiver unit uses the historical `receiver-simple-prune --max-delete` and `btrfs_simplified_receiver_prune_max_delete` inventory variable. |
| `roles/btrfs-replication/templates/btrfs-receiver-simple-prune.timer.j2` | Receiver timer uses historical name/variables; schedule must not be guessed from the template alone. |
| `roles/btrfs-replication/README.md` | Notes active simplified agreed-parent sender, its existing `btrfs-native-push` unit name and receiver-specific pruning; retains historical explanations that can remain in archived feature evidence but should be simplified in live docs. |
| Diaries `change-control/in-progress/0048-FEAT.../README.md` | 0048 owns permissions/source-mode investigation for `backup-collection`. 0049 should not overlap that independent work. |

## Implementation cautions

- `0041-FEAT` was reported closed on 2026-11-16, after these source bundles; capture its exact accepted Git and deployed revisions before authoring any source/service change. No privilege behaviour should be guessed from older `User=root`/`User=richard` templates.
- Source and receiver agreed-parent state and the receiver prune journal protect real snapshots. Cosmetic rename cannot justify dropping or reinitialising those records.
- Historic `receiver-prune` and active `receiver-simple-prune` have different contracts. The name collision must be resolved by caller audit and tests, not a blind text replacement.
- The existing `diaries-backup-history` output is partly tabular. The task is to create a **consistent** table format rather than replace working history semantics.
- The project instructions require all feature evidence in this Diaries feature directory, while permanent operational changes remain in Playbooks. Nothing in this planning package claims a deployment, installed update or successful acceptance gate.
