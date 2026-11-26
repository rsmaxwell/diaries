# 0029 Step 2 — Explicitly approved development SQL cutover overlay (2026-11-25)

The user approved the full 49-record mapping following a successful isolated rehearsal. This overlay avoids executing a script whose header explicitly forbade live development use. It adds `tools/step2-49-live-development-conversion.sql` as a comment-only adaptation of the tested SQL, and updates the cutover runner to verify a pinned SHA-256 and assert executable SQL equivalence against the original isolated SQL. The original rehearsal SQL and hybrid SQL remain unchanged.

New development conversion SQL SHA-256: `c01bcd5450287eec00c9eccf1657ebc676847814e1307dfa6ccc8f1a5c22cb39`. The hybrid SQL remains pinned to `563cb107ac8fa518610c2f3a9a4e6b65575cf4acfc89a889bfd2ec288e3080ef`.

The runner requires `DIARIES_0029_APPROVED=YES_49_MAPPING_AND_CAPTIONS` and `DIARIES_0029_RESPONDER_STOPPED=YES_IDE_AND_DOCKER_STOPPED` for `--execute`. The first is now supported by the user's explicit approval; the second MUST ONLY be provided after stopping the development responder in the IDE and confirming no alternate instance runs. Source DB fixed to `diaries-development-db`; production excluded. A fresh custom-format dump is made before the two committed migrations. On failure, keep responder stopped and recover using a controlled restore; do not use the schema-only rollback.

The package has been checked for ZIP integrity, Bash syntax, and SQL statement equivalence in the authoring environment. No development cutover was executed here.

Postmigration still requires updated responder startup, MQTT synchronisation verification, and editor/reader end-to-end checks. Step 2 remains OPEN.
