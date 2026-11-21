# 0051 Step 5 — supported operation and rollback boundary

**Prepared:** 21 November 2026. This is an operating reference, **not** permission to change production.

## Accepted active production stack (reported 21 Nov)

| Component | Image | Runtime |
| --- | --- | --- |
| Angular Editor / Day Reader | `rsmaxwell/diaries-client:0.0.9-build-79` | Healthy |
| Java responder | `rsmaxwell/diaries-responder:0.0.9-build-85` | Healthy |
| Public reader | `rsmaxwell/diaries-web:0.0.9-build-9` | Healthy |
| PostgreSQL / Mosquitto | `postgres:18-alpine` / `eclipse-mosquitto:2` | Healthy |

The production responder configuration sets `imageFragmentWritesEnabled=true` and `imageFragmentExtensionsWritesEnabled=true`. It supports optional IMAGE link and same-Page Marquee writes; both flags are implemented in the responder, not merely client UI options. Ansible render variables are `diaries_image_fragment_writes_enabled` and `diaries_image_fragment_extensions_writes_enabled` in the `mango` Playbooks checkout. **Do not edit generated `/config/responder.json` inside the running container** or bypass Ansible for permanent changes.

## Safe operational checks

**Windows Cygwin** (read-only, executes on `pluto`):

```bash
ssh pluto 'docker ps --filter "name=diaries-" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"'
ssh pluto 'docker exec diaries-responder grep -E "imageFragment(WritesEnabled|ExtensionsWritesEnabled)" /config/responder.json'
```

**Windows Cygwin** (read-only backup manifest status):

```bash
ssh mars 'sudo -n diaries-backup-status'
ssh backup 'sudo -n diaries-backup-status'
```

Manifest health and successful systemd service exit do not constitute a complete content-hash verification or test restore; consult the accepted backup evidence before destructive action.

## Data and rollback boundary

- **Before any extension-format record was written**, the protected rehearsal allowed temporarily returning to the former responder/reader after disabling extension writes; the additive schema column was preserved.
- **After an IMAGE link or IMAGE-with-Marquee state has been written** (the now-activated production capability), older client/responder/reader binaries are **not approved rollback targets**. Their previous invariants cannot safely represent all current records. Do not assume an old-image rollback is fixed by merely disabling the extension gate.
- Setting `diaries_image_fragment_extensions_writes_enabled: false` through Ansible may stop **new** link and optional-Marquee writes as an operational containment measure, but it **does not delete existing new-format records or restore backward compatibility**.
- For faults after activation, prefer a compatible forward fix or a tested compatible version. Any database/Files restore would require a **separate authorised recovery operation** against a verified consistent snapshot, with explicit consequences for subsequent writes and MQTT retained replay.
- Do not delete the nullable `image_link_url` column, rewrite or tombstone retained Fragment/Marquee links, or remove NAS files as a shortcut.

## UI boundaries

The Day Reader displays `Image ID: N` after Position for an IMAGE with positive `imageId`, then shows the catalogue image beneath the header, followed by transcription text. A valid per-Fragment external link navigates independently of selecting a source Page or highlighting an optional Marquee. Removing an IMAGE Marquee does not delete its Fragment, link or Image; deleting a Fragment never removes shared catalogue Image bytes. A legacy MARQUEE fragment containing an embedded `<img>` remains a separate 0028 migration candidate.

## Tooling classification and cleanup

- `change-control/in-progress/0051-FEAT .../tools/` and `/tests/`: **historical feature-specific test/rehearsal tools**; retain with the feature evidence at closure. Do not install them as permanent deployment/backup roles.
- 0028 v2 reviewer/test code belongs to **0028's feature-specific tools/tests**, not as a new normal-operation Playbooks role.
- Permanent operation stays with the deployed Diaries services, normal Compose/Ansible roles, established backup-status tools and long-lived docs/regression tests already in the application repositories.
- The Step 4 disposable Docker resources were reported cleaned by the harness; the normal Windows published-smoke database and NAS Files were deliberately **not** treated as disposable. No additional production helper removal has been verified by this report.
