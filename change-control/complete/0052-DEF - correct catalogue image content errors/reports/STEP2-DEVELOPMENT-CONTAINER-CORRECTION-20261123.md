# 0052 Step 2 — development infrastructure container correction (23 November 2026)

The first `--mode both --apply` attempt stopped before backup or write because the Step 2 script queried `diaries-local-db`, which belongs to `local-docker-build`, and was not running (`No such container`). The approved direct-development environment is `development-infrastructure`, whose `compose.development-infrastructure.yaml` names the PostgreSQL container `diaries-development-db`.

The Step 2 correction script now uses `diaries-development-db` for development SQL. This package also extends its offline tests to assert the correct container routing. No production container names, catalogue identities, image paths, image hashes, or data operations changed.

Start local `development-infrastructure` via the supported Windows start batch script, checking its effective database/Files pair matches the dataset used by 0052 (`files-development-common`). Do not run a Java responder during the apply. The Step 2 script still guards the pre-change Image 3/18 metadata and source hashes before any write; if the selected dataset is wrong it must fail without applying changes.

The original failed run's private diagnostics are under `evidence/Step 2/private/20261123T101209Z/` and must remain untouched.
