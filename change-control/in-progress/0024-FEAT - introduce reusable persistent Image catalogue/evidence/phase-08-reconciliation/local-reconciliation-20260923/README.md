# Local Image catalogue reconciliation — 2026-09-23

This directory archives the reviewed dry-run, committed apply and final
idempotency dry-run for the development database and configured NAS Files root.
It supersedes the unresolved **data findings** in the parent Phase 8 proof; it
does not replace that proof or satisfy the separate Phase 11 production gates.

## Result

| Step | Outcome |
| --- | --- |
| Reviewed dry-run | 71 existing catalogue matches, 12 creates, 4 unsupported `Thumbs.db` files and no conflicts |
| Apply | `COMMITTED`; 12 rows inserted as Image IDs 72–83 |
| Apply verification | 83 Image rows, zero remaining creates, zero metadata conflicts and complete candidate cross-reference |
| Final dry-run | 83 catalogue matches, zero creates, 4 unsupported `Thumbs.db` files and no conflicts |
| Final candidate cross-reference | 73 of 73 candidates matched exactly one Image: 3 exact-path and 70 unique local-suffix matches |

The final zero-create dry-run demonstrates that rerunning reconciliation against
the resulting state is idempotent. The utility did not create any
`ImageFragment` rows. It does not publish retained MQTT topics; normal responder
startup performs database replay.

## Repairs and corrections completed before the reviewed run

- Eleven PNG files had only invalid CRC values on ancillary `iCCP` chunks. The
  CRC fields were recalculated without changing image data or chunk payloads.
  `repairs-and-corrections/png-iccp-crc-repair-summary.json` links each original
  rejection hash to its repaired hash and final Image ID.
- `img2926-burnhopeside-hall.jpg` contained 1,573 zero bytes after its valid JPEG
  end marker. They were removed; the report records the original and repaired
  hashes, lengths and rendered-pixel comparison.
- The PNG stored as `img2805-blue-posts-pub.jpg` was renamed to `.png`, and the
  JPEG stored as `img3018-murder-of-nicholas-fairles.png` was renamed to `.jpg`.
  Image rows 65 and 68, the affected live Fragment 1461 reference, and the
  candidate inventory were updated together. The final candidate CSV also makes
  Fragment 1564's full diary-1832 path explicit.

The extension-correction report was emitted before the Fragment 1564 candidate
row was made explicit, so its `correctedCandidatesSha256` records the immediately
generated intermediate CSV. The archived CSV and every migration run use the
final SHA-256
`f12f69cd56797c50dec2fd73ff151de1734ebc15fa54eb2e3ac6ff9a041a43e0`.

## Contents

- `image-candidates-corrected-extensions.csv`: exact candidate input used by all
  three archived migration runs.
- `reviewed-dry-run/`: reviewed pre-apply evidence and the approved create plan.
- `committed-apply/`: apply output, created row IDs and post-commit verification.
- `final-idempotency-dry-run/`: independent post-apply scan proving zero pending
  creates and complete candidate coverage.
- `repairs-and-corrections/`: JSON audit reports for the prerequisite repairs and
  coordinated filename/database/reference correction.
- `SHA256SUMS.txt`: hashes for every archived file other than the manifest itself.

Each migration bundle retains its original `SHA256SUMS.txt`. The apply bundle's
`0024-file-inventory.csv` is the pre-commit scan bound to the reviewed plan;
`0024-post-apply-verification.json` and the final dry-run are the authoritative
post-commit state.

Image backup binaries are deliberately omitted. The reports preserve source and
result hashes, while the final inventory proves that the repaired files are the
bytes associated with the catalogue rows. The original image bytes were already
covered by the parent Phase 8 source-copy and conflict evidence.

## Integrity check

From this directory in PowerShell:

```powershell
Get-Content .\SHA256SUMS.txt | ForEach-Object {
    $expected, $relativePath = $_ -split '  ', 2
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $relativePath).Hash.ToLowerInvariant()
    if ($actual -ne $expected) { throw "Checksum mismatch: $relativePath" }
}
```

