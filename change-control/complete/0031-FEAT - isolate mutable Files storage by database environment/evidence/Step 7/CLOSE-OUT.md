# 0031-FEAT — Step 7 close-out

**Decision:** COMPLETE — 2026-10-02

Step 7 — **Define matched database + Files backup/restore semantics using effective configuration** — is closed.

The implementation now makes the durable pairing visible and enforceable without conflating a database dump with a complete dataset backup. New backups record their effective database/Files identity; sidecar-backed restores reject a mismatched pair; intentionally shared local modes resolve to one `common` backup namespace; and the production Playbooks helpers follow the same contract.

Verification retained in this evidence directory shows that the portable Diaries and Playbooks regression suites pass and that the changed production shell helpers pass syntax validation.

No real Files snapshot is required to close Step 7. That operation belongs to Step 8, which freezes mutable writes and captures the actual pre-migration database + Files recovery artifacts together.

**Next implementation step:** Step 8 — Freeze mutable writes and take pre-migration backups.
