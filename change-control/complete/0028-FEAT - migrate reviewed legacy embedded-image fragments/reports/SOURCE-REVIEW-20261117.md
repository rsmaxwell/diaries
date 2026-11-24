# 0028 — Source review and readiness baseline (17 November 2026)

## Evidence examined

- `diaries-sources-20261117-185710.zip`, `SOURCE-REVISIONS.txt` generated
  2026-11-17 18:57:17 UTC. Its authoritative Windows parent is `main`
  `73c173db865ca3c95d5e0091706c58f5fda1ea9b`.
- Source snapshot submodules: `diaries-client` at
  `e45ae170017fdf4974f642f654d7f709269af711`, `diaries-responder` at
  `bd65d08435c0f5d240337cd6479cb41befe4d8c1`, `diaries-web` at
  `cc147426e93ee6952558b65147e444d38316b3ce`.
- Parent Git status in **bundle manifest**, not an independent live check:
  tracked deletion of `change-control/todo/0028.../README.md` and new
  untracked `change-control/in-progress/`; the move must be staged/committed
  deliberately, not reset.
- `playbook-sources-20261117-185515.zip` source revisions show Ansible
  controller `28e394b48ba91479b147452d70adb39ff3b84559`, Playbooks
  `b0063d455faf4b264504405f9db72ab21c692741`, inventory
  `ebcce026723db37b9b53b76ba21903a351d48466`. No Playbooks code change
  is presently indicated. The bundle does not include private inventory.
- The source ZIP omits Git internals, so checkout status cannot be verified
  directly in the extracted copy; rerun source-control preflight before code.

## Implemented preconditions

1. 0022 source has `Migration0022Inventory` and `LegacyImageDetector`; its
   historic documentation warns that `<img>` detection alone cannot classify.
2. 0024 source has `ImageReconciler`, `CandidateCrossReference`,
   `ImagePathPolicy`, `Migration0024ImageCatalogue` and `Image` catalogue code.
   `CandidateCrossReference` may report `UNIQUE_LOCAL_SUFFIX` — review is
   essential before any such match is accepted.
3. 0025 persistence/0026 web/0027 editor provide first-class IMAGE contracts.
   0027 README documents full production IMAGE authoring enablement on
   2026-10-06, client image `0.0.9-build-76`, responder `0.0.9-build-84`,
   reader `0.0.9-build-8` **as historic rollout identities**, not verified
   current production versions.
4. Fragment persistence has `page_id`, nullable `type`, optional `image_id`,
   and separate Marquee association. `Marquee.page_id` still exists.
5. `FragmentSequenceNormaliser` and repository use date-wide order and
   four-decimal sequence with versioned updates. New insertion must not use
   per-Page-only renumbering.
6. `FragmentPublishDTO` and `MarqueePublishDTO` demonstrate exact retained
   topics; the normal `Synchronise` path can reconcile retained messages to
   DB state, including pruning orphan keys.

## What is *not* established by this upload

- Actual 0022 production-generated `0022-legacy-image-candidates.csv` or
  `0022-inventory.csv`: **not present** in source ZIP.
- Actual 0024 production-generated
  `0024-candidate-cross-reference.csv` / final reconciliation report:
  **not present** in source ZIP.
- The count of current embedded-image candidates, individual reviewed matches,
  current database contents/versions, active locks, Files integrity, live MQTT
  state and deployed current application versions: **not measured**.
- Any restored rehearsal, freshly verified pre-migration production recovery
  point, production writer-stop or 0028 apply: **not performed**.
- The screenshot after source-bundle generation shows the 0028 design and steps
  filenames; these newer local contents cannot be inferred from the bundle.

## Design decisions to implement, verify and accept

| Risk / gap | Resolution in design | Verification required |
|---|---|---|
| Historic CSV drift and existing IMAGE creations | Fresh read-only DB/Files inventory + lineage comparison, explicitly exclude non-legacy IMAGE | Diff candidate coverage and current type/page/Marquee |
| Path ambiguity or 0024 suffix match | Exact path+Image ID+checksum; reviewed exceptions only | Negative test for suffix/basename ambiguity |
| Original text corruption | Parse nodes with verifiable source spans, remove only reviewed tags | Byte/character diffs; malformed HTML/Unicode fixtures |
| Date-wide sequence and versions | Lock whole date, inject in `(sequence,id)` order, renumber once | Test mixed existing IMAGE/MARQUEE same date |
| Partial split/crash/re-run | Per-date DB transaction + durable unique journal | Failure injection, resume and idempotent readback |
| MQTT diverges from DB | Offline DB apply, then controlled responder replay/tombstones | Compare retained canonical/date/marquee/tree topics |
| Production rollback would erase later writes | Writer-stop, matched backup/Files snapshot, tested restore before reopening writes | Record rollback window and rehearsed readback |

## Implementation package boundary

This ZIP contains planning documentation, report/readiness record, test matrix,
empty reviewed-manifest **templates** and folder READMEs. It changes **no
application code, database, image files, Playbooks or live system**. Its files
must be compared with any newer Windows working-tree copies in Beyond Compare.
