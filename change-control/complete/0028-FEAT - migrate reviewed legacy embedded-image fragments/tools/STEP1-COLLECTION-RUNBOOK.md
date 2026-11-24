# 0028 Step 1 — read-only production collection

**State:** procedure prepared, no live commands executed. **Safety:** the
collector runs one `COPY (SELECT ...) TO STDOUT` on PostgreSQL through SSH,
with `default_transaction_read_only=on`; it does not write the database,
change MQTT, stop services or touch Files. It produces **UNREVIEWED** manifests;
no occurrence automatically becomes a conversion.

## 0. Check sources before running

The new tool is a *one-off Python 3 standard-library script* in the parent
Diaries feature, not a permanent Ansible role or responder change. Its remote
SQL assumes the confirmed 2026-11-17 JPA columns (`fragment.type`,
`fragment.page_id`, `fragment.image_id`, lock fields, `marquee.page_id`,
`image.relative_path`/`checksum`). If live schema differs, stop and review; do
not patch production to make the export succeed.

**Windows Cygwin terminal — authoritative checkout:**

```bash
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
git branch --show-current
git rev-parse HEAD
git status --short
git submodule status
git -C diaries-responder branch --show-current
git -C diaries-responder rev-parse HEAD
git -C diaries-responder status --short
git -C diaries-client status --short
git -C diaries-web status --short
git diff --check
```

Apply this parent-only ZIP with Beyond Compare 4. Then synchronize the relevant
Diaries parent repository state to `/home/richard/diaries` on mango using your
normal Git workflow; **the ZIP being applied on Windows does not create these
files on mango**. Do not force-pull or overwrite uncommitted changes.

**mango SSH terminal — independently verify actual checkout and new tool:**

```bash
cd /home/richard/diaries
git branch --show-current
git rev-parse HEAD
git status --short
git submodule status
FEATURE='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
if test -f "$FEATURE/tools/step1_inventory.py"; then echo 'PASS: Step 1 collector present'; else echo 'FAIL: synchronize Diaries parent repository first'; fi
```

## 1. Non-destructive production preflight

**mango SSH terminal, via SSH to pluto — current deployed Compose state:**

```bash
ssh pluto 'cd "$HOME/projects/diaries" && docker compose --file compose.yaml --env-file .env ps && docker compose --file compose.yaml --env-file .env config --images'
```

The production directory matches the latest Playbooks role default
`diaries_project_dir: {{ projects_dir }}/diaries` and `projects_dir:
{{ HOME }}/projects`; check the actual output, since inventory can override it.
If the command fails, investigate the live deployment path before running the
collector. Preserve service/image/authoring-gate evidence without dumping `.env`
or responder configuration secrets into logs.

## 2. Collect a single consistent current-schema database export

**mango SSH terminal — run from the synchronized parent repository:**

```bash
cd /home/richard/diaries
FEATURE='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
RUN="$(date -u +%Y%m%dT%H%M%SZ)"
python3 "$FEATURE/tools/step1_inventory.py" \
  --ssh-host pluto \
  --output "$FEATURE/evidence/Step 1/private/$RUN"
```

The script runs `ssh -T pluto sh -s` and a `docker compose exec -T diaries-db`
`psql -c COPY...TO STDOUT` **inside pluto's database container**, sending the
result stream directly to the ignored/private feature evidence directory on
mango. It does not create scripts or evidence directories on pluto. The
container's own `POSTGRES_USER`/`POSTGRES_DB` environment supplies connection
identity; no passwords are printed or copied to command arguments. Output
includes the **full original HTML**, so do not paste its contents into chat.

Output files include:

- `current-schema-snapshot.PRIVATE.csv`: unredacted, internally consistent
  Fragment and Image rows and database identity (private);
- `0028-dispositions.UNREVIEWED.csv`: source Fragment review rows, **empty**
  decision/identity fields;
- `0028-image-decisions.UNREVIEWED.csv`: one source occurrence per row with
  **empty** matching/action/caption fields;
- `0028-structural-exceptions.csv`: state anomalies, lock warnings and
  excluded existing IMAGE rows;
- `0028-summary.json` and `SHA256SUMS.txt`: provenance and file hashes.

