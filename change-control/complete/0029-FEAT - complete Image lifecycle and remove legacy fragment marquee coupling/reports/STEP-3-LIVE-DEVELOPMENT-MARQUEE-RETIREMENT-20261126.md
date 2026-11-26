# 0029-FEAT — Step 3 live development Marquee retirement runbook (2026-11-26)

**Status:** PREPARED — not executed. Production is out of scope.

## Basis and accepted evidence

- Full responder Gradle tests: `BUILD SUCCESSFUL` (2026-11-26 12:16).
- Isolated PostgreSQL 18 rehearsal (2026-11-26 12:20): 2,269 Marquees, guarded retirement PASS, rollback rebuilt all 2,269 rows PASS, second retirement PASS. Read-only source development database unchanged.
- Forward SQL SHA256 `758a41e5ecdddd895827865b35edd362edb4dd56d12a51f845fc515a9b735931`.
- Rollback SQL SHA256 `b629dcfe85f6525f5c3a0a7b3c8308b7f88432e23e1b22d5833b7bf2feba244a`.

## Operator sequence — Windows PC, Cygwin Bash, Diaries root

Run the read-only preflight first:

```bash
cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries
bash 'change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling/tools/run-step3-live-development-marquee-retirement.sh' --plan
```

Inspect the log. Before write execution, close the local Editor and Reader sessions and **stop the local IDE responder**. Confirm that no other application processes write to the development database. Do not stop the development PostgreSQL container. Development-only execution requires explicit approval and attestation; from the same Cygwin terminal, once approved:

```bash
DIARIES_0029_RESPONDER_STOPPED=YES_IDE_AND_DOCKER_STOPPED \
DIARIES_0029_STEP3_APPROVED=YES_DEVELOPMENT_MARQUEE_RETIREMENT \
bash 'change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling/tools/run-step3-live-development-marquee-retirement.sh' --execute
```

The script checks the source database identity, schema, ownership, migration SQL hashes, captures a fresh verified custom-format backup plus TOC and checksum, executes the guarded SQL, and checks that the record count and ownership remain unchanged. It writes the log and dump beneath `evidence/step-3-live-development-marquee-retirement/`. **It never performs a production operation.** The IDE responder cannot be independently detected, hence the mandatory human attestation.

## Manual integration verification after successful database step

Start **only the updated** `diaries-responder` IDE process and examine logs for startup exceptions, `Synchronise` completion, MQTT publish/subscribe errors, and Marquee/Fragment owner resolution. Verify Editor and Reader in development. Cover existing Page Marquees and IMAGE/TEXT editing, creation and deletion using disposable test records only; verify annual PREAMBLE read/display without deleting historical content. Record screenshots, responder logs, MQTT retained topics and any failures in this feature evidence directory. Confirm the development DB no longer contains `marquee.page_id` and that owners still resolve by Fragment. Do not mark Step 3 CLOSED based on SQL success alone.

## Rollback and failure handling

If SQL fails, **do not start the responder**. Inspect the transaction outcome and retained backup. The forward SQL is transactional, so a failing guarded operation should roll back; independently verify the actual schema before proceeding. If SQL succeeds but the updated responder fails, stop it and investigate. The guarded `tools/step3-restore-marquee-page-id.sql` can reconstruct the redundant column in the development database **only after approval and after all application writers have stopped**. That script was successfully tested in isolation, but running it live is a separate explicit decision. To return fully to the old responder contract, verify application version compatibility, migrated data, and MQTT retained state; restoring the column alone does not reverse Step 2. A full database restore from the fresh `.dump` is a fallback requiring explicit approval, not an automatic step.

## Gates still open

- Live development cutover and integration GUI/MQTT checks.
- Coordinated production migration readiness, backup, and release approval.
- 0029-FEAT remains in progress; production untouched.
