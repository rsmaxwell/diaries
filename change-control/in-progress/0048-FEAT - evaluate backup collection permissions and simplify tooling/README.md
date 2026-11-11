# 0048-FEAT — Evaluate backup collection permissions and simplify tooling

- **State:** PLANNED — NOT STARTED
- **Opened:** 2026-11-11
- **Prerequisites:** **0046-FEAT and 0047-FEAT must both be formally CLOSED, with published commits and accepted evidence.**
**Ownership:** Diaries parent Git change control; permanent Ansible code/configuration belongs in the Playbooks Git repository on `mango`.

## Objective

Establish which source and deployed file/directory permission bits are genuinely required by the `backup-collection` role, rather than assuming every historical mode from the 0045 installed-state baseline is essential. Use that evidence to simplify the fresh-clone and deployment workflow: ideally a normal Git checkout should work with rsync preserving each source entry's native mode, without a special source-mode restoration step or blanket `--chmod` settings.

**The desired result is evidence-based simplification, not permission relaxation for its own sake.** If a non-Git-representable mode is actually required, keep the smallest justified mechanism that reliably establishes it and document why the tool cannot yet be retired.

## Deferred start — hard prerequisites

Do not implement, deploy, retire, or alter source-mode tooling until BOTH are true:

- `0046-FEAT — Move non-sensitive Ansible inventory into Playbooks Git` is formally **CLOSED** and the new inventory/Vault resolution is accepted.
- `0047-FEAT — Retire legacy backup entry points and align collection role` is formally **CLOSED**, including its installed-state equivalence, source-mode correction, and publication evidence.

At execution time, resolve closed feature records from `change-control/complete/`, and freeze **then-current** Windows Diaries/submodule and `mango` Playbooks Git revisions. The November source bundles and 0047 planning SHA are not a substitute for that fresh baseline. Do not reopen or rewrite either closed feature.

## Source and deployment boundaries

- Source: `/home/richard/playbooks/roles/backup-collection/files/backup/` and `files/backup-machine/` on `mango`; role tasks `install_user_scripts.yaml` and `install_machine_scripts.yaml`.
- Deployed targets: normal-user `~/scripts/backup/` and `/root/scripts/backup/` on `mars`, including the copied include/exclude configuration files and directories. Inspect corresponding consumers, ownership, ACLs and ancestor traversal permissions.
- Audit the actual Git executable bits (`100644`/`100755`) and directory modes from a genuine fresh checkout. Git does not retain arbitrary group-write bits (`0644` vs `0664`) or directory modes (`0750` vs `0755`).
- Examine the 0047 per-path contract `roles/backup-collection/source-modes.json` (historically nine files at `0664` and five directories at `0750`) and the one-off `restore-0047-collection-source-modes.py` preserved in 0047 change control.
- Preserve `ansible.posix.synchronize` archive-mode source metadata with `--omit-dir-times`; **do not add `--chmod` or `--no-perms`** as a convenience workaround.

## Scope

- Review actual runtime access requirements, file modes, owner/group/ACLs, executor identities, and role ordering; distinguish *required* bits from merely historical bits.
- Test a genuinely clean clone of the **post-0046/post-0047** Playbooks source, without any 0047 restoration step, in a disposable, controlled verification environment before touching installed configuration.
- Pay particular attention to Ansible's `file: mode: "0750"` on normal-user directories: subsequent rsync from a fresh-clone source directory may set `0755`, widening access and producing repeated `changed` tasks.
- Compare affected installed content, owner/group, permissions, ACLs, service/timer behaviour, scheduled jobs and backup read/write outcomes against the accepted baseline, with explicit security review of any intended permission changes.
- Remove the *active requirement* for source-mode restoration and any redundant Playbooks per-path manifest/regression/documentation only if fresh-clone correctness, security and repeated idempotence are demonstrated. Keep historical 0047 tools, reports and evidence in its closed feature directory for audit.
- Update the permanent Playbooks role documentation and maintain only useful permanent regressions; keep one-off tests/tools and evidence within this 0048 feature directory in the Diaries parent repository.

## Out of scope

No inventory migration (0046 owns that), legacy interface renaming (0047 owns that), backup data modification, destructive snapshot/pruning operations, manual replication, restore exercises, schedule or retention changes, new privilege grants, credential exposure, or unrelated role cleanup. Do not change destination modes without an explicit access/security rationale and reversible installation plan.

## Deliverables and closure

See [`IMPLEMENTATION-STEPS.md`](IMPLEMENTATION-STEPS.md), [`PERMISSION-DECISION-CONTRACT.md`](PERMISSION-DECISION-CONTRACT.md), and [`tests/ACCEPTANCE-MATRIX.md`](tests/ACCEPTANCE-MATRIX.md). The final disposition must explicitly say either **(A) the 0047 restoration dependency is retired** or **(B) it is retained/replaced for enumerated requirements**, and include the corresponding fresh-clone and idempotence evidence. Mark 0048 CLOSED and move it from `in-progress` to `complete` only after formal acceptance and publication of both repositories' actual results.
