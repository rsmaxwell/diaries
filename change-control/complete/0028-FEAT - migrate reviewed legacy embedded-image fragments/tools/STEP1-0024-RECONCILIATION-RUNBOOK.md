# 0028 Step 1 — Reconcile current image candidates through existing 0024 read-only code

**Status:** package prepared and tested offline; production 0024 dry-run has **not yet been executed**.

## Purpose and evidence

The 0028 read-only collector ran on 2026-11-18 and found 72 candidates, all of which have `fragment.type IS NULL` (intentional in the 0022 design). Fifty also lack explicit `fragment.page_id`. It is not yet known whether they have usable Marquee Page associations.

The script `diaries-responder/scripts/files/migration0024ImageCatalogue.sh` exists in the supplied responder source, but it is **not deployed** at `pluto:~/projects/diaries/scripts/`. Do not install the historical wrapper or run its `apply` mode to work around this. Its baked-in JAR path also differs from the supplied current Dockerfile, which installs `/opt/diaries/diaries-responder.jar` rather than `/opt/diaries/lib/diaries-responder.jar`.

The one-off `tools/step1_prepare_0024.py` converts the frozen current 0028 occurrence inventory into the **old 0022-compatible input schema** understood by the existing 0024 Java CLI. This is **not** a recovered original 0022 report. It also publishes a private, aggregate Page-ownership classification for the 72 candidate fragments.

The one-off `tools/step1_run_0024_dryrun.sh` invokes the **already deployed responder image** as a disposable Compose service, using Java `--mode dry-run` only. It reads the current database and configured Files root, produces a fresh file integrity inventory and candidate cross-reference, verifies hashes and copies evidence into the Diaries feature tree on mango. No DB writes, migration apply, service stop or application deployment are authorised. It uses a protected scratch directory beneath `pluto:~/temp/` only for the container volume; that scratch directory is deleted **only on full success after transferring and verifying output**. On error, scratch data is preserved for diagnosis.

## 1. Install from Windows

**Windows Cygwin terminal** — compare/apply the package to the Windows Diaries parent repository first. Inspect Git changes before commit. Then synchronise the parent repository to `mango` using your normal Git workflow. The submodules are not needed for this Step 1 tool.

```bash
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
git branch --show-current
git rev-parse HEAD
git status --short
git diff --check
```

Avoid overwriting uncommitted changes in other features.

## 2. Prepare the compatible candidate input locally

**mango SSH terminal** (not Windows or pluto):

```bash
cd /home/richard/diaries
FEATURE='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
FROZEN="$FEATURE/evidence/Step 1/private/20261118T093606Z"
RUN="$(date -u +%Y%m%dT%H%M%SZ)-0024"
DERIVED="$FEATURE/evidence/Step 1/private/$RUN"

python3 -m unittest discover -s "$FEATURE/tests" -p 'test_step1_prepare_0024.py' -v && \
python3 "$FEATURE/tools/step1_prepare_0024.py" \
  --inventory "$FROZEN" --output "$DERIVED"
```

The output prints *aggregate counts only*. The candidate CSV is private and must not be added to Git. The output directory must be NEW, and its `SHA256SUMS.txt` is a separate evidence set; it does not alter the frozen original inventory or its hashes.

Review aggregate `Page` ownership before proceeding. For example, missing direct Page IDs with exactly one Marquee with a populated Page ID are *possible* derivations, not verified Page relationships; they must be checked against `page` table and approved with the migration decisions.

## 3. Run 0024 Files-root integrity and source cross-reference

**Same mango SSH terminal**, only if the preparation succeeded and `$DERIVED` still points to the new output:

```bash
bash "$FEATURE/tools/step1_run_0024_dryrun.sh" "$DERIVED"
```

This will invoke `ssh pluto`, without transferring a script or editing deployed code. It uses a disposable responder-image container; the production responder remains running. The 0024 reconciler writes **only** to its separate evidence output, never to the catalogue in dry-run mode. The script verifies its `DRY_RUN_COMPLETE` outcome and full occurrence count before removing the **unique** temporary `pluto` scratch directory.

If it fails, do **not** run `apply`, change the database, recreate the evidence directory or clear unknown scratch locations. Preserve the raw terminal log and report the failure. If the utility is absent from the deployed JAR, record that as a deployment/tool compatibility finding and stop.

## 4. Inspect results and next gate

On **mango**:

```bash
cd /home/richard/diaries
FEATURE='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
(cd "$DERIVED" && sha256sum -c SHA256SUMS.txt)
(cd "$DERIVED/0024-dry-run" && sha256sum -c SHA256SUMS.txt)
```

Do not publish `0028-0024-candidates.PRIVATE.csv`, `0024-file-inventory.csv`, `0024-candidate-cross-reference.csv`, or raw HTML in Git or in chat; share the aggregate terminal output only.

The new cross-reference can classify exact Image ID matches, unique suffix hints, absent files/catalogue entries, ambiguous paths, and unacceptable metadata/checksum status. These are still *unreviewed hints*. Before Step 1 is closed: reconcile against historic 0022 inventories where available, investigate all 50 missing direct Page associations, manually approve 72 fragment dispositions and 72 occurrence actions, and hash the approved manifest.
