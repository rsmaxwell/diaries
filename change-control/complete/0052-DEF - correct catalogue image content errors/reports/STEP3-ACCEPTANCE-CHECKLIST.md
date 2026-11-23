# 0052-DEF — Step 3 consolidated acceptance checklist

This checklist is deliberately **not** an acceptance receipt. The operator must record the results and supporting evidence from the current Windows and `pluto` systems. The source bundle inspected to construct these checks was captured at 2026-11-23 08:23, before the final Step 2 changes, so the scripts do not claim to represent a later Windows working tree.

## Already confirmed through user evidence (2026-11-23)

- Step 2 replacement of Image 3 / Image 18 and their production/development catalogue rows: successful application and tests in the earlier execution record.
- Both production normal image URLs return the approved SHA-256 after a targeted Cloudflare purge.
- The owner visually confirmed both corrected pictures in the production Editor and confirmed they remain correct after restoring Edge's normal caching.

## Run the remaining automated read-only check

From **Windows 11 — Cygwin Bash**, in the parent Diaries repo root:

```bash
bash 'change-control/in-progress/0052-DEF - correct catalogue image content errors/tools/verify-0052-step3-readonly.sh'
```

The tool writes a timestamped private evidence folder containing Git identity/status, the **production/development `public.image` metadata**, NAS file hashes for Images 3/18 and protected 21/25, and `RESULT.txt`. It requires the development database container to be running, the Windows `P:` NAS share to be mounted, and working `ssh pluto` access. It makes **no production or development writes** except local change-control evidence files.

The script does **not** publish to MQTT, restart processes, manipulate snapshots, purge CDN caches, or change any catalogue record. A failed check must be inspected rather than treated as success.

## Retained MQTT metadata (manual read-only inspection)

Using an existing read-only MQTT client connected to each environment's broker (e.g. MQTT Explorer), inspect **`diaries/images/3`** and **`diaries/images/18`**. Compare their `id`, `version`, `relativePath`, `mimeType`, `width`, `height` and `checksum` with the corresponding rows in the captured `production-catalogue.txt` / `development-catalogue.txt`.

Expected corrected identities:

| Image | Type | Width x height | SHA-256 |
| --- | --- | --- | --- |
| 3 — Whitley Park | `image/jpeg` | 776 x 502 | `71263a0b4b8ed3bac18dd650d841c165a58f23d11717f7399b1139811b7b10fc` |
| 18 — Hermitage | `image/png` | 720 x 480 | `9cbe68505a023ad9db4898914c5bf763cce4fb33b6689364586350d58d6411e0` |

Do not assume version 1 is correct without comparing the broker publication with the actual row. The source DTO does not expose byte size; that is verified through the file hash and the earlier HTTP evidence instead.

## Visual and behavioural acceptance

- [ ] Production public Reader — diary **20 March 1828**, `img2840`: correct historical Whitley Park map wherever Image 3 / legacy Fragment 84 is displayed, and existing selection/link/Marquee behaviour preserved.
- [ ] Production public Reader — diary **8 July 1829**, `img2900`: correct Hermitage picture for legacy Fragment 598, with caption and chronological position preserved. Do not mistake St Isaac Fragment 606 for the corrected Hermitage image.
- [ ] Development Editor — both dates: correct Whitley Park and Hermitage pictures after normal refresh; expected fragment and Marquee behaviour.
- [ ] Image 3 full-size / catalogue preview and Image 18 preview show the replacements; existing protected images 21 / 25 still look unchanged.
- [ ] Retained MQTT metadata checks passed in production and development.
- [ ] Relevant app health/logs show no new errors and there are no unexpected changes to image references/fragment chronology.
- [ ] Preserve the existing 0028 frozen review and record the changed image identities for later Fragment 598 review, without running 0028 conversion.
- [ ] Owner explicitly accepts the consolidated evidence and formal 0052 closure; only then move this feature to `complete/`.

All screenshots, private logs and reconciled evidence belong in this feature's private Step 3 evidence directory, not in Playbooks or a home-directory evidence store.
