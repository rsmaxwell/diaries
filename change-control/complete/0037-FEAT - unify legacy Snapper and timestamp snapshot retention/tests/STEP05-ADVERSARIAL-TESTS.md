# 0037-FEAT Step 5 — Adversarial regression tests

**Status: IMPLEMENTED — awaiting execution on mango and evidence review; Step 5 OPEN.**

## Isolation and scope

`tests/step05-adversarial.py` loads the current snapshot manager **as a module**; mocked `preflight`, Btrfs/Snapper calls, native inventories, UTC time, pins, and holds are used. The suite does not call the command-line entrypoint, modify configuration, write snapshots, invoke Snapper deletion, or modify scheduler settings. Real temporary directories are Python-managed and removed on completion. Tests only require Python's standard library.

## Case matrix (20 tests)

- No legacy snapshots; legacy-only history and recovery anchor; native-overlap/natively retained floor; native-only unchanged.
- Separate `root`/`@data` source decisions; excluded manual/pre/post; minimum age; duplicate timestamps and deterministic tie-breaking.
- Incomplete native set; missing replication pin data; unavailable checkpoint holds; pinned and held native sets remain selected; no deletion action from plan mode.
- Empty Snapper configuration without `.snapshots`; nonempty configuration with missing `.snapshots`; duplicate numeric snapshot IDs; missing CSV columns; source identity mismatch; failed Snapper command; duplicate Snapper config mappings.

**Scope limits / mandatory later tests:** Step 5 exercises the **read-only planner**, not a legacy deletion path (which does not yet exist). A disappearing snapshot during per-delete revalidation, actual CLI deletion failure, and concurrent mutation must be re-tested in Step 6/7 when deletion logic is implemented, with mocked commands and simulated races. Do not represent planning tests as proof of destructive-path safety.

**Observed diagnostic limitation:** `Path.resolve(strict=True)` may raise a raw `FileNotFoundError` on a missing configured source. It fails closed (the plan aborts) but should be wrapped in a domain-specific `SnapshotError` for operator clarity in a later code-hardening change. No production source changes were made in Step 5.

## Local preparation and deployment of test-only file

1. Extract this ZIP into the existing **Diaries repository root** on Windows (`.../diaries/`). It places `step05-adversarial.py` within `change-control/in-progress/0037-FEAT - unify legacy Snapper and timestamp snapshot retention/tests/`.
2. In WinSCP, use the **mango tab**. Create `/tmp/0037-feat-step05/` (owned by `richard`) and copy `step05-adversarial.py` from the above Windows feature `tests/` directory into it. Do not copy it into `~/playbooks` or onto mars/backup.
3. In the already-open **mango SSH terminal**, execute:

```bash
mkdir -p /tmp/0037-feat-step05
python3 /tmp/0037-feat-step05/step05-adversarial.py \
  /home/richard/playbooks/roles/snapshots/files/btrfs-snapshot-manager.py \
  2>&1 | tee /tmp/0037-feat-step05/results.txt
```

If using a pipeline, confirm Python status using `set -o pipefail` before the test command (or `echo "${PIPESTATUS[0]}"` directly after the pipeline). Expected: **Ran 20 tests ... OK**.
4. In WinSCP, download `results.txt` into the Windows feature `evidence/Step 05/` directory (not Git-tracked raw production evidence). Optionally record the tested Playbooks Git revision (`git -C ~/playbooks rev-parse HEAD`) and source checksum (`sha256sum ~/playbooks/roles/snapshots/files/btrfs-snapshot-manager.py`).
5. After verifying the evidence was copied, from the **mango** terminal remove `/tmp/0037-feat-step05` using `rm -rf -- /tmp/0037-feat-step05` (only this explicitly named disposable test directory).

No other host needs commands; do not deploy a new manager for this step.
