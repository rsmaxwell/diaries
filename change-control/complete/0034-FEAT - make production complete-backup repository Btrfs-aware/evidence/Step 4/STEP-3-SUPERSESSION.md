# Step 3 historical result and architecture supersession

Step 3 capability detection and mode-selection regression suites passed. Production `pluto` preflight identified the current repository filesystem as ext4 and selected `full-copy` under `auto`. These were valid results for the original design, and their evidence must remain intact.

Subsequent confirmation of the actual ext4 `pluto` → Btrfs `mars` → Btrfs `backup` topology means source-side reflink capture is **not the mechanism for sharing extents across whole-backup snapshots**. The Step 3 runtime probe/selection is obsolete for the revised fixed-path publisher and will be explicitly retired in Step 8 after compatibility tests. This is **supersession, not a failed test, not implemented reflink copy, and not proof of Btrfs deployment**. Do not enable `required-btrfs` on `pluto` for the new path.
