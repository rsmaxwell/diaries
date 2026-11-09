# 0040-FEAT Step 12.3 — Private-name receive experiment (test only)

This experiment determines whether a Btrfs incremental send stream can be received
under a private name **directly in the intended publication parent**. It deliberately
changes only the PATH attribute of the first Btrfs SNAPSHOT/SUBVOL send command and
recomputes that command's CRC32C. It does **not** alter the sender snapshot's UUID
or creation-transid, the incremental parent's identifiers, or subsequent commands.

This test is NOT an operational stream transformer and must never be installed in
production. It buffers the disposable test stream in RAM and is not hardened for
untrusted large or malformed streams. A production implementation would require a
strictly bounded streaming parser, full command validation, authentication binding,
a transaction-safe journal transition and revised staging layout/discovery rules.

## Test (SSH terminal to `mango`)

In `/home/richard/playbooks`:

```bash
(
  python3 roles/btrfs-replication/tests/verify-0040-step12-3-private-stream-name.py &&
  sudo -n python3 roles/btrfs-replication/tests/verify-0040-step12-3-private-stream-name.py --run &&
  git diff --check
)
if [ "$?" -eq 0 ]; then
  echo 'PASS: disposable private-name Btrfs receive experiment'
else
  echo 'FAIL: disposable private-name Btrfs receive experiment'
fi
```

`--run` requires root, btrfs-progs and loop mounts. Creates two *new* 512-MiB
sparse filesystems in its own temp directory. It does not access any production
mount, snapshot, journal, keys, timer or replication service. It creates baseline
snapshot A and incrementally sends B to a private dot-prefixed name under the
same destination parent, verifies the final B timestamp is **absent throughout
receive**, checks received UUID, readonly state and payload, then performs
same-parent `RENAME_NOREPLACE` publication and rechecks identity.

If cleanup cannot unmount its images, it preserves the temporary working directory
and raises an error; investigate the displayed path before manual removal.

### Acceptance boundary

A successful result demonstrates *filesystem/stream feasibility only*. It does
not establish the trustworthiness of rewriting arbitrary send streams or the
safety of a new deployed receive pipeline. Current direct/scoped-direct runtime
and the 03:30 timer must remain unchanged. Keep 0040 Step 12.3 OPEN.

Specification reference: https://btrfs.readthedocs.io/en/latest/dev/dev-send-stream.html
