# Step 03 — Private sender transaction deadline regression

Status: source-only; **not deployed**, production receiver pruning remains disabled.

Changes: private `run_private_transaction_process()` now accepts `transaction_timeout` and starts a watchdog for the entire child-process exchange. When time expires the watchdog kills the transport child to break blocked pipe reads; the normal cleanup then closes streams and reaps the child while holding the source lock. The persistent source pruning pin is never cleared.

Local Python 3 regressions completed on 2026-10-23:
- New private deadline regression: 6/6 passed (silent first challenge, silent second challenge, silent final completion, success, bad deadline, no CLI).
- Previous private process lifecycle regression: 5/5 passed.

**Unverified / not acceptance evidence:** No live SSH, production snapshot deletion, privilege changes, journal replay, or disposable Btrfs run. The watchdog bounds a blocked child pipe while the parent can run; it does not forcibly interrupt an indefinitely blocking local `protect_pin` callback, nor handle descendant processes retaining stdout after the direct child exits. These require targeted checks before any production integration.

On mango source validation from Windows Cygwin, pipe the test into `python3 /dev/stdin <sender-source-path>`; do not deploy the private code to mars yet. The last deployed installed sender can differ from this source version.
