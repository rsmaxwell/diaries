# Step 03 — Shared Btrfs manager and guarded receiver deletion design

**Status: OPEN — intermediate design, non-destructive implementation and validation evidence consolidated as of 23 October 2026.** The original `../reports/STEP03-DESIGN-START.md` says no source/production modifications; that sentence describes the *start* of Step 3, not the current state. This register records subsequent work without prematurely closing Step 3.

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
| Parent UUID binding | Source package / tests proposed after hold verification; latest transcript does **not** show a 5/5 regression on `mango` or deployment | **Pending verification** |

The previously reported disposable Step 3L Btrfs rehearsal on `mars` exercised a protected parent, deletion and interruption recovery in a disposable namespace. Consult `../../reports/step03l-accelerated-rehearsal.md` and related source reports for its scope; **do not** substitute it for integrated cross-host executor acceptance.

## Still open

1. Finish the trusted authenticated source-held deletion session, receiver lock integration and journalled executor; keep privileged receiver deletion unavailable for now.
2. Run the pending protected-parent UUID-binding regression against current `mango` sources; reconcile integration tests and function signatures before deployment.
3. Validate success, interruption and recovery in disposable Btrfs test data; prove holds and source pin remain safe across failures.
4. Review design invariants and adversarial matrix against final integrated code before declaring Step 3 CLOSED. Later deployment, native pruning activation, and irreversible legacy retirement have their own separate acceptance gates.

**No production receiver snapshots deleted or authorised for deletion by these design tests.** The latest observed receiver plan was `total=19`, `retention_keep=19`, `candidate_count=0`, `executable=false`.
