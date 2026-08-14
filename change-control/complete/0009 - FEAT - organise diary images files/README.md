# 0009 - FEAT - organise diary image

## Summary

Reorganise the files used by the Diaries application so that final published images are grouped by the diary to which they belong, while preserving original photographs, scans, Gimp projects, Inkscape projects and other working material under the corresponding diary’s `metadata` directory.

The reorganisation must provide a clear separation between:

* authoritative source and working material;
* final files published by the Diaries application;
* temporary migration and validation files.

The work should be performed one diary at a time to avoid handling the entire image collection in a single migration.

---

## Background

Diary HTML fragments reference images that must be available through the Diaries application’s static-file mechanism.

The existing content contains two broad categories of image-related files:

1. Original diary material and image-processing sources held under each diary’s `metadata` directory.
2. Flattened JPEG and PNG files copied into the shared `files` hierarchy for use by the application.

Some displayed images are derived from original photographs or scans using Gimp or Inkscape. These derived images may include:

* text;
* arrows;
* captions;
* outlines;
* highlighted areas;
* maps;
* composited images;
* other annotations or decorative elements.

Only the flattened exported image is required at runtime, but the original image and editable Gimp or Inkscape project must be retained so that the final image can be reproduced or changed later.

The supplied directory layout also contains Synology-generated indexing and thumbnail files under directories such as `@eaDir`. These files are NAS implementation details and are not part of the diary source or application content.

---

## Problem

The current image organisation has several problems:

* final application images are collected in shared directories rather than being clearly grouped by diary;
* the same image may exist in several locations;
* temporary migration files, source files and published files are not always clearly distinguished;
* it may be difficult to determine which source project produced a published image;
* the common image directory can become overwhelming when working on only one diary;
* Synology-generated thumbnail and metadata files obscure directory listings and archives;
* inconsistent file naming may create problems when files are served on Linux or referenced through URLs.

A clearer structure is required before further diary HTML fragments are updated to reference application-hosted images.

---

## Objectives

The implementation shall:

1. Group application-visible files by diary.
2. Keep original and editable image sources under the relevant diary’s `metadata` directory.
3. Keep only final browser-displayable files in the runtime `files` hierarchy.
4. Preserve a clear relationship between a published image and its source material.
5. Allow migration and validation to be completed one diary at a time.
6. Exclude Synology-generated files from application content, migration archives and diagnostic listings.
7. Adopt a consistent, URL-safe file-naming convention.
8. Avoid deleting existing files until the corresponding diary has been completely tested.

---

## Proposed directory responsibilities

### `diaries`

The `diaries` hierarchy is the authoritative archive.

It may contain:

* original diary page scans;
* original photographs;
* downloaded historical images;
* maps;
* Gimp `.xcf` projects;
* Inkscape `.svg` or `.svgz` projects;
* supporting layers and overlays;
* `.xmp` metadata;
* Word documents;
* research notes;
* editor comments;
* final exports retained for comparison.

Example:

```text
diaries/
└── diary-1831/
    ├── diary pages
    └── metadata/
        ├── images/
        ├── word/
        ├── editor-comments/
        └── other source material
```

The source material must remain associated with its diary.

### `files`

The `files` hierarchy is the runtime publication area used by the Diaries application.

It should contain only files intended to be requested directly by the client or referenced from diary HTML, including:

* final JPEG images;
* final PNG images;
* final WebP images, if introduced later;
* downloadable documents intentionally linked from diary content.

It should not contain:

* Gimp `.xcf` projects;
* editable Inkscape projects, unless an SVG is deliberately served as the final web image;
* `.xmp` sidecar files;
* temporary exports;
* research documents not linked from the diary;
* Synology `@eaDir` content;
* Synology thumbnail files;
* `Thumbs.db`.

---

## Proposed target structure

The permanent runtime structure should be diary-first:

```text
files/
├── diary-1828-and-1829-and-jan-1830/
│   └── images/
├── diary-1830/
│   └── images/
├── diary-1831/
│   └── images/
├── diary-1832/
│   └── images/
├── diary-1834/
│   └── images/
└── staging/
```

For example:

```text
files/
└── diary-1831/
    └── images/
        ├── img2734-doodle-on-blotting-paper.jpg
        ├── img2753-white-swan-alnwick.png
        ├── img2754-castle-alnwick.png
        ├── img2805-blue-posts-pub.jpg
        └── img2805-launch-of-hms-thunderer.jpg
```

The `staging` directory may be retained temporarily during migration:

```text
files/
└── staging/
    └── diary-1831/
        └── images/
```

After a diary has been migrated and verified, its temporary staging directory should be removed.

