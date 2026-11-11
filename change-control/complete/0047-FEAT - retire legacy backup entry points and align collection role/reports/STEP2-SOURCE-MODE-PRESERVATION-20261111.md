# 0047 Step 2 — Preserve source modes through rsync

**State:** OPEN; pending corrective deployment and acceptance evidence.

The first 0047 application at Playbooks `833da94` returned `changed=2` on `mars` (the two collection copy tasks), `failed=0`, while native replication was idempotent. The rsync itemizations showed timestamp/permission changes to the include/exclude files. No installation equivalence was accepted.

**Decision:** Reject `--chmod=Fu=rw,Fg=rw,Fo=r` and remove the existing `--chmod=Du=rwx,Dg=rx,Do=`. Match `roles/ledger/tasks/copy.yaml`: use `ansible.posix.synchronize` with `archive: true` and `--omit-dir-times`; rsync preserves each individual source entry's mode without an override.

The accepted 0045 `mars` manifest specifies nine include/exclude files with `0664` and five corresponding synchronized directories with `0750`. Their **per-path** modes and the files' SHA-256 hashes are recorded in `roles/backup-collection/source-modes.json`. The feature-specific `tools/restore-0047-collection-source-modes.py` restores these modes only in `/home/richard/playbooks` on `mango`, after checking content hashes. The permanent regression verifies source modes, rejects all rsync `--chmod` use in the two tasks, and tests native mode synchronization plus idempotence.

Git tracks executable versus non-executable files but does not preserve full group-write modes (`0644` vs `0664`) or any directory modes. A fresh checkout or ZIP transfer may therefore need source metadata restoration; do not claim Git guarantees these 14 per-path modes.

**Verification:** After publishing the source correction, the feature-specific `tools/reconcile-0047-source-modes.sh --apply` permits only the two identified copy tasks to report changes in the first corrective deployment, compares installed configuration and modes against the unchanged accepted 0045 baseline, and invokes the existing consolidated 0047 idempotence and health checks. No backup/restore or snapshot replication exercise is needed. Preserve evidence under `evidence/Step 2/`.
