# Step 2 build failures: responder dated placement and reader raw-template check

Evidence from the 2026-11-25 17:18 and 17:19 Windows build logs:

- Responder: 369 tests, one failure (`AddFragmentContractTest` line 62); the legacy `addFragment` handler creates a `TEXT` Fragment without `placement=DATED`. This patch sets placement explicitly in its DTO.
- Reader: 12 failures during the prior run, with repeated HTTP 500 error pages. The root cause is **not yet established**: JUnit assertions alone do not expose the rendering exception. Do not treat the 500s as resolved by this package.
- `RenderingSafetyTest` counts one raw slot while new annual preamble/postamble slots add two further `fragment.html | raw` occurrences. The patch updates the count specifically for that sanitized field, and keeps the other raw-field rejection assertions.

This is an overlay to the applied Step 2 candidate, not a deployment package. Re-run the responder and reader tests only after applying. Review reader diagnostic command output for the actual exception before touching rendering logic.
