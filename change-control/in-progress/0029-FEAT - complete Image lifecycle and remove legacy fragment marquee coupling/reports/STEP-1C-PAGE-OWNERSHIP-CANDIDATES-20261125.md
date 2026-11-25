# Step 1C — Page ownership candidate discovery (2026-11-25)

**Status: prepared / awaiting execution.** This is a read-only investigation; no Page IDs have been approved or assigned.

## Established facts

- Approved target model: every TEXT or IMAGE Fragment belongs to a Page, and optional Marquee identifies a physical position.
- Development has 60 Page-less Fragments; production has 11. All 11 production IDs also occur in development.
- All have nonempty HTML/text. Production 0028 journal references none of its 11 Page-less Fragments. Preserve content.
- Current `Page` source exposes `id`, `diary`, `name`, `sequence`, not a Page date. The date fields `year/month/day` are on Fragments. Date-derived Page suggestions are **not authoritative**.

## Outputs and decision

Run the packaged SQL against both environments. Record candidate Pages based on existing dated Fragments and nearby dated Pages. Zero candidates, multiple candidates, and opening-page material require manual mapping to scanned Pages / reader presentation.

**Do not update or delete anything** based solely on candidate matches. Also review whether development-only embedded-HTML image Fragments are superseded by 0028 before associating them. Approved Page mapping must preserve Fragment sequence and avoid duplicating already-migrated image content.

## Checks prior to a later migration

1. Resolve all 11 production records to explicitly verified Pages, or document an intentional new Page/cover where no physical Page exists.
2. Compare development-only 49 against 0028 image replacements rather than treating as live editorial content by default.
3. Produce a reviewed ID-to-Page mapping, content disposition and guarded, reversible correction; separate environment-specific expected counts.
4. Verify reader/editor and MQTT presentation before adding NOT NULL constraints.

No correction, deployment, acceptance gate or production backup claim is made by this report.
