# 0040-FEAT — Step 12 guarded journal retirement and cutover script prepared

Date: 6 November 2026. Status: **PREPARED; NOT EXECUTED ON PRODUCTION**. Step 12 remains OPEN.

## Inputs and current evidence

The 6 November mars/backup read-only audits both passed. The receiver has a published, read-only candidate `20261030-170009Z` and a legacy receipt, but their exact receipt lineage requires the *revised* audit (not yet returned from production). The initial parent `20261101-140039Z` was verified read-only at both endpoints with source UUID `69ef9a57-50ff-9a4e-92ed-8f10560ab1f2`. The receiver legacy journal SHA-256 remains `e11483fe05c482894c2db6fc15ffa63164f6b9c3da831508e0a2990123b9f3f2` according to that earlier audit. Only the fresh preflight can confirm it still matches.

Installed simplified executable version expected on both endpoints: `9be64295a6b6807df0fcd33d924b7a6549959f2a03dcab2953dcf0ac77fa6297` (accepted previous install). Sender/receiver state files are not yet bootstrapped. Receiver pruning must remain disabled.

## Consolidated feature-local change

The `tools/step12-controlled-cutover.sh` standalone Windows Cygwin Bash script offers two modes: read-only `preflight` and fail-closed, state-changing `execute`. `execute` rechecks all preflight conditions before touching live state. It checks the real received UUID and valid receipt, archive journal digest, absence of staged data and source service inactivity before archiving. It bootstraps through the existing installed simplified sender and attempts one controlled transfer. It refuses unattended reactivation; that requires an independently reviewed Ansible check-mode result and subsequent actual Playbooks deployment.

The script streams `tools/step12-legacy-journal-transition.py` over SSH, preserving the authoritative Windows repo and avoiding synchronisation to mango for these one-off operations. Logs are written to `evidence/Step 12/raw-logs` inside the feature directory.

## Verification performed on generated artifact

- `bash -n tools/step12-controlled-cutover.sh`: PASS (syntax only).
- `python3 tests/verify-step12-legacy-journal-transition.py -q`: PASS, 17 isolated fixtures (from revised journal utility).
- Source inspection of the latest supplied `playbook-sources-20261106-111342.zip`: simplified sender `bootstrap` and `cycle` semantics and active systemd service template confirmed. This is not a production test.

No SSH commands, journal rename, bootstrap, send/receive, Ansible playbook or reboot has been performed by this preparation.

## Outstanding acceptance evidence

(1) Actual preflight stdout/stderr with exit code 0 and exact accepted receipt SHA; (2) successful guarded journal archive with checksum and root-only rollback path; (3) equal initial source and receiver parent state; (4) successful single live sender cycle and equal advanced parent/prior; (5) checked Playbooks preview followed by authorised deployment and timer/service readback. If a gate fails, preserve logs and stop rather than bypass the guard. Receiver pruning remains a separate acceptance gate.

## 6 November — first Windows preflight, correction pending live verification

Windows and mango pulled main `220672e`. Windows initially clean; mango has five untracked Step 12 raw logs that must be retained. `bash -n` succeeded. The read-only preflight confirmed source snapshot B and no source simplified state, but stopped when the overly strict migration auditor rejected the historical candidate receipt (generic lineage/transport error). No live mutation occurred.

Review of the uploaded legacy `btrfs-native-push-receiver.py` established that its accepted-receipt contract supports full or incremental transport and does **not** assert the journal parent equals a previously published receipt parent. The corrected feature-local auditor checks the receipt independently, preserves source/receiver UUID, filesystem, destination, success/read-only and checksum guards, and reports historical receipt ancestry. The resulting preflight must still pass against live production data; this report does not claim it has passed.
