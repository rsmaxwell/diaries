# 0028-FEAT — Git change-control consolidation and production handoff

Prepared 24 November 2026 from the user’s three Git terminal logs at 15:51–15:54 UTC, the 24 November Diaries and Playbooks source bundles, and the accepted Step 3 preparation reports. **This is a change-control/source commit handoff; it does not grant production approval.**

## Verified source state

- Responder `main` commit `7aa6296e0c675b3d315e9a46bb0dd70202a8cd55` contains the disposable 0028 migration CLI; pushed to `git@github.com:rsmaxwell/diaries-responder.git`.
- Diaries parent `main` commit `1d45a17` pins that exact responder revision; pushed to `git@github.com:rsmaxwell/diaries.git`.
- The last parent `git status --short` shows five modified 0028 feature documentation/tool files and numerous untracked 0028 reports/tests/tools; separate work remains in `change-control/todo/0029-FEAT...` and `change-control/in-progress/0053-DEF...`.
- The feature `.gitignore` excludes `evidence/Step {1,2,3,4}/private/`. These private records contain production manifests, database evidence and JAR hashes, and must never enter source control.

## Change-control commit boundary

Stage only 0028 feature-owned source: root feature README/design/implementation documents, `reports/*.md`, `tests/*.py|*.sh`, and known source/config formats in `tools/`. **Do not stage any `evidence/`, any binary, private manifest, archive, dump, generated dependency tree or unrelated feature.** The accompanying helper audits every changed/untracked candidate and refuses to stage anything if a file is outside the allowlist, symlinked, oversize, binary or has a recognisable credential pattern. It also requires an empty existing Git index, the expected responder pin, and a clean responder submodule.

This is a **defensive screening step, not a complete content/privacy review**. Operator must review the staged diff for private diary text, URLs, credentials, user-specific data and unexpected changes before committing. In particular, source scripts and documentation must not embed approved private review CSV rows or NAS access secrets. The helper does not stage or commit 0029 or 0053.

## Commands — Windows PC, Cygwin terminal

From the Diaries parent root, after applying the ZIP using Beyond Compare 4:

```bash
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
python3 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tools/stage-0028-change-control.py'
```

Review candidate paths and warnings. Then stage only audited 0028 files:

```bash
python3 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tools/stage-0028-change-control.py' --stage

git diff --cached --check
git diff --cached --stat
git diff --cached --name-only
```

Inspect the actual staged content using `git diff --cached -- 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/'` or Beyond Compare. If any private material or unexpected content is found, **do not commit**; unstage that individual file with `git restore --staged -- '<path>'`, edit/remove the material, and repeat the guarded stage check after resolving index changes. Do not use `git reset --hard`, `git clean`, or `git add -A`.

When the exact staged content has been personally reviewed and is acceptable, make one parent-only feature commit:

```bash
git commit -m '0028-FEAT: preserve reviewed migration and release evidence tooling'
git log -1 --oneline
git status --short
```

That final commit and any later push are **not** executed by the helper. A push can trigger CI; inspect the GitHub action/Jenkins configuration before pushing.

## Release boundary and existing evidence

- Reviewed disposition: 71 intended in-place IMAGE conversions and one defer (Fragment 1564). 30 links and 22 existing Marquees to preserve. Formal owner acceptance of Step 1/2 remains open.
- Isolated 71-row transactional rehearsal, MQTT replay, Reader and Editor tests passed; Editor lock-return defect tracked separately in 0053.
- `mars`/`backup` retained matching `production/20261124-003112Z`; PostgreSQL custom dump restored into isolated network-disabled PostgreSQL 18 (2,331 Fragments, 2,270 Marquees, 85 Images, 683 Pages). Three Files payloads verified, **not** a full Files restore.
- Pinned Java 25 fat JAR built with source and checksum; runtime Java 25 checked, but no live migration dry-run on stopped production writers.
- Still OPEN: verified responder/SQL/Files writer exclusion; verified new immutable DB+Files rollback point on `mars` and `backup`; live production dry-run/source drift check; separate owner approval for journal creation and apply; MQTT/GUI postflight; feature closure.

**No production migration is authorised. Do not run maintenance commands in this change-control consolidation step.**