---

## Source-image organisation

Simple, unmodified images may remain directly under the diary’s metadata image directory.

Example:

```text
diaries/
└── diary-1831/
    └── metadata/
        └── images/
            ├── img2767-hms-samarang.jpg
            └── img2767-hms-samarang.xmp
```

Images with editable source projects or multiple supporting files should use an image-specific directory.

Example:

```text
diaries/
└── diary-1831/
    └── metadata/
        └── images/
            └── img2805-launch-of-hms-thunderer/
                ├── original.jpg
                ├── img2805-launch-of-hms-thunderer.svg
                ├── img2805-launch-of-hms-thunderer.jpg
                └── img2805-launch-of-hms-thunderer.xmp
```

Where a derived image has several components, the directory may optionally be divided further:

```text
img2805-launch-of-hms-thunderer/
├── original/
│   └── source-photograph.jpg
├── project/
│   └── img2805-launch-of-hms-thunderer.svg
├── resources/
│   ├── arrow.svg
│   └── notes.txt
└── export/
    └── img2805-launch-of-hms-thunderer.jpg
```

This more detailed layout should only be used where it adds value. It is not necessary for every ordinary image.

---

## File-naming convention

Published image filenames should use the following pattern:

```text
img<image-number>-<short-description>.<extension>
```

Examples:

```text
img2755-bondgate-hall.png
img2805-launch-of-hms-thunderer.jpg
img2842-map-dublin.jpg
img2900-st-petersburg-map.png
```

The following rules should apply:

* use lower-case names;
* use hyphens rather than spaces;
* avoid underscores where practical;
* retain the existing image number where it relates to a diary page, fragment or existing identifier;
* use a short descriptive suffix;
* avoid redundant words such as repeated `image`;
* do not include `final` or `published` in runtime filenames;
* use the directory structure to distinguish source files from published files;
* avoid changing an existing name unnecessarily when it is already suitable.

Existing HTML references and filenames must be changed together.

---

## Relationship between source and published files

The source and published file should share the same diary name and basename wherever practical.

Example:

```text
Source project:

diaries/diary-1831/metadata/images/
    img2805-launch-of-hms-thunderer/
        img2805-launch-of-hms-thunderer.svg
```

```text
Published file:

files/diary-1831/images/
    img2805-launch-of-hms-thunderer.jpg
```

This convention allows the editable source for a published image to be found without introducing a separate database or manifest.

A manifest may be considered later, but it is not required for the initial implementation.

---

## HTML references

Diary HTML fragments should use paths that include the diary name.

Conceptual example:

```html
<img
  src="/files/diary-1831/images/img2805-launch-of-hms-thunderer.jpg"
  alt="Launch of HMS Thunderer">
```

The exact URL prefix must be confirmed against the Diaries responder’s existing static-file mapping.

The implementation must not assume that the filesystem path and public URL are identical. The mapping used by:

* day-to-day development;
* local Docker build;
* local published-image smoke testing;
* remote deployment

must be checked so that the same relative content path works consistently in all modes.

---

## Synology-generated files

The NAS creates thumbnail and indexing material such as:

```text
@eaDir/
SYNOPHOTO_THUMB_XL.jpg
SYNOPHOTO_THUMB_M.jpg
SYNOPHOTO_THUMB_SM.jpg
SYNOPHOTO_THUMB_PREVIEW.jpg
SYNOINDEX_MEDIA_INFO
* @SynoEAStream
Thumbs.db
```

These files must not be:

* copied into the application runtime tree;
* referenced from diary HTML;
* treated as source image variants;
* included in migration ZIP files;
* included in clean directory-layout reports.

A clean directory listing can be generated with:

```bash
find . \
  -path '*/@eaDir' -prune -o \
  -name 'Thumbs.db' -prune -o \
  -print \
  | sort > ../file-layout-clean.txt
```

A ZIP archive can exclude Synology-generated files with:

```bash
zip -r files.zip files \
  -x '*/@eaDir/*' \
  -x '*/Thumbs.db' \
  -x '*@SynoEAStream'
```

---

## Implementation approach

The migration must be completed one diary at a time.

`diary-1831` is a suitable candidate for the first migration because its image material is already reasonably well grouped and can be used to validate the proposed structure before applying it to larger or less consistent diaries.

No old directory should be deleted until the corresponding diary has passed all verification steps.

---

# Implementation steps

## 1. Back up the existing content

Create a full backup of the existing `diaries-content` directory before making any changes.

From the parent directory:

