# Step 03 — Offline investigation planner adversarial regression acceptance

Date: 2026-10-21  
Scope: 0039-DEF / Step 03 (IN PROGRESS)  
Execution environment: Windows 11 Cygwin, local Diaries repository only.

## Original evidence and integrity

- Original terminal log: `planner-regression/note(20261021-151658).txt`, copied byte-for-byte.
- Integrity manifest: `STEP03-PLANNER-REGRESSION-SHA256.txt`; paths are relative to the **0039-DEF defect root**, not the Step 03 directory.
- Run: from defect root, `sha256sum -c 'evidence/Step 03/STEP03-PLANNER-REGRESSION-SHA256.txt'`.
- Applying this ZIP and verifying the log on the user's workstation are separate acceptance checks; the log's original bytes and hash are packaged here.

## Results directly supported by the terminal log

1. Python compilation of `plan-qgroup-investigation.py` and `test-plan-qgroup-investigation.py` completed without errors.
2. Both valid complete saved manifests (`backup` and `mars`) passed the planner baseline with deletion authorisation disabled.
3. All **12** adversarial cases produced controlled `PLAN UNAVAILABLE:` rejections: modified manifest classification, altered assessment counts, removed protected-ID attestations (including one protected ID), deletion authorisation enabled, injected deletion command, fingerprint mismatch, altered investigation sample, missing assessment counts, missing manifest sections, malformed JSON, and tampered filesystem identity.
4. The regression reported `PASS: original input evidence SHA256 unchanged`.
5. `git diff --check` ran without output and `=== REGRESSION COMPLETE ===` was printed.

The immediately preceding attempt (`note(20261021-151337).txt`) failed on an unhandled validator exception. The corrective package caught the independent validator's `ValidationError` and returned controlled `PLAN UNAVAILABLE:` rejection. The successful log establishes that this failure mode was corrected for the tested cases. The original failing run is historical evidence and should not be overwritten.

## Accepted scope and limits

**ACCEPTED:** initial offline planner functional baselines and its 12-case adversarial regression; no original source evidence was modified during tests. All planner output is non-executable and retains `deletion_authorized: false`, empty `deletion_commands`, and empty `executable_actions`.

**NOT ACCEPTED / NOT AUTHORISED:** independent live filesystem identity and manifest recapture, concurrent-change detection, receiver receipt / hold / protected-snapshot revalidation on live hosts, or a production deletion plan/executor. No qgroup deletion, snapshot deletion, quota rescan, replication change or other production mutation is authorised.

Step 03 remains **IN PROGRESS**, as does the overall defect. The disposable `mango` filesystem remains reserved for further safety testing pending explicit cleanup approval.
