# 0040-FEAT Step 11 — Final operational acceptance (26 October 2026)

**Decision:** Step 11 operational execution **ACCEPTED**. **Formal Step 11 closure pending archival of required raw evidence and master acceptance-record update.** Steps 12–14 remain OPEN. This addendum deliberately does not overwrite the current locally edited `IMPLEMENTATION-STEPS.md`.

## Retirement results already accepted

- `backup`: 115 legacy Snapper snapshots retired (two pilots plus 113 manifest entries); obsolete containers, Snapper configuration and hook retired. Receiver recovery `CLEAN` and receiver pruning disabled. See `reports/STEP11-BACKUP-RETIREMENT-ACCEPTANCE-20261025.md` and Step 10 evidence archive.
- `mars` legacy Snapper: approved 17-target manifest SHA-256 `643c3dff637be45da4188f9991a2bddb27a8bb894d474aebd2318c5ebfa412b4`; subsequent inventory found no `@data/.snapshots` directory or nested Snapper subvolumes. Historical batch and cleanup evidence is archived under `evidence/Step 10/0040-step10-evidence/`.
- `mars` native `root`: operator specifically authorised deletion of 63 UUID-verified snapshots. Durable receipt reconciliation found one `BEGIN`, 63 `DELETE_INTENT`, 63 `DELETED` and one `COMPLETE`. No remaining root snapshot paths/subvolumes. Original replication service restored; native push and both snapshot timers active. Receipt `/media/usb/@snapshots/.0040-step11-root-retirement-receipt.jsonl` SHA-256 `e75e5c57f5a99524d37dccca2c8c9982a1e22b32e011b9bd95f132901cc8c955`.
- Snapshot manager on `mars` has only `@data` source; both historical holds retained; 0 incomplete timestamp sets, valid production Diaries marker; check-mode idempotency `changed=0 failed=0` for snapshot and replication Playbooks; receiver recovery `CLEAN`.

## One-time APT-hook retirement on mars

- Authoritative one-off playbook: `tools/step11-retire-orphaned-snapper-hook.yaml` in this feature (execution copy on mango at `/home/richard/change-control-temp/step11-retire-orphaned-snapper-hook.yaml`). Not installed in permanent production roles.
- Initial `--check --diff` (26 October) passed, showing the expected rollback-copy creation and APT-hook removal (`changed=2 failed=0`).
- Actual run passed safety assertions, preserved rollback and removed `/etc/apt/apt.conf.d/80snapper` (`changed=2 failed=0`).
- Repeated `--check --diff`: `changed=0 failed=0`; `sudo apt-get check` succeeded; runtime hook absent, 0 incomplete native snapshot sets, Diaries verification valid, three timers active.
- Independently verified rollback file: `mars:/home/richard/80snapper.0040-step11-before`, `root:root`, mode `0600`, 734 bytes; SHA-256 `a528b866c08ab0d52fef043129267c996a78ead2ee97bae0ee86e4aace79a967`.

## Permanent Step 10 evidence transfer

- 135 non-bytecode source files copied from `/home/richard/0040-step10-evidence` on mango to Windows Diaries `evidence/Step 10/0040-step10-evidence/` with WinSCP. The sorted multiset of 135 SHA-256 content hashes matched; the full pathname comparison was not passed because of the extra wrapper directory and Cygwin `sha256sum` filename formatting. The source folder was subsequently deleted through WinSCP, visually confirmed.
- The bytecode file in `__pycache__` was excluded from the hash comparison. Verify repository inclusion/commit separately.

## Outstanding documentation and archive gates

1. Copy the Step 11 retirement receipt from `mars` into `evidence/Step 11/`, verify its SHA-256 exactly matches the digest above and retain the source receipt.
2. Preserve raw Step 11 terminal logs (including explicit authorisation, commit execution, receipt reconciliation, service restoration, Ansible `--check --diff`, cleanup deployment and idempotency) and root-retirement manifest/regressions. Record actual repository/source revisions rather than inventing them.
3. Review this addendum against the most recent locally edited `IMPLEMENTATION-STEPS.md` before recording the formal **Step 11 CLOSED** decision. Never use this historical addendum to activate receiver pruning.

## Explicit exclusions

- New offsite replication after retirement was not independently observed in the supplied evidence. The next normal native push was scheduled for 27 October 2026 03:30 UTC; no forced transfer is required to accept the destructive retirement already verified.
- `mars` stale qgroups rose to 359 by final cleanup verification; this remains in **0039-DEF**, which stays `in-progress`.
- Receiver pruning remains disabled pending 0040 Step 12 safety and approval gates. Feature 0040 as a whole is not closed.
