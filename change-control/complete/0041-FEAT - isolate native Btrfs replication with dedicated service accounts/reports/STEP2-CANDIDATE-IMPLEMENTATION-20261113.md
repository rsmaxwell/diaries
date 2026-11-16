# 0041-FEAT — Step 2 design acceptance and source candidate

**Recorded:** 13 November 2026 UTC
**State:** Candidate source implementation, **not deployed**. Steps 3–10 remain OPEN.

The operator agreed to the goal of dedicated unprivileged sender/receiver
accounts, narrowly restricted privileged operations and no change to
`richard`'s personal SSH or sudo access, and requested implementation.
This follows the approved direction of
`reports/STEP2-RESTRICTED-IDENTITY-DESIGN-PROPOSAL-20261113.md`.

## Implemented in candidate Playbooks package

- Default-off `btrfs_0041_additive_enabled` gate and explicit
  `btrfs-0041-provision` tag; both endpoints must be selected.
- Provisioning of `btrfs-send` on `mars` and `btrfs-receive` on `backup`.
  New Ed25519 private key stays on `mars`; only public key crosses through
  Ansible. Receiver's `authorized_keys` is managed by root and contains
  only a restricted, forced-command key.
- Fixed, no-argument root sudo entrypoints. Sender transaction keeps the
  existing lock across transfer and reconciliation. Receiver dispatcher
  validates exact operations; the privileged gate validates them again
  and passes binary receive input without a buffered read ahead.
- Opt-in dedicated SSH transport in the existing simplified runtime;
  legacy transport remains its exact default, including for the currently
  scheduled service. The unknown-mode case refuses instead of falling back.
- A candidate (non-active) systemd unit only; **no scheduled timer changes**.
- Python source tests for allowed/denied commands and stream integrity.

## Conserved properties

- The manager lock and existing sender/receiver agreed-parent schema remain
  unchanged; source/receiver current and prior roots remain protected.
- Root-managed snapshot creation, pruning and qgroup cleanup unchanged.
- No snapshot, backup dataset, replicated state or root-owned `0600`
  agreement files are changed by applying the ZIP to the Playbooks checkout.
- Current receiver `.replication-state` directory and `writer.lock` ownership
  are **not** silently migrated in this package; any migration needs its own
  inode/consumer review after additive tests.
- `richard` account, memberships, authorized keys and sudo rights untouched.

## Verification and limitations

The package was built from the uploaded source bundle dated 12 November 2026.
The current live baseline dated 13 November verified the identical shared
replication runtime hash, with Playbooks commit `c510934` and controller commit
`83cba34`. The reviewed package changes only `roles/btrfs-replication/`.

Local checks: new adversarial contract tests and unchanged 0040 replication
unit tests pass. These do not constitute Ansible runtime syntax/host validation
or a real SSH/Btrfs stream integration. Do not mark Step 3 accepted or deploy
on the strength of local checks alone.

**Residual root boundary:** One fixed sender sudo entrypoint still executes
all of the existing trusted sender Python transaction as root while its SSH
transport runs without administrative privileges. It does not claim that the
503-line trusted transaction was split into individually capability-scoped
kernel operations. This preserves the continuous manager lock and recovery
semantics until an equivalent split can be demonstrated safely.

**Next action:** Apply the Playbooks ZIP to the `mango` submodule via Beyond
Compare, and the separate Diaries ZIP to the Windows parent checkout. Run the
single consolidated source regression/syntax/check-mode script from Windows,
saving its log under the 0041 feature directory. Examine results before any
live service-account provisioning.
