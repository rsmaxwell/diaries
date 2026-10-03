# 0031 Step 2 — Decision rationale

## Why use a leaf selector rather than a complete NAS path?

`DIARIES_FILES_DIR` can be interpreted consistently by all local execution styles:

- Docker combines it with `DIARIES_NAS_CONTENT_PATH`;
- direct Windows development can use it as the effective responder `diaries.files` child beneath its existing root;
- Playbooks can render the same runtime contract from `diaries_files_dir`.

A Docker-specific full NAS path would require a second independently maintained concept for direct Windows development and would make database/Files pairing easier to get wrong.

## Why keep production at `files`?

Production already uses `.../diaries-content/files`. Renaming or moving that tree is unnecessary to satisfy the invariant and would add migration risk to the most important dataset.

The safer direction is:

```text
production:     keep existing root
non-production: create isolated roots
```

Production therefore remains `files` while non-production receives new directory names.

## Why give each committed local mode its own default?

The committed `.env` files are valid independently of the normal developer override. If `local.env` is absent, each local database default identifies a different durable database dataset. Giving each of those defaults a correspondingly distinct Files root preserves the invariant automatically.

This also makes the default configuration safe rather than relying on every developer to remember a local override.

## Why does the normal developer configuration still share one root?

The current workflow deliberately uses:

```text
./data/database/common
```

so the three local modes see the same durable database content while exercising different execution/deployment paths.

0031 does not require mode isolation when the modes are intentionally accessing one dataset. The correct pairing is therefore:

```text
./data/database/common <-> files-development-common
```

for all three modes.

Creating three Files roots while retaining one common database would be the opposite mismatch: one database could refer to bytes that differ according to which execution mode happened to be running.

## Why keep `diaries` shared?

The original diary scans are read-only source material and are not mutated by Image catalogue lifecycle operations. Sharing them does not create the cross-dataset deletion/replacement hazard that applies to mutable Files.

## Why not encode environment identity in `Image.relativePath`?

The database catalogue should describe logical content within its matched Files root, not deployment topology. Keeping `relativePath` environment-neutral allows a matched database + Files dataset to be cloned, backed up, restored or promoted without rewriting every Image record.

Environment selection therefore belongs in configuration, not persisted Image identity.