```bash
zip -r diaries-content-before-image-reorganisation.zip diaries-content \
  -x '*/@eaDir/*' \
  -x '*/Thumbs.db' \
  -x '*@SynoEAStream'
```

Also retain the existing Synology snapshot or normal NAS backup where available.

Confirm the archive can be listed:

```bash
unzip -l diaries-content-before-image-reorganisation.zip
```

Do not proceed until the backup has been verified.

---

## 2. Record the current clean directory layout

Generate a directory report without NAS-generated files:

```bash
cd /volume1/photo/nancy-and-ronald-maxwell/documents/sea-captains-chest/diaries-content

find . \
  -path '*/@eaDir' -prune -o \
  -name 'Thumbs.db' -prune -o \
  -print \
  | sort > ../file-layout-before-image-reorganisation.txt
```

Retain this report with the change item.

---

## 3. Confirm the application’s static-file mapping

Inspect the current Diaries responder configuration and deployment files to determine:

* the host directory mounted as the runtime files directory;
* the container directory to which it is mounted;
* the URL prefix exposed by the responder or static file server;
* whether the mapping supports nested diary directories;
* whether all four operating modes use compatible mappings.

Check:

* responder configuration;
* local development configuration;
* local Docker Compose files;
* local published-image smoke Compose files;
* Ansible deployment templates;
* Nginx configuration, where relevant.

Record the confirmed mapping in this change item before updating HTML.

---

## 4. Select the first diary

Use `diary-1831` as the initial pilot unless another smaller diary is preferred.

Limit the first migration to:

```text
diaries/diary-1831
files/staging/diary-1831
files/diary-1831
```

Do not reorganise unrelated diaries at the same time.

---

## 5. Create the target runtime directory

Create:

```bash
mkdir -p files/diary-1831/images
```

Retain the staging directory during the migration:

```bash
mkdir -p files/staging/diary-1831/images
```

The staging directory is temporary and should not be used as the permanent HTML location.

---

## 6. Inventory the images referenced by the diary

Search all HTML fragments belonging to `diary-1831` for image references.

For example:

```bash
grep -RniE '<img|src=|href=' diaries/diary-1831 \
  --exclude-dir='@eaDir'
```

Create a checklist containing:

* the HTML file or fragment;
* the current image reference;
* the current image location;
* the intended published filename;
* the source or project location;
* whether the image is simple or derived;
* whether the source is complete;
* whether the image has been copied;
* whether the HTML has been updated;
* whether the result has been tested.

Do not rely only on the contents of the current shared `files/images` directory. The HTML references are the authoritative indication of what the application needs.

---

## 7. Identify each image’s authoritative source

For every referenced image, locate the corresponding material under:

```text
diaries/diary-1831/metadata
```

Classify each image as one of:

* original image used unchanged;
* flattened derived image with Gimp source;
* flattened derived image with Inkscape source;
* flattened derived image with missing editable source;
* image whose relationship is uncertain;
* apparent duplicate;
* unused image.

Where the source relationship is uncertain, do not delete or rename the files until it has been resolved manually.

---

## 8. Organise complex source images

For images with editable projects or several resources, create an image-specific directory under the diary metadata.

Example:

```text
diaries/diary-1831/metadata/images/
└── img2805-launch-of-hms-thunderer/
```

Move only files that are clearly associated with that image.

Keep:

* original raster source;
* `.xcf`, `.svg` or `.svgz` project;
* supporting image layers;
* notes;
* metadata;
* final export.

Do not flatten or discard the editable project.

Avoid reorganising simple images unless there is a clear benefit.

---

## 9. Normalise the published filename

Choose a URL-safe runtime filename for each image.

Example:

```text
img2805-launch-of-hms-thunderer.jpg
```

Before renaming, search for every current reference:

```bash
grep -RniF 'old-image-name.jpg' diaries/diary-1831 \
  --exclude-dir='@eaDir'
```

Only rename the file when all affected references are known.

Avoid renaming an image solely for cosmetic reasons where the existing name is already:

* lower-case;
* free of spaces;
* descriptive;
* unique within the diary.

---

## 10. Copy the final image into staging

Copy the flattened, browser-displayable image into:

```text
files/staging/diary-1831/images/
```

Example:

```bash
cp \
  diaries/diary-1831/metadata/images/img2805-launch-of-hms-thunderer/img2805-launch-of-hms-thunderer.jpg \
  files/staging/diary-1831/images/
```

Do not copy:

* `.xcf`;
* `.xmp`;
* editable SVG projects that are not themselves the web image;
* source photographs not referenced by HTML;
* NAS metadata;
* temporary files.

---

## 11. Verify staged files

For each staged image:

