# Step 03 — Shared Btrfs manager and guarded receiver deletion design

**Status: CLOSED 24 October 2026 for the Step 3 design gate; accelerated cross-host test waiver recorded.** The original `../reports/STEP03-DESIGN-START.md` says no source/production modifications; that sentence describes the *start* of Step 3, not the current state. This register records subsequent work without prematurely closing Step 3.

## Source/design evidence already recorded

- Design evolved through `../../reports/STEP03B-READONLY-RECEIVER-CONTRACT.md` to `STEP03K-TEST-TRANSACTION-SEQUENCE.md`, `step03l-preflight.md`, `step03l-accelerated-rehearsal.md`, `CONSOLIDATED-TRANSACTION-INTEGRATION.md` and `PARENT-JOURNAL-CONTRACT.md`. These contain earlier intermediate status statements and should be read as historical snapshots, not proof that all later integration gates passed.
- Receiver inventory validates read-only Btrfs snapshots, receipts and source/received UUIDs; retention plans are advisory, with no deletion authorisation. Locked receiver journal primitives and guarded transaction coordination are internal, not exposed by a production deletion CLI.
- Separate source pruning pin, protected-parent selection, live challenge-response and candidate eligibility checks were developed. Failure responses were verified to fail closed. One diagnostic issue remains: sender currently reports “Missing receiver candidate challenge” rather than surfacing the receiver's retained-candidate rejection.
- Historical checkpoint holds use the existing manager schema and a separately controlled root-owned `0600` file under `/etc/btrfs-receiver-checkpoint-holds.json`; Ansible initialises only when absent and validates mandatory entries on later runs. Receiver manager config requires holds and keeps `receiver_prune_enabled: false`.

## Accepted checks observed during 23 October session

| Check / gate | Observed evidence | Decision |
|---|---|---|
| Protected retention plan | Live `mars` → `backup` plan: 19 snapshots, 19 retained, 0 candidates; source pinned, no deletion | Accepted non-destructive |
| Candidate challenge and negative test | Live retained candidate `20261022-030026Z` rejected by `backup`: “Candidate is not eligible under receiver retention policy”, exit 1 | Accepted |
| Candidate-scoped wrappers | Source regression 9/9; `mango` Ansible deploy `mars changed=1`, `backup changed=1`; second run both `changed=0` | Passed |
| Internal coordinator | Cygwin→`mango` regression 8/8; `backup` wrapper deployment changed=1, repeat changed=0 | Passed; executor not publicly wired |
| Receiver checkpoint guard | Cygwin→`mango` regression 8/8 | Passed source regression |
| Permanent receiver holds | Ansible-source regression 8/8; live receipt identities `20261013-171228Z` = `340674cc-d02c-244e-b7ec-e3ea5a6b151f` and `20261018-165453Z` = `087c906a-0518-e34a-88f7-40a5b693c41a` | Passed |
| Inventory refactor | Existing `local_backup`/`remote_backup` group vars resolved `mars=source`, `backup=receiver`, manager opt-in only on `backup` | Passed |
| Receiver hold installation | `mango` `native-btrfs.yaml --limit 'mars:backup' --tags receiver-manager`: first deploy backup changed=3, mars changed=0; repeat both changed=0 | Passed |
| Live receiver hold enforcement | `backup`: config has `checkpoint_holds.required=true`, prune disabled; inventory 19 verified / 0 problems; plan 19 RETAIN, 0 candidates, executable=false; both historical checkpoints RETAIN | Passed read-only |
| Parent UUID binding | The 24 October deployment contains the expected-parent-UUID validation on `backup`; deployed manager/receiver-helper checksum and Ansible parity passed. The supplied 24 October logs do not independently establish the historical 5/5 source-regression result | **Deployed; source-regression evidence still to reconcile** |

The previously reported disposable Step 3L Btrfs rehearsal on `mars` exercised a protected parent, deletion and interruption recovery in a disposable namespace. Consult `../../reports/step03l-accelerated-rehearsal.md` and related source reports for its scope; **do not** substitute it for integrated cross-host executor acceptance.

## Still open

1. Finish the trusted authenticated source-held deletion session, receiver lock integration and journalled executor; keep privileged receiver deletion unavailable for now.
2. Run the pending protected-parent UUID-binding regression against current `mango` sources; reconcile integration tests and function signatures before deployment.
3. Validate success, interruption and recovery in disposable Btrfs test data; prove holds and source pin remain safe across failures.
4. Review design invariants and adversarial matrix against final integrated code before declaring Step 3 CLOSED. Later deployment, native pruning activation, and irreversible legacy retirement have their own separate acceptance gates.

**No production receiver snapshots deleted or authorised for deletion by these design tests.** The latest observed receiver plan was `total=19`, `retention_keep=19`, `candidate_count=0`, `executable=false`.

## 24 October 2026 — Production installation, idempotency and read-only receiver verification

**Scope of acceptance:** installation/operational safety verification for the *current Step 3 source*, not approval of production receiver deletion, activation of receiver pruning, closure of Step 3, or advancement past the later feature gates. This installation included previously developed Step 3 functional code as well as explanatory comments.

