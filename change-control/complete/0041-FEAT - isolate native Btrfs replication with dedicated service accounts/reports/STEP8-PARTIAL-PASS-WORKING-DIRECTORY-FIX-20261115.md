# 0041-FEAT — Step 8 partial success and working-directory fix (2026-11-15)

Evidence reviewed: Windows terminal log `note(20261115-143352).txt`; on-disk evidence is recorded at `evidence/Step 8/security-idempotence-20261115-143318Z.txt` in the Windows Diaries repository.

## Passed in live environment

- `mars` sender and `backup` receiver groups and login shells satisfy the service-account restrictions.
- Receiver `authorized_keys` contains one root-managed restricted key and cannot be edited by its service account.
- Both accounts reject arbitrary sudo and reject arguments to the fixed privileged helper; `visudo` succeeds.
- Dedicated SSH read-only status verifies the receiver agreed parent (`relation=equal`).
- The forced-command dispatcher rejects arbitrary `id`, shell requests, bootstrap, shell operators, and path traversal (all exit 64).

## Stopped before completion

At the Ansible idempotence stage, the script executed:

```bash
cd /home/richard/ansible-controller
source ./enter.sh
cd playbooks
```

`enter.sh` already changes the current directory to `/home/richard/ansible-controller/playbooks`. The final relative `cd playbooks` consequently fails with `No such file or directory`, before Ansible is invoked. The final service/timer comparison was not reached.

The revised script uses `cd /home/richard/ansible-controller/playbooks` after sourcing `enter.sh`, matching the established Step 7 deployment pattern.

## Status and follow-up

**Step 8: PARTIAL PASS, OPEN** pending re-run of idempotence (`changed=0` on both hosts) and post-run service/timer/candidate-inactive checks. The preceding security test evidence is valid; the re-run is for a consolidated acceptance log, not because those checks failed.

No Btrfs transfer, snapshot deletion, agreed-parent alteration or production service cutover occurred in this failed Step 8 run. Retain the prior raw log; do not overwrite historical evidence.
