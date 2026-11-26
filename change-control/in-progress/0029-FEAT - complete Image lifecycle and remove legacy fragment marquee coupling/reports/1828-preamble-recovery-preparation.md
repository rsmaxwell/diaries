# 0029-FEAT — 1828 PREAMBLE recovery preparation

Status: NOT EXECUTED. Historical fragments 1, 2, 3 missing from development database. Temporary fragments 2348, 2349 present. 2026-11-25 pre-cutover archive has pg_restore TOC including fragment table; contents not yet extracted and verified.

1. Run `python3 tools/prepare-1828-preamble-recovery.py` from within the feature directory (see chat for exact command).
2. Examine generated read-only extraction summary and guarded SQL under `evidence/step-2-1828-preamble-recovery/`. Do not execute before review and explicit approval.
3. After approval, take a fresh full database backup immediately before transactional SQL recovery. Run only against diaries-development-db.
4. Restart the development responder so Synchronise republishes restored retained topics and removes orphaned temporary topics. Confirm originals in Reader and SQL and no temporary topics; capture evidence.

No broad restore, migration replay, or production operation is authorised.