- **Source-control checkpoint:** operator's 23 October Git output showed Diaries `ab14f43f3604eeb31cfb8a6c2ce6a416c123eddc` and Playbooks `80eed96482628ef09050e3b9e4efc59c18e46963`, with clean working trees and tracking branches synchronised. The 24 October verification command also reported Playbooks `80eed96482628ef09050e3b9e4efc59c18e46963`. The operator subsequently edited the one-line check-mode correction on `mango`; the latest command's reported revision should be reconciled against the working tree before citing a final committed release identifier.
- **Python syntax:** all six `roles/{btrfs-replication,remote-backup}/files/btrfs-native-*.py` passed AST parsing on `mango` (23 October source-check log; no uncommitted changes at the time).
- **First dry run:** `ansible-playbook native-btrfs.yaml --vault-password-file ~/.vault_pass.txt --check --diff` predicted `mars changed=4`, `backup changed=3`, but *failed* at the dual-off-site-transport assertion because its read-only shell probe was skipped under check mode. This was **not** evidence of a live legacy rsync phase.
- **Safeguard reconciliation:** `mars` installed `/root/scripts/backup/backup.sh` has the legacy remote phase disabled; a direct grep returned `rc=1`. Effective inventory for `mars` resolved `legacy_remote_rsync_push_enabled=false`, `btrfs_native_push_schedule_enabled=true` despite opposite role defaults. The shell inspection task was corrected using `check_mode: false` alongside `changed_when: false`, preserving the assertion rather than bypassing it.
- **Passing check/diff:** rerun had `mars ok=15 changed=4 failed=0` and `backup ok=20 changed=3 failed=0`; dual-transport assertion and mandatory receiver hold/receipt assertions passed. Proposed changes were manager, endpoint and push/receiver-helper installs plus formatting-only rewrite of `mars` manager JSON. No reported changes to timers, retained snapshots, receipts, checkpoint-hold contents or retention values.
- **Actual deployment:** `mango` ran `ansible-playbook native-btrfs.yaml --vault-password-file ~/.vault_pass.txt`: `mars ok=15 changed=4 failed=0`, `backup ok=20 changed=3 failed=0`. A **second real playbook execution**, not just check mode, returned `mars ok=15 changed=0 failed=0`, `backup ok=20 changed=0 failed=0`; idempotency **PASSED**.
- **Installed code integrity:** SHA-256 of native endpoint on both hosts, sender on `mars` and receiver helper on `backup` matched `roles/btrfs-replication/files/` source on `mango` (four explicit `PASS` lines). The common `btrfs-snapshot-manager` on `mars` and `backup` matched the Playbooks source checksum `fe3fc7a9298f8a56b0a9f2b6e0197eddc64fe0142a496e19270714d5b7569f2c`.
- **Actual installed receiver configuration:** on `backup`, `/etc/btrfs-snapshot-manager.json` has `mode=receiver`, `receiver_prune_enabled=false`, repository `snapshot_root=/@data/mars-received`, `receiver_state_dir=/@data/mars-received/.replication-state`, and root-owned checkpoint holds required at `/etc/btrfs-receiver-checkpoint-holds.json`. `/etc/btrfs-receiver-retention.json` also has `mode=receiver`, `receiver_prune_enabled=false`. Earlier diagnostic attempted the *wrong* path `/etc/btrfs-snapshot-manager-receiver.json`; missing file was a verification-command error, not a failed install.
- **Read-only production recovery/inventory:** `receiver-recovery-plan` returned `CLEAN`, `authorizes_repair=false`. `receiver-inventory` verified **20 of 20** received snapshots/UUID receipts, `problems=0`; newest `20261024-030038Z` had source UUID `22e0ca45-0f49-c745-85b0-af6b6cfb915c`. Previously accepted checkpoint receipts `20261013-171228Z` and `20261018-165453Z` were present/verified; Ansible separately revalidated both mandatory checkpoint holds. The new 20th snapshot is evidence that normal unattended replication continues, but no manual post-deployment incremental was performed as part of this verification.
- **Scheduled transport:** `mars` `btrfs-native-push.timer` reported `enabled` and `active`. No command in this stage ran receiver pruning or deleted a production snapshot.

**Gate decision (24 October): ACCEPTED — non-destructive installation, real-run idempotency, installed-source parity and read-only receiver safety checks.** Step 3 as a whole **remains OPEN**. The above evidence does *not* establish production source-held deletion authority, successful interruption/repair across both hosts, or approval for candidate deletion. No fresh full restore or destructive rehearsal is necessary just to acknowledge this deployment.

### Evidence provenance

Operator terminal logs (24 October 2026), in chronological sequence: `note(20261024-062721).txt` (initial failing dry-run), `note(20261024-063019).txt` (legacy wrapper probe), `note(20261024-063200).txt` (Ansible task/inventory), `note(20261024-063857).txt` (passing dry-run), `note(20261024-064520).txt` (deployment), `note(20261024-064626).txt` (zero-change real rerun), `note(20261024-065058).txt` (four checksum matches/timer), `note(20261024-065208).txt` (manager checksum parity), `note(20261024-070327).txt` (configuration/recovery/20-snapshot inventory). These log filenames identify evidence supplied in the operator session; they have **not** been embedded in this documentation ZIP.

### Next implementation gate

Review the remaining Step 3 requirements against the deployed current Playbooks source, and reconcile the historical protected-parent UUID regression evidence. Then design and test the *production* trusted sender-held session, receiver manager/writer-lock ordering, confined privileged execution, timeouts/process-lifetime guarantees and journal recovery, first with a fresh source-level adversarial suite and disposable Btrfs state. Keep receiver pruning disabled until the full production coordination safety gate and explicit operator approval are satisfied. Avoid re-running an already accepted large destructive rehearsal unless a specific changed invariant requires it.

## Accelerated Stage 2 and design closure (24 October)

See `ACCELERATED-STAGE2-CLOSURE-20261024.md` and `../../IMPLEMENTATION-STEPS.md` Step 3 closure decision. The previous “Still open” and intermediate OPEN wording above describe the historical interim state, not the final Step 3 design-gate status. The full sudo regression suite passed; actual cross-host deletion was waived and is not evidenced. Production pruning stays disabled, and later activation/destructive gates remain separate.
