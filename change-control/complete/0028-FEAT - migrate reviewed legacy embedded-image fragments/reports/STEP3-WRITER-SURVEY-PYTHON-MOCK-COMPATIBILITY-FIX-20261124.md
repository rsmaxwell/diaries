# 0028-FEAT — Step 3 offline test compatibility correction

Date: 2026-11-24  
Status: Patch prepared; Windows live re-verification pending.

## Observed result

The user ran `tools/verify-0028-step3-retained-restore-and-writers.sh` on Windows/Cygwin. Offline regression tests finished with 18 passes and one failure, before SSH or Docker restore actions:

```text
FAIL: test_writer_sql_queries_actual_postgres_container
AssertionError: 'arg' != ['docker', 'exec', 'diaries-postgres']
```

`unittest.mock`'s newer `call_args.args` property is not portable to the user's Cygwin Python. The test accidentally treated the attribute-name `arg` as a command. The actual production writer-survey code still targets `diaries-postgres` and has not failed a live SQL query in this attempt.

## Correction

In `tests/test_step3_retained_restore_and_writers.py`, change the argument inspection from `runner.call_args.args[0]` to `runner.call_args[0][0]`. Both forms inspect the same mock call in modern Python, but the latter uses the long-supported tuple interface.

No writer survey, retained restore implementation, Docker command, backup configuration or production code is changed.

## Acceptance boundary

Run the existing one-shot Step 3 script from the Windows Diaries parent repository. The prior invocation stopped before its remote survey or creation of a disposable restore container or volume. Keep the script's existing fail-closed checks. A passing offline suite alone does not prove the retained database backup restores; the actual restore and production writer discovery remain pending.

Production migration remains unauthorised.
