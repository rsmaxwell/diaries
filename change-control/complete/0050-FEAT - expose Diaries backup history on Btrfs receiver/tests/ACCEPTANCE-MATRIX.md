# 0050 — Receiver Diaries backup history acceptance matrix

**Current status:** FORMAL CLOSURE APPROVED; required acceptance results recorded; Steps 1–4 CLOSED. Final archival GitHub publication is pending execution of the guarded closure helper.

| ID | Required result | Evidence |
| --- | --- | --- |
| BL-01 | Source/receiver/controller Git revisions and dirty state, deployed scripts/config and timer state captured before change | Windows + mango + mars/backup baseline logs, submodule status and installed hashes |
| DV-01 | Receiver retains `mode=receiver`, `verification.required=false`, existing retention, locks, holds, parent/prior and security | Before/after JSON and read-only manager status/plan; negative regression that enabling source-verification is not attempted |
| IN-01 | Both commands installed root-owned and executable on `backup`, verifier installed in safe root-owned location | Installed file hashes and owner/modes; Ansible source/deploy manifest |
| IN-02 | Source `mars` commands remain installed and behave unchanged | Source CLI fixture, text/JSON read-backs, installed hashes |
| HI-01 | Receiver history reads `/@data/mars-received/@data/<stamp>/backup/...` locally, never source `/media/usb` or SSH | Fixture and receiver live path read-back; mocked/monitored zero network calls |
| HI-02 | Receiver-only backup ID appears only in receiver inventory, with correct identity, retained occurrence count and first/last stamps | Disposable two-repository fixture plus optional naturally retained real receiver-only ID |
| HI-03 | Both reader and status preserve existing grouped/`--all`, `show`, `path`, `--snapshot`, `--logical-dataset` output and JSON schema | Text and machine-readable test matrices, selected receiver-local path |
| HI-04 | Verified marker must be eligible and identity/hash match manifest; broken/unsafe paths rejected, warnings cause degraded/nonzero, no silent skip | Tampered marker, symlink, invalid JSON, missing manifest and bad SHA fixtures |
| HI-05 | Same `(logicalDataset, backupId)` across snapshots with differing manifest SHA-256 is reported as conflict and cannot be silently verified/selected | Conflicting-occurrence fixture, status `health=degraded`, specialist nonzero exit |
| HI-06 | `verify` invokes independent real schema-2 verifier over receiver's selected backup files and propagates success/failure; no writes | Disposable verifier-invocation fixture plus selected live received backup verification and pre/post checksums/state |
| HI-07 | Empty local received inventory reports labelled empty result and no fabricated source backups | Empty fixture, text/JSON/exit code |
| HI-08 | Status JSON remains narrow Diaries-only with valid indented JSON and expected health 0/1/2; warnings/error to correct channel | Existing and new permanent regressions, fixture stdout/stderr assertions |
| SE-01 | No widening of 0041 dedicated SSH accounts, forced command, sudoers, Btrfs receive permissions or endpoint access | Role diff and 0041 negative/security tests |
| SE-02 | No source snapshot verification/scheduling/retention/replication change; receiver prune preview selects identically before/after | Source/receiver read-only reports, parent/prior/hold identities and dry-run comparison |
| OP-01 | Full relevant Playbooks unit/source regressions, Ansible syntax/check, receiver deployment and strict idempotence (`changed=0`) accepted | Raw consolidated tests, Ansible output/recap, receiver command and verifier read-backs |
| OP-02 | All code committed/published in Playbooks; controller pins correct submodule; final Diaries records/rollback/closure | Three-repo Git revisions, state and publication receipts; formal closure approval |

## Fixture guidance

The feature-specific `verify-0050-receiver-history-fixtures.py` creates independent temporary source/receiver repositories and simulates a receiver-only backup, warnings and conflicts. It failed as expected against the unmodified 0049 reader and all nine cases now pass with the proposed 0050 reader. Its temporary verifier stub proves dispatch/exit propagation **only**; `verify-0050-real-schema2.py` additionally invokes the real schema-2 verifier against a valid disposable received dataset, then deliberately changes a file and requires verification failure. The latter test does not use or mutate production datasets. Do not modify production retention to create a receiver-only test case.

