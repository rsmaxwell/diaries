# Step 03 — Offline qgroup assessment and historical-pattern investigation

**Observed:** 2026-10-21. **Status:** Step 03 IN PROGRESS; defect OPEN. All work described here is diagnostic and non-mutating. No deletion eligibility is asserted.

## Accepted safety assessment (offline saved evidence)

The assessor from Playbooks `roles/snapshots/files/assess-qgroup-safety.py` was applied locally against the previously validated full JSON manifests and filesystem identity evidence, with separately verified protected snapshot IDs. Operator output `note(20261021-133241).txt` records PASS on both hosts. The independent local reconciliation in `note(20261021-133351).txt` verified the source manifest fingerprints, counts, category totals, false deletion flag and empty deletion command array.

| Disposition | mars | backup |
| --- | ---: | ---: |
| Active excluded | 140 | 131 |
| Explicit protected active snapshots | 6 | 3 |
| Limited excluded | 24 | 13,962 |
| Unmatched — investigation only | 21 | 15,475 |
| **Total** | **191** | **29,571** |

Saved report paths in the *operator's existing Windows checkout* (not recreated in this package):

- `assessment/mars-qgroup-safety.json` — SHA256 `b0f6500349279ae0727db4448b45c74e3321b0f1a36083280db48a913284e20f`; manifest fingerprint `84655523aaaf069a7f9501fe9c8e6bbc07997a8932dc4259757df153c9f1f9e3`.
- `assessment/backup-qgroup-safety.json` — SHA256 `b7052fcf71f376981d3da86e2d70603da3dd834a3478dd8884ea6bab1201fdcf`; manifest fingerprint `dd2f90fa766164e17a38ca665b11a1f188559f33353a66536845a6fc196f8bd1`.

Both reports contain `result=PASS`, `deletion_authorized=false`, and an empty `deletion_commands` list. Source regressions including adversarial, syntax, 31,002-record test and existing validator/audit suites passed on `mango` (`note(20261021-133007).txt`). CLI contract inspected (`note(20261021-133113).txt`). Nine explicitly protected subvolume IDs were verified as active qgroups; this explicit list is not an exhaustive set of retention/replication constraints.

## Historical ID distribution (read-only offline evidence)

Operator outputs `note(20261021-134054).txt` and `note(20261021-134225).txt` inspected the original saved manifests, without modifying them.

- `mars`: 45 unmatched, of which 21 without limits and 24 with limits, ID range 20189–20922.
- `backup`: 29,437 unmatched, of which 15,475 without limits and 13,962 retaining quota limits, ID range 276–55746.
- On `backup` the ID bands 27000–40999 each contain 1,000 unmatched entries. Many later bands are nearly full. Across these bands the two classifications are **interleaved**, not separated into early/late blocks: e.g. 27000–27999 has 526 unlimited and 474 limited; 53000–53999 has 571 unlimited and 427 limited.
- Last reported unlimited IDs: 55728, 55730, 55732, 55734, 55736, 55738, 55740, 55742, 55744, 55746. Last limited IDs: 55727, 55729, 55731, 55733, 55735, 55737, 55739, 55741, 55743, 55745.

**Inference, not verified root cause:** broad contiguous IDs and the near-end odd/even alternation are compatible with repeated historical subvolume-pair creation followed by deletion and surviving qgroup records. The current evidence neither identifies the creating program nor establishes why limits were retained or how old Btrfs behaves during qgroup destruction. Btrfs subvolume IDs are not timestamps. Zero reference usage and missing active subvolume IDs do not grant safe deletion status.

## Source inspection (mango, no runtime mutation)

- `note(20261021-133510).txt`, `note(20261021-133612).txt`: snapshot manager `prune()` validates entire deletion set and retains replication pins and checkpoint holds. Before `btrfs subvolume delete`, it obtains and logs an exact native subvolume ID. No explicit qgroup removal follows. `create_all()` rollback separately deletes already created snapshots (`note(20261021-133853).txt`); this is **not** routine pruning.
- `note(20261021-133742).txt`, `note(20261021-133853).txt`: receiver uses `btrfs receive`; an unsuccessful receive leaves an unaccepted destination for manual inspection, not automatic deletion. Receiver protection updates share the manager lock. Native receiver's failure path is therefore not proven to account for the historical backlog.
- The exact mechanism and creating/deleting workflows underlying 29,437 unmatched `backup` entries remain **unresolved**. Source inspection alone is insufficient to assign causality to the currently installed manager or historical Snapper/backup tooling.

## Original terminal evidence — unchanged bytes

- `investigation/note(20261021-133007).txt` — SHA256 `7f1abc54494faccef3b58afa346d84b8a204fba19a5a641da8c07d030667227b`
- `investigation/note(20261021-133113).txt` — SHA256 `e0fc01926a322c368d54d6cf9fb8b1588678403045d079fe8a5c3a9384e40e9b`
- `investigation/note(20261021-133241).txt` — SHA256 `7db302e7a07aa8aae22d32c8f2bb54bf1d942a84e672f400492ee5fba6065ffd`
- `investigation/note(20261021-133351).txt` — SHA256 `06b4ae7f517308affee5eeb59cae7d96cf9bdc4843c634357f971ce559e0cd7a`
- `investigation/note(20261021-133510).txt` — SHA256 `73470770102c13e809f34c526cf9540edb5afb78af72f8c16cb2fc8e73078743`
- `investigation/note(20261021-133612).txt` — SHA256 `7f11d7c7042ac1397187a3a50f8e2c395c65a2c3015434ab9dd108cbaaee30a4`
- `investigation/note(20261021-133742).txt` — SHA256 `c48015ed02314cf6858040078f0e11deb183b9176e9d0694c98a5f7350da0f55`
- `investigation/note(20261021-133853).txt` — SHA256 `f79c38e72f013be1ff05ac43a617480fb6422d8ffe5104e614a2af4c1eb3ee4e`
- `investigation/note(20261021-134054).txt` — SHA256 `201406d53bd2bb26e8bdd52ed329d607677265f491c81aa23d69f4b941b53c5a`
- `investigation/note(20261021-134225).txt` — SHA256 `e4ed1f3deb342bb4164b3f78d75adfdfcbcd08a4a73c4ba2ed3fb6f7a1f9b70f`

The original receiver/protection evidence and verified manifest/identity/report JSON remain in their already-established Step 03 folders. The ZIP includes no replacement copies of the large or local reports.

## Remaining acceptance gates and restrictions

1. Complete read-only examination of specific recent adjacent qgroups (especially limit values and usage) and compare with historical creation/retention source evidence. Do not infer deletion eligibility from adjacency or from category alone.
2. Document supported Btrfs utility/version behaviour, historical attribution confidence, a prevention-of-recurrence approach and distinct historical reconciliation design.
3. Define a fresh live identity/protection/quota/replication preflight, non-atomic inventory limitations, irreversible rollback implications and explicit operator approval **before** any potential mutation. Review OS upgrade separately from qgroup actions.
4. Close Step 03 only after its documented acceptance criteria are met. Do not imply this evidence approves cleanup, rescan, quota disable/enable, snapshot deletion or a replication change.

## Subsequent confirmed evidence — 2026-10-21

Historical Snapper snapshot pairing and the disposable limited/unlimited stale-qgroup reproduction are recorded, with original terminal logs and SHA256, in `STEP03-STALE-QGROUP-REPRODUCTION.md`. The original paired-workflow theory is now **strongly supported** by seven verified surviving pairs, and the symptom is reproducible on `mango`. The precise production persistence mechanism and deletion eligibility remain unconfirmed.
