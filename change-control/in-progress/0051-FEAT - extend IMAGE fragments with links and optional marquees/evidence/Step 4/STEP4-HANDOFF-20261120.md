# 0051 Step 4 — handoff from closed Step 3

**Prepared:** 20 November 2026  
**Status:** OPEN, not implemented or tested in this receipt  
**Authority:** the accepted 0051 cross-component contract and Steps 1–3 closure evidence. 0028's current in-progress design and review drafts remain paused and are not approved for conversion.

## Current state and source caveat

The Windows responder, client and web reader have passing local/isolated evidence for the optional `imageLinkUrl` and same-Page IMAGE Marquee contract. The Step 2 migration was exercised twice on the disposable frozen fixture, but **the production schema is unchanged** and mixed-version deployment safety has not been demonstrated.

The last uploaded Diaries source bundle (`diaries-sources-20261120-095555.zip`) predates the Step 2/3 change packages. The Windows checkout contains uncommitted changes in 0028/0029 and the three submodules have independent revisions. Do not overwrite the current 0028 working files from the earlier bundle. Before editing Step 4 source, obtain/inspect a refreshed source bundle or the authoritative Windows working files and record `git status`, parent and submodule revisions. Do not assume the checkout on `mango` has the same revisions.

## Migration-handoff implementation (non-destructive first)

1. Update 0028's **currently edited** design, implementation steps, versioned reviewed manifests/templates and checker/portal logic to preserve `imageLinkUrl` and a valid existing Marquee (identity, Page and geometry) as explicitly reviewed outcomes. Replace the obsolete invariant that IMAGE prohibits Marquees. Do **not** silently convert previous `CONVERT_TO_IMAGE` / `SPLIT_MARQUEE_AND_IMAGE` decisions, or automatically approve pending draft rows.
2. Add explicit per-occurrence source-link extraction with reviewed HTTP(S) destination and exact value round-trip. Preserve query/fragment components; capture link evidence from the reviewed original HTML, without fetching external URLs or exposing private diary text in public reports. Distinguish **no link**, **preserve link**, and **explicitly cleared link**; do not infer removal from omitted fields.
3. Make Marquee handling explicit: preserve, remove if independently reviewed, or absent. Verify existing Fragment/Marquee Page identities, association and geometry. A preserved Marquee must not generate an MQTT tombstone or lose its ID/version; shared Image and file bytes remain untouched.
4. Update synthetic migrated examples and the 0028 checker to reject stale Fragment versions, mismatched source/URL hashes, invalid URL, unresolved ownership, duplicate/cross-Page Marquees and accidental differences to dates, text and ordering. Version any transformed review draft and present a differences report. Leave unresolved candidates as `DEFER` / the appropriate approved exception.
5. Preserve the existing 0028 source observations (including 30 historical linked-image cases and 22 observed with Marquees) as historical only; do not treat them as a fresh production inventory or change their review status. Feature 0028 remains PAUSED until 0051 production capability is accepted and its own apply gate approved.

## Compatible rollout rehearsal and production gate

- Check current Windows Git/submodule state, frozen source bundle age, runtime image identities and the real Playbooks deployment roles/variables before preparing a change. Keep Diaries and Playbooks changes in distinct, repository-relative ZIPs.
- Rehearse the additive schema upgrade on an isolated restored fixture and verify the approved backup/hash and preserved existing values. Reuse the accepted Step 2 result where it already proves correctness; do not repeat expensive full restores unless a different rehearsal capability is required.
- Rehearse a **coordinated compatible responder + client + web** rollout with `imageFragmentExtensionsWritesEnabled` **false** initially. Verify old-writer/consumer compatibility and activation order, retained replay, source-page highlighting, link navigation, status/health, and rollback. Avoid activation if incompatible writers are still active.
- Exercise local-docker-build and local-published-smoke with actual component build/image IDs. Record which rollback combinations cease to be safe once `image_link_url` and IMAGE+Marquee states have been written. Preserve the additive schema; do not drop it to imitate rollback.
- Only after evidence, backup verification and explicit rollout approval, perform controlled production deployment and gate activation; record deployment log, container identities, health, permission checks, DB schema and MQTT retained-state receipts.

## Acceptance and preservation

Place Step 4 commands, results, migration diffs, environment revisions and rollback receipts in `evidence/Step 4/`; keep private original HTML, captions, links, reviewer decisions and production identifiers out of public ZIPs. Production data mutations, snapshots/deletion, publication and 0028 conversion each require their own authorised gates. Do not mark 0051 complete or unpause 0028 based solely on this handoff note.