One query gives a statement-consistent database snapshot; it does **not** freeze
later edits or the Files root. All review and apply checks must detect drift.
The HTML parser here is for discovery only; source-span-safe HTML mutation is
Step 2's responsibility.

## 3. Recover historical inputs and reconcile

The 0022 source bundle contains the **historic review ledger** in:

`change-control/complete/0022-FEAT - migrate fragments to explicit page ownership and type/0022-static-baseline-20260911/review-ledger.json`

This is **not** the generated `0022-legacy-image-candidates.csv` and cannot
replace it. The actual generated 0022 and 0024 CSVs were **not present** in the
2026-11-17 source bundle. Search preserved 0022/0024 execution evidence,
backups or your existing archives without assuming those files exist; preserve
hashes and provenance. The 0022 review ledger has 42 historical decisions but
only 2 IMAGE decisions with database Fragment IDs; neither figure is a current
production candidate count.

After historical CSVs are located, rerun the offline report from the already
captured current snapshot (new output directory), specifying any existing inputs.
Do **not** fabricate or use empty CSVs. Example — replace literal paths with
files you have actually located:

```bash
cd /home/richard/diaries
FEATURE='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
# One optional example with the known bundled review ledger, not candidate CSV:
python3 "$FEATURE/tools/step1_inventory.py" \
  --snapshot "$FEATURE/evidence/Step 1/private/<RUN>/current-schema-snapshot.PRIVATE.csv" \
  --historic-ledger 'change-control/complete/0022-FEAT - migrate fragments to explicit page ownership and type/0022-static-baseline-20260911/review-ledger.json' \
  --output "$FEATURE/evidence/Step 1/private/<NEW-RUN>"
```

Replace `<RUN>` and `<NEW-RUN>` before running. To add actual recovered
inventories, pass `--historic-0022 <0022-legacy-image-candidates.csv>` and/or
`--xref-0024 <0024-candidate-cross-reference.csv>`. These are review hints;
`UNIQUE_LOCAL_SUFFIX` and matching ID/path/checksum **never** grant automatic
conversion. Output is intentionally still unapproved.

## 4. Independently verify Files-root integrity

Run a **read-only** 0024 Image reconciliation against the *same production
catalogue and Files root*, with the pre-existing `migration0024ImageCatalogue`
utility in `dry-run` mode only. Preserve its `0024-file-inventory.csv`,
`0024-conflicts.csv`, `0024-candidate-cross-reference.csv`, summary and hash
manifest under this feature's private Step 1 evidence. The installed 0024
wrapper defaults to an out-of-repository `${HOME}/temp/dry-run`; do **not**
accept that as a permanent evidence location. Agree the actual mount/evidence
collection command after inspecting `compose.yaml` and available storage on
pluto. Do not run `apply`, modify the catalogue or change Files.

The current SQL collector verifies only **database catalogue values**, not
Filesystem presence, symlink confinement, file checksum or MIME validity.
Until 0024 reconciliation is collected and accepted, **no image mapping is
approved**, even if current Image ID/path/checksum equals a historical hint.

## 5. Review/freeze and Step 1 gate

For each current source Fragment with one or more embedded images, independently
review the Fragment-level disposition and every embedded `<img>` occurrence.
Review preserved text/captions, Page/Marquee/type/sequence, Image ID/path and
File checksum. Preserve explicit reasons for KEEP_LEGACY or DEFER. Require
review identity/time and complete coverage; ensure zero-image historic
candidates are also resolved. **Do not** edit the unreviewed drafts directly to
claim approval without the 0028 Step 2 strict validation utility and owner
sign-off. Record input hashes and manifest hashes.

Step 1 stays **OPEN** until historical/current lineage, Files integrity,
complete manual decisions and approval are genuinely established. Never mark
Step 1 CLOSED from a successful script run alone.

## 6. Offline unit checks (no production access)

**mango SSH terminal, repository root:**

```bash
cd /home/richard/diaries
FEATURE='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
python3 -m unittest discover -s "$FEATURE/tests" -p 'test_step1_inventory.py' -v
```

The synthetic tests cover double/missing image sources, Unicode HTML entities,
no premature approval, candidate drift, duplicate IDs and read-only SQL scope.
They are not a replacement for the live collection or Step 1 approval.
