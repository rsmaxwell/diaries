# 0028 Step 3 — Cygwin unittest.mock call compatibility correction

24 November 2026. Owner-approved maintenance input staging and the two live **read-only** pluto preflights passed. Of 25 local tests, 24 passed and one `test_docker_runner_uses_readonly_volumes` failed on the Windows Cygwin Python unittest.mock call-argument accessor. No production services, database, Files or snapshots were changed.

## Correction

Change the test-only expression `fake.call_args.args[0]` to the cross-version tuple form `fake.call_args[0][0]`. Under the Cygwin Python in use the former returned the literal `args` instead of the recorded Docker `argv`. No production command, one-shot runner or HBA control is changed.

## Verification in isolated source inspection

All 25 offline tests passed (9 maintenance, 7 receiver hold, 9 dry-run). The test continues to assert the production dry-run command uses the PostgreSQL container namespace, read-only responder volumes, read-only root filesystem, and no `apply` operation.

## Remaining gates

The prepared private inputs and live preflights have passed. The owner authorised **temporary isolation, creation/protection of fresh recovery points and dry-run only**; actual isolation has **not** been executed. Verify independent NAS Files writers are quiescent, and external IPv6 denial as required. Do not proceed to backup or dry-run until writer isolation is demonstrably complete. The 71-conversion apply, SQL journals, MQTT writes and destructive restores remain unauthorised.
