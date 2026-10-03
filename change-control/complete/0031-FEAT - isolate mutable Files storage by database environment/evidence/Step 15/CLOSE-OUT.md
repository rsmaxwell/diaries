# 0031-FEAT — Step 15 close-out

**Decision:** COMPLETE — 2026-10-03

Step 15 — **Update architecture and operating documentation** — is closed.

The one-database-dataset/one-mutable-Files-root invariant is now documented outside the feature implementation conversation at the architectural, responder, local-operations and production-role levels.

The completed documentation explains both supported local configurations:

```text
isolated committed defaults
  development-infrastructure -> development-infrastructure DB + files-development-infrastructure
  local-docker-build         -> local-docker-build DB + files-local-docker-build
  local-published-smoke      -> local-published-smoke DB + files-local-published-smoke

normal intentionally shared local override
  all three launch modes -> ./data/database/common + files-development-common
```

It also makes clear that `local.env` is loaded after the mode file, both selectors must move together, and removing both common overrides restores the isolated committed defaults.

The physical Files directory is documented as an environment/deployment selector rather than application identity. The original `diaries` scan tree remains shared/read-only, mutable Files are selected separately, the responder-facing container path remains `/data/files`, browser URLs remain `/files/...`, and persisted `Image.relativePath` remains environment-neutral.

Direct Windows development is documented as using the same effective selector through generated responder configuration. Production is documented as using explicit inventory variable `diaries_files_dir`, rendered as `DIARIES_FILES_DIR`, with no implicit role default.

Backup/restore documentation now distinguishes database-only helpers from a complete recoverable dataset. A complete backup requires the database dump and matching Files snapshot/copy with identity/checksum evidence while writers are frozen. Matched restore and read-only reconciliation before writes resume are documented, as is the danger of temporarily re-sharing independently changed roots.

Static verification completed with 31 checks and zero failures. No live deployment or mutable-data operation is required for this documentation-only step.

Step 16 may now use these documents as the normal operating baseline for final regression, rollback rehearsal and feature close-out.
