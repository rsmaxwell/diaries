# 0028 Step 2 — Cygwin Python compatibility correction (2026-11-23)

## Observation

The isolated original page-scan runner established an inventory of 41 source pages, then stopped before media staging with `AttributeError: 'PosixPath' object has no attribute 'is_relative_to'` in `0028-stage-original-page-scans.py`. The host Python interpreter lacks `Path.is_relative_to` (introduced in Python 3.9).

## Correction

Replace `Path.is_relative_to` with `is_within(path, root)`, which checks equality or canonical ancestor membership using `Path.parents` (supported by Python 3.8). Both checks use canonicalized paths. Preserve the requirements that the destination is empty and separate from the source, source files are regular non-symlinks, resolved source paths remain within the source root, and image digests are independently verified after copying.

Add compatibility, similarly-named sibling, and symlinked-parent escape regression tests. Existing tests remain in place. The change is confined to the page-scan staging script and its tests; no Java, Docker networking, database, MQTT or production configuration changes are required.

## Running and acceptance

In the Windows PC Cygwin shell, rerun the same command from the Diaries parent repository root:

```bash
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
export DIARIES_0028_SOURCE_DIARIES_ROOT='/cygdrive/p/nancy-and-ronald-maxwell/documents/sea-captains-chest/diaries-content/diaries'
bash 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments/tools/verify-0028-step2-source-scans.sh'
```

The runner reuses the accepted MQTT/Reader evidence and the unchanged isolated database. It does not execute a migration `apply`. The staging script first validates the complete list of source files, then copies them to private evidence and verifies digests; browser visual and Editor acceptance remain separate gates. Production migration remains unauthorised.