## 17 November 2026 live acceptance update

- **IN-01, HI-01, HI-03 (list/status), HI-05, SE-02 (infrastructure read-back):**
  corresponding live receiver observations are passing; defer formal acceptance
  of the full criteria until all required associated evidence is reviewed.
- **HI-06:** **NOT ACCEPTED** on the initial receiver deployment. Full `verify`
  exited 2 because `diaries-backup` was passed as a UTC-ID-named directory.
  Minimal fix implemented and real verifier tests passed against disposable
  fixed-directory, generation and tampered bytes; repeat live verification.
- **OP-01:** initial deployment successful, strict post-fix idempotence pending.
- Do not mark any step CLOSED or claim end-to-end verification until successful
  live re-read and the remaining acceptance gates.

## 17 November 2026 — Final operational evidence update

- **HI-02 receiver-only case:** **PASS**, now backed by production observation of 11 naturally retained receiver-only backup identities (not just fixtures). 19 were shared; 3 were source-only.
- **HI-06 full verification:** **PASS**, independent schema-2 verification on `backup` checked 128 files for `production/20261116-003112Z` in snapshot `20261116-150008Z`; existing fixed-root correction resolved the prior failure. Full verification was not performed against each of the 11 receiver-only IDs.
- **OP-01 receiver deployment/idempotence:** **PASS**, Ansible reapply `changed=0 failed=0`, following earlier `changed=1` corrected-reader installation; source, security and compatibility regressions passed.
- **OP-02 repository publication and formal closure:** **PENDING**. Do not claim published revisions or move the feature until publication receipts and explicit closure approval.

See `reports/FINAL-OPERATIONAL-ACCEPTANCE-20261117.md`, verbatim idempotence/history log and its SHA-256 receipt. Prior dated status notes remain as historical checkpoints, now superseded by this update.

## 17 November 2026 — Operational repository publication update

- **OP-02 Playbooks publication:** PASS. Initial source commit `a1f27ddf20e6c9668c6ad8f0d801de0233695ccc`; final `100755` executable-mode-only correction `b0063d455faf4b264504405f9db72ab21c692741`. Both remote revisions verified.
- **OP-02 controller pin/publication:** PASS. Controller `28e394b48ba91479b147452d70adb39ff3b84559` pins `b0063d455faf4b264504405f9db72ab21c692741` and retains private inventory `ebcce026723db37b9b53b76ba21903a351d48466`. Remote SHA verified.
- **OP-02 Diaries publication/formal closure:** PENDING. Preserve original publication logs and do not label the feature CLOSED until all change-control records are published and the feature owner explicitly approves closure.
- Production behaviour, previously accepted full content verification and strict Ansible idempotence remain unaffected by the Git file-mode-only change.

## 17 November 2026 — Formal closure acceptance (supersedes earlier gates)

- **BL-01, DV-01, IN-01–02, HI-01–08, SE-01–02 and OP-01:** accepted PASS based on source/receiver configuration inspection, regression/negative tests, live command readback, real schema-2 full verification of 128 files, and strict Ansible reapply `changed=0 failed=0`. Preserve the original failure-stage logs as historical evidence.
- **HI-02:** accepted PASS with 11 real receiver-only identities (19 shared, 3 source-only) and disposable fixture coverage. The 11 were **not** all individually content-verified; no claim of that kind is made.
- **OP-02:** Playbooks, Ansible-controller and Diaries evidence publication verified by remote SHA readback. Formal closure approved on 17 November 2026. The final archive relocation/closure commit remains a guarded execution action, and its SHA is determined only when published.
- **Step status:** Steps 1, 2, 3 and 4 accepted **CLOSED**. Closure record: `reports/FORMAL-CLOSURE-DECISION-20261117.md`.
