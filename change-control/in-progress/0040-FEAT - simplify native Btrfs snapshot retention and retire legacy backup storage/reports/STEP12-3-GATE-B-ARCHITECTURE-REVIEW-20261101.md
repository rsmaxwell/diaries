# 0040-FEAT Step 12.3 — Gate B source review and read-only boundary inventory

Date: 2026-11-01. **Status: REVIEW IN PROGRESS; NO RUNTIME ACTIVATION APPROVED.**

## Source basis

Reviewed the uploaded Windows/Playbooks source bundles `diaries-sources-20261101-121953.zip` and `playbook-sources-20261101-121948.zip`, rather than assuming live Git checkout revisions match. Live host configuration has **not** been re-read during this review.

- `roles/btrfs-replication/files/btrfs-agreed-parent-fixed-commands.py`: fixed argv uses SSH with `BatchMode=yes`, `StrictHostKeyChecking=yes`, port 39263, `richard@10.254.22.1`, and prospective `/usr/local/bin/btrfs-agreed-parent-receiver`; receive/session/finalise/receipt commands.
- `roles/btrfs-replication/files/btrfs-agreed-parent-receiver-entry.py`: contains review/receive/session/finalise/receipt implementation; `promote_receiver_fixed` is internal and not exposed by its CLI dispatch. Root check in `main()` alone does not authenticate the SSH originator.
- `roles/btrfs-replication/files/btrfs-agreed-parent-receiver-operation-contract.py`: internal `promote` / `promoted-readback` operations explicitly lack an SSH authentication boundary and must not be forwarded to a generic privileged shell command.
- `roles/btrfs-replication/files/btrfs-agreed-parent-session-proof.py` and `btrfs-agreed-parent-sender-proof-handoff.py`: session-bound keyed evidence; live trust provenance of key provisioning, process wait completion and separate SSH request not yet demonstrated.
- Existing operational `/usr/local/bin/btrfs-native-push-receiver` and related endpoint were left in place at Gate A.
- The Step 12.3 linear reconciliation plan dated 2026-10-31 requires a single selected architecture and a failure matrix before code/activation; its original six design closure gates still govern Step 12.3.

## Architectural recommendation (PROPOSED, not approved)

Prefer a fixed-command SSH path using the existing `richard` account for 0040 (restricted dedicated identities deferred to 0041), with no arbitrary remote argument forwarding or broad new sudoers permission. A *trusted fixed receiver executable* must bind the actual authenticated SSH principal/command to precisely validated A/B arguments and binary stream handling. Separate `--receive`, `--session`, `--finalise`, `--receipt` operations must not permit premature promotion. A transition to B must require authenticated session-bound completion, independent local Btrfs identity and receipt verification, receiver durable promotion and independently locked readback; previous A remains pinned. No prune or release authority follows from a successful readback alone.

**Unresolved design decision:** Is the current single SSH receive with separate completion-proof connection sufficient to attest both the sender's send exit and remote receive exit, given the current SSH command and privileged process model? If not, define the smallest trusted companion/registration mechanism rather than silently treating HMAC assertion as proof. Audit child process lifetime and lock descriptor retention; current source comments acknowledge process-group escape risk.

## Read-only baseline required before implementation

Capture live revisions and status on `mango`; verify exact active SSH command boundaries and sudoers on `mars` and `backup`; inspect source-side send invocation and receiver command wiring; compare actual root-owned executable hashes to historical evidence where available; read current agreed-parent state and journals without changing them; inspect current timer enable/active state. Validate actual SSH host/port independently before proposing a fixed command. No secrets or private key content should appear in reports.

## Failure matrix to establish

| Event | Required result |
|---|---|
| SSH authentication/argument mismatch | Refuse before privileged operation |
| Sender send/SSH nonzero or unknown exit | Retain A, provisional journal, no receipt/promotion |
| Receiver timeout or lingering descendant | Fail closed; prohibit retry/prune until recovery |
| Receipt commit ambiguous or interrupted | Preserve A, investigate durable files; no blind retry |
| Receiver B promotion succeeds but acknowledgment lost | Re-read durable B/previous A state under locks; do not release A |
| Sender state disagrees with receiver | Halt promotion/prune; reconcile without discarding receipts |
| Unexpected pending journal or symlink | Refuse mutation and require manual inspection |
| Pruning races with receive | Lock and pinned-parent protection must prevent deletion of A/B |

## Next gate

Only after live observations and a reviewed sequence/failure matrix: source regressions, disposable Btrfs rehearsal, then a separate controlled `--check --diff` of any operational cutover. Step 12.3 and 0040-FEAT remain OPEN.
