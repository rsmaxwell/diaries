# Step 1 collector test notes

`test_step1_inventory.py` uses synthetic examples, *never production diaries*.
Run with `python3 -m unittest discover -s tests -p test_step1_inventory.py -v`
from this feature directory (or use the absolute repository-root command in
`tools/STEP1-COLLECTION-RUNBOOK.md`). It verifies:

- `<img>` discovery with repeated sources, case variation, HTML entities and
  missing `src`;
- preserving original Fragment ID, version, Page, Marquee and date in the
  **unreviewed** drafts without making decisions automatically;
- exclusion of already-typed IMAGE rows from conversion candidates;
- comparison with a fabricated historic candidate ID set;
- rejection of duplicated Fragment IDs;
- text of SQL limited to a read-only `COPY ... TO STDOUT` shape.

The remote PostgreSQL service, actual database schema and Files-integrity scan
have **not** been exercised by these local tests. Capture separate results when
run on mango and pluto. No state change is authorised.
