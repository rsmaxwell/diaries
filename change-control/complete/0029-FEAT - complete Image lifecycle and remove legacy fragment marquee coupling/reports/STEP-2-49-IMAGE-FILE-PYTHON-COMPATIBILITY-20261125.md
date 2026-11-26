# Step 2: Image audit Python compatibility correction (2026-11-25)

The development audit failed before hashing because the Cygwin Python runtime lacks `Path.is_relative_to()` (Python 3.9+). Replace the check with `Path.relative_to()` inside `try/except ValueError`, preserving the restriction that evidence output must not be under Files root. No database or image modifications.

Local checks: patched Python source compiled successfully; ZIP integrity verified. Actual checksum audit remains pending rerun on Windows.
