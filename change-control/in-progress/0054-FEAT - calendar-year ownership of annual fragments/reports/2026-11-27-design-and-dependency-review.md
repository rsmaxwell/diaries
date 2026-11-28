# 0054 design/dependency review — 2026-11-27

## Verified in provided source snapshot

- `diaries-responder/.../model/Fragment.java`: nullable `page`, explicit nullable `diary` mapped to `diary_id`, `year/month/day`, placement, IMAGE, sequence and lock fields. `getDiaryId()` resolves explicit `diary` before Page-derived Diary.
- `diaries-responder/.../handlers/AddAnnualFragment.java`: validates no Page/Marquee/month/day, **requires `diaryId` and `year`**, sets `month=1`, `day=1`, persists Diary association and publishes via `FragmentPublishDTO`.
- `diaries-web/.../model/FragmentItem.java`: validates annual placement has no Page/Marquee and **requires `diaryId`**; validates a complete LocalDate even for annual placement.
- Existing 0053 plan in prior review explicitly positions annual content at each **Diary/year** boundary; this must change to **year** scope after 0054.

## Design questions to settle in Step 1

1. Physical-volume provenance: preserve old association as optional `sourceDiaryId`, as audit-only migration provenance, or both? Never overload ownership.
2. `month/day` representation for annual fragments: nullable fields and DTO changes versus documented placeholder kept for legacy transport compatibility.
3. Annual ordering: `(year, placement, sequence, id)` and editing behaviour when several volumes originally supplied annual sections.
4. Consumer compatibility and deployment ordering for existing Reader/client/responder versions; retained records are persistent and schema interpretation must be safe.
5. Historical duplicate/ambiguous rows and relation to prior 0029 work; validate against actual database, not bundle alone.

## Coordination with 0053

- 0054 owns model/migration and annual year-level projection compatibility; it does **not** add calendar-first Reader navigation.
- 0053 begins implementing new year/month routes **after 0054 is accepted**, consumes its final payload and year-scoped ordering, and must never reintroduce Diary-owned annual sections or require Page/Marquee for them.
- Keep separate feature documentation and evidence; one coordinated integration test plan can reuse accepted results without treating the two features as a single change-control item.

## Accepted editor navigation decision — 2026-11-27

The editor remains **physical-Diary-oriented**: select a physical Diary first, then open its Annual editorial content panel/dialog. Within that editor, explicitly select a calendar year and PREAMBLE/EPILOGUE. The selected Diary is navigation context (and may provide grounded year suggestions), not the owner or filter for annual content.

For a completely new Diary with no dates or Pages, allow manual year selection and annual CRUD without creating fictitious dated content. If multiple physical Diaries span a year, both entry points display/edit the identical year-owned collection. Do not infer provenance from whichever Diary opened the UI. Preserve existing editing and locking capabilities; panel versus dialog presentation may be chosen during implementation so long as these behaviours are tested.

This resolves the editor bootstrapping concern without altering 0053's calendar-first **public Reader** scope. These decisions are incorporated in the 0054 README, implementation steps and acceptance criteria; they are design approval, **not evidence of implementation or test completion**.

## Terminology decision (2026-11-27)

Approved name: **EPILOGUE**, replacing the earlier **POSTAMBLE** term in the target design. This is a whole-contract rename, not display-only. The deployed legacy literal `POSTAMBLE` must be recognised and migrated during the coordinated 0054 database/MQTT cutover, without an enduring alias. No runtime change has yet been made.
