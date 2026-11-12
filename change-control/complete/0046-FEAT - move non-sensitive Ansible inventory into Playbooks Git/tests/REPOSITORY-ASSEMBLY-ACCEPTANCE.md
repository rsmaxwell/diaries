# 0046 — Repository assembly checks

This is a **staging** check, not the all-host acceptance gate.

1. Run `bash -n tools/establish-0046-three-repositories.sh` locally.
2. Run `python3 tests/test-0046-repository-assembly.py` to exercise a synthetic private-parent/public-child/private-child Git topology without contacting GitHub.
3. Before real `--apply`, run `verify-0046-prepared-inventory.py` against the local source and candidate. No raw values may appear in logs.
4. On `mango`, `--preflight` must validate clean frozen source and private remote visibility. The private names must not be mistaken for verified existing repositories.
5. Real `--apply` must publish protected inventory only after PRIVATE visibility is confirmed. Parent must track child **gitlinks** (`160000`) rather than copy child contents.
6. Post-publication verify `git submodule status` shows the expected pins, child/parent SHAs are published, private/private/public visibility is unchanged, and no operational inventory was switched.
7. If GitHub CLI is absent or unauthenticated, stop; do not work around the privacy gate with public repositories.
8. Proceed to consolidated Step 3 estate-wide equivalence and cutover only after the staging evidence is reviewed.
