# 0029 Step 3 — Retire redundant Marquee Page persistence (candidate)

**Status:** PREPARED, NOT DEPLOYED. Source based on `diaries-sources-20261126-114732.zip`.
No production changes performed or authorised. Step 2 acceptance evidence remains intact.

## Contract

- `fragment.page_id` is authoritative for DATED Fragments. `marquee` persists `fragment_id` and rectangle geometry/version only.
- `Marquee.getPage()` derives the Page through its Fragment. The persisted Marquee DTO contains no Page ID.
- The existing MQTT Marquee publication **retains** `pageId` and both topic paths for backward-compatible clients, but derives it from Fragment ownership. Incoming RPC pageId remains validated against the owning Fragment.
- Repository `findAllByPage` queries through Fragment; legacy 0022/0028 migration inventories choose the appropriate query based on the presence of `marquee.page_id`.

## Guarded migration

`tools/step3-retire-marquee-page-id.sql` requires the Step 2 hybrid schema, rejects orphaned or non-DATED owners and refuses any mismatch between `marquee.page_id` and `fragment.page_id`. It then drops the redundant column atomically. Run **after** production Step 2 data conversion, before starting a responder built from this candidate. The old responder requires the original column; do not roll back the application alone after the drop.

The complementary `tools/step3-restore-marquee-page-id.sql` rebuilds column values from authoritative Fragment pages, adds a foreign key and NOT NULL, but is **not** an alternative to the verified pre-migration database backup.

## Consolidated acceptance still required

1. Inspect applied source diff and preserve existing Windows submodule local changes.
2. Run responder unit and integration tests, client build/tests and reader build/tests once as a consolidated cycle. Test TEXT creation/update/delete, IMAGE with/without Marquee, Page ownership rejection, Marquee geometry update/delete, locks, MQTT retained aliases and full startup replay.
3. Against an isolated *copy* of the development database, verify the guarded schema migration, repository operations and rollback SQL. Do **not** drop the column from the live development database without an authorised coordinated restart and a recovery backup.
4. Verify the production Step 2 migration preflight's exact row-set guard and the current production backups before obtaining approval to deploy.
5. Deploy Playbooks MQTT annual ACL, schema conversion + Marquee column retirement and compatible responder/editor/reader as one coordinated release; capture postflight and rollback evidence.

**No tests or migration were executed in preparation of this package.**