* open it directly;
* confirm orientation;
* confirm annotations are present;
* confirm it is the intended final version;
* confirm the extension matches the file type;
* confirm the dimensions are reasonable;
* compare it visually with the existing application image;
* verify that it is not an accidental duplicate of an unrelated image.

Checksums may be used to identify exact duplicates:

```bash
find files/staging/diary-1831/images \
  -type f \
  -exec sha256sum {} \; \
  | sort
```

Where two differently named files have the same checksum, inspect them manually before deciding whether the duplication is valid.

---

## 12. Publish the diary images

After the staged images have been checked, copy them into:

```text
files/diary-1831/images/
```

For example:

```bash
cp -p \
  files/staging/diary-1831/images/* \
  files/diary-1831/images/
```

At this stage, retain all old shared image copies.

---

## 13. Update diary HTML references

Change the relevant diary HTML fragments so that they reference the diary-specific runtime path.

Conceptual change:

```html
<img src="/files/images/img2805-launch-of-hms-thunderer.jpg">
```

to:

```html
<img src="/files/diary-1831/images/img2805-launch-of-hms-thunderer.jpg">
```

Use the public URL prefix confirmed in implementation step 3.

Include meaningful `alt` text where it is missing:

```html
<img
  src="/files/diary-1831/images/img2805-launch-of-hms-thunderer.jpg"
  alt="Launch of HMS Thunderer">
```

Do not change image captions, dimensions or page layout unless required by the path migration.

---

## 14. Test in day-to-day development mode

Start the normal development environment.

For every changed diary page:

* open the page in the browser;
* check that the image loads;
* check the browser network tab;
* confirm the response is HTTP 200;
* confirm the returned content type is correct;
* confirm the image dimensions and layout are unchanged;
* check the browser console for errors;
* check the responder log for missing-file or path errors.

Test direct access to at least one migrated image URL.

---

## 15. Test in local Docker build mode

Build and start the local Docker stack.

Confirm:

* the new nested diary directory is mounted into the responder or static file server;
* the image is available inside the container;
* the same HTML reference works without mode-specific changes;
* no Windows-only path assumptions have been introduced.

Inspect the mounted directory inside the relevant container where necessary.

---

## 16. Test in local published-image smoke mode

Start the local published-image smoke stack.

Confirm:

* the shared runtime files directory is mounted correctly;
* the published image is returned through the same URL;
* Nginx or the static file server does not strip or rewrite the diary path incorrectly;
* the diary page displays without missing images.

This test is important because the runtime image and application images may come from separate sources.

---

## 17. Test the remote deployment mapping

Inspect the Ansible-generated deployment configuration and confirm that the remote target exposes:

```text
files/diary-1831/images/
```

without requiring a separate mount for each diary.

Deploy only after local testing is complete.

On the remote host, verify:

* the files exist beneath the mounted runtime directory;
* permissions allow the responder or static server to read them;
* the public URL works;
* the relevant diary pages display correctly.

---

## 18. Check for remaining old references

Search for references to the previous shared location.

For example:

```bash
grep -RniF '/files/images/' diaries/diary-1831 \
  --exclude-dir='@eaDir'
```

Also search for every old filename that was renamed.

No old reference should remain for the migrated diary.

---

## 19. Check for missing and unreferenced files

Compare:

* images referenced by the migrated diary HTML;
* images present under `files/diary-1831/images`;
* corresponding source material under the diary metadata.

Classify extra files as:

* intentionally retained but not currently referenced;
* candidate for future use;
* source-only material;
* duplicate;
* obsolete runtime file;
* uncertain.

Do not delete uncertain files during the first pass.

---

## 20. Remove the completed staging directory

Once the migrated diary has passed all tests:

```bash
rm -rf files/staging/diary-1831
```

Before running the command, list the directory and confirm that every required image is already present in the permanent runtime directory.

---

## 21. Remove obsolete shared runtime copies

Only after the diary has been fully tested in all required modes, identify obsolete copies under locations such as:

```text
files/images/
```

Before deleting a file:

1. Search all diaries for references to its old path and filename.
2. Confirm another diary does not still rely on it.
3. Confirm the diary-specific replacement exists.
4. Confirm the replacement checksum or visual content is correct.
5. Retain the pre-migration backup.

Delete only files that are proven to be obsolete.

---

## 22. Repeat for remaining diaries

Repeat the same process independently for:

```text
diary-1828-and-1829-and-jan-1830
diary-1830
diary-1832
diary-1834
```

Additional diaries found in the content tree should be assessed in the same way.

Complete and verify one diary before starting the next.

