# Step 3 — Private process-group cleanup and bounded source pin

Status: source implementation / local regressions passed; **not deployed**.

## Implemented

- Private child process starts in its own process session and is terminated by process-group signals on deadline, abort, and cleanup. This covers a descendant that inherits stdout and outlives the immediate parent.
- Default private source-pin renewal uses `subprocess.run(..., timeout=...)` and retains existing persistent protection on failure.
- Child process group is reaped under the held source lock; no new CLI or privileged receiver endpoint is enabled.

## Local evidence (2026-10-23)

- Existing sender-process-lifecycle tests: 5/5 PASSED.
- Existing sender-private-transaction-deadline tests: 6/6 PASSED.
- New process-group and bounded source-pin tests: 5/5 PASSED.
- All tests use disposable local child processes, not production `mars` or `backup` operations.

## Restrictions / remaining acceptance

- User-injected `protect_pin` callbacks must themselves be bounded; arbitrary blocking Python callbacks cannot be forcibly cancelled safely by the current thread-based owner.
- A direct `sudo` command timeout is not yet evidence that every descendant of that command has terminated. A future authenticated SSH rehearsal must test this separately.
- No live cross-host destructive execution, no end-to-end journalled disposable Btrfs deletion, and no crash-recovery rehearsal were performed.
- Receiver pruning remains disabled. Keep 0040 Step 3 OPEN.
