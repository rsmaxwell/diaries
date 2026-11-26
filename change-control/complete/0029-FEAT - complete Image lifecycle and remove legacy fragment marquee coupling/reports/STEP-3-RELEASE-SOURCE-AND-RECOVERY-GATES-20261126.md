# 0029-FEAT — Step 3 release-source and recovery audit handoff (26 November 2026)

## Accepted evidence — do not repeat

- Complete development integration and six Editor/Reader browser checks: accepted.
- Production baseline: 2,331 Fragments; 2,270 Marquees; exactly 11 expected Page-less Fragments.
- Isolated production migration: hybrid conversion, Marquee column retirement, reverse rollback and reapplication all PASS (12:53 UTC).
- Production MQTT ACL source includes all three `diaries/years/#` permissions; deployed ACL still lacks them.

## Source and release boundaries

Windows `diaries` parent and its independent `diaries-client`, `diaries-responder`, and `diaries-web` submodules have uncommitted changes. Their current HEAD revisions alone do **not** identify the accepted release. Preserve all local work; prepare independent submodule commits before updating parent Gitlinks. Do not blindly stage unrelated evidence or README files.

Ansible repo on mango is `/home/richard/ansible-controller` with submodules `playbooks/` and `inventory/`. `playbooks` has existing local changes including production MQTT ACL, defaults and `scripts/diaries.sh`. Do not overwrite or reset them. After the three application images are built, update the *effective* Playbooks image-tag values. Previously observed defaults: client `0.0.9-build-80`, responder `0.0.9-build-86`, web `0.0.9-build-9`.

## Published dataset checks

The attached audit checks the completed manifest's status, required backup components, the two database-dump SHA256 entries and `pg_restore --list` on the published custom dump. It deliberately does not hash the entire Files payload or perform a restore. The prior publisher service reported success at 00:31 GMT and the published root is `/home/richard/projects/diaries/data/diaries-backup`.

**Outstanding before production approval:** verify full Files hashes and perform a disposable restore of the selected completed dataset, or explicitly cite previously accepted restore evidence covering the same recovery model. Confirm the recovery point covers writes since publication or create a new quiesced pre-deployment recovery point. Capture production File dataset and database rollback coordination. Production deployment remains unauthorised.

## Execution

Run from Windows 11 Cygwin in `/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries`:

```bash
bash 'change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling/tools/run-step3-release-source-and-recovery-audit.sh'
```

Audit output is stored under `evidence/step-3-release-source-and-recovery/`. Command reads Git metadata and the published backup only. It creates **local evidence logs**, not production data.