The large combined `diary-1828-and-1829-and-jan-1830` directory should be migrated only after the pilot diary has established that:

* the target path convention works;
* the application handles nested directories;
* the source-to-published relationship is understandable;
* the testing procedure is sufficient.

---

## 23. Generate an after-migration layout report

After each diary migration, generate an updated clean layout:

```bash
find . \
  -path '*/@eaDir' -prune -o \
  -name 'Thumbs.db' -prune -o \
  -print \
  | sort > ../file-layout-after-diary-1831.txt
```

Retain this report with the change-management evidence.

---

## 24. Document the image-management convention

Add a short project document explaining:

* source files belong under `diaries/<diary>/metadata`;
* runtime files belong under `files/<diary>/images`;
* editable projects must not be placed in the runtime directory;
* published filenames should be lower-case and URL-safe;
* the source and published basenames should match where practical;
* Synology-generated files must be ignored;
* migrations must be completed one diary at a time;
* old files must not be removed before verification.

A suitable location could be:

```text
diaries-documentation/image-file-organisation.md
```

or the existing documentation area used by the Diaries project.

---

# Acceptance criteria

The feature is complete when:

1. Runtime images are organised under:

   ```text
   files/<diary-name>/images/
   ```

2. Original images and editable Gimp or Inkscape sources remain under the corresponding diary’s `metadata` directory.

3. No `.xcf`, `.xmp`, source-only asset or Synology-generated file is required in the runtime `files` directory.

4. Published image filenames are URL-safe and follow the agreed naming convention.

5. A published image can be associated with its source material through its diary name and basename.

6. HTML fragments for each migrated diary reference the new diary-specific paths.

7. All migrated images load successfully in:

   * day-to-day development mode;
   * local Docker build mode;
   * local published-image smoke mode;
   * remote deployment, when deployed.

8. Browser and responder logs contain no missing-image errors for the migrated diary.

9. Direct requests to representative image URLs return HTTP 200 and the correct media type.

10. Old shared copies are removed only after all references have been checked.

11. Synology `@eaDir`, thumbnail, stream and `Thumbs.db` files are excluded from runtime content and migration archives.

12. The migration can be completed and recorded independently for each diary.

13. The image-file organisation convention is documented for future diary work.

---

# Out of scope

The following are not required by this feature:

* changing the visual design of diary pages;
* recompressing or resizing every image;
* converting all images to a new format;
* rebuilding missing Gimp or Inkscape projects;
* introducing a database-backed media catalogue;
* implementing an automated media-management user interface;
* changing diary identifiers or diary names;
* reorganising all non-image metadata;
* deleting source material whose purpose is uncertain.

These may be considered as separate changes after the file organisation has been stabilised.

---

# Risks and mitigations

## Risk: broken HTML references

**Mitigation:** Search for all references before renaming and test each changed diary in every supported mode.

## Risk: deleting the only editable source

**Mitigation:** Treat the diary metadata directory as authoritative and take a verified backup before migration.

## Risk: two diaries share one runtime image

**Mitigation:** Search the complete diary tree before removing any shared image. Duplicate the published output into each diary directory where independent ownership is clearer, while retaining only one authoritative source if appropriate.

## Risk: incorrect source-to-export relationship

**Mitigation:** Use matching basenames, retain final exports beside complex source projects and manually inspect uncertain cases.

## Risk: Synology files are mistaken for application files

**Mitigation:** Exclude `@eaDir`, `Thumbs.db`, `@SynoEAStream` and Synology thumbnail files from reports, ZIPs and migrations.

## Risk: different deployment modes expose files differently

**Mitigation:** Confirm the static-file path and volume mapping before changing HTML, then test all supported modes.

## Risk: large migration becomes unmanageable

**Mitigation:** Complete one diary at a time, beginning with a pilot diary and retaining a per-diary checklist.

---

# Suggested manual migration checklist

For each diary:

```text
[ ] Backup verified
[ ] Clean before-layout report generated
[ ] Runtime URL mapping confirmed
[ ] Referenced images inventoried
[ ] Source material identified
[ ] Complex source directories organised
[ ] Published filenames agreed
[ ] Final images copied to staging
[ ] Staged images visually checked
[ ] Images copied to permanent runtime directory
[ ] HTML references updated
[ ] Day-to-day development tested
[ ] Local Docker build tested
[ ] Published-image smoke test completed
[ ] Remote mapping checked
[ ] Old references searched
[ ] Missing files checked
[ ] Duplicate files reviewed
[ ] Staging directory removed
[ ] Obsolete shared copies removed
[ ] Clean after-layout report generated
[ ] Migration notes recorded
```
