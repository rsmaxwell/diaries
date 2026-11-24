#!/usr/bin/env python3
"""0028 Step 1: render PRIVATE HTML + source-derived suggestion portal from sealed v2 draft.

No database/network access. Does not alter the original draft, HTML or hashes.
Requires the unchanged SHA256SUMS-recorded v2 draft and the frozen,
SHA256-verified production snapshot. Exported reviewer edits are imported
later in the browser (not used as the sealed source here).
"""
import argparse
import json
import os
from pathlib import Path
from step4_0051_compatibility_review import SCHEMA, portal, sha, source_previews

OUTPUT_NAME = '0028-0051-review-v2.SOURCE-SUGGESTIONS.PRIVATE.html'
INPUT_NAME = '0028-0051-review-v2.DRAFT.PRIVATE.json'


def refresh(source, frozen_snapshot=None):
    if source.name != INPUT_NAME or not source.is_file():
        raise ValueError('Expected original 0028 v2 PRIVATE draft: ' + INPUT_NAME)
    sha_file = source.parent / 'SHA256SUMS.txt'
    if not sha_file.is_file():
        raise ValueError('Original source directory has no SHA256SUMS.txt')
    digests = {}
    for line in sha_file.read_text(encoding='utf-8').splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or '/' in parts[1] or '\\' in parts[1] or parts[1] in ('', '.', '..'):
            raise ValueError('Invalid original evidence checksum line')
        if parts[1] in digests:
            raise ValueError('Duplicate checksum filename')
        digests[parts[1]] = parts[0]
    if digests.get(source.name) != sha(source.read_bytes()):
        raise ValueError('Original v2 draft failed SHA256 evidence verification')
    doc = json.loads(source.read_text(encoding='utf-8'))
    if (doc.get('schema') != SCHEMA or doc.get('productionApplyAllowed') is not False or
        doc.get('review_status') != 'UNREVIEWED_V2' or not isinstance(doc.get('decisions'), list)):
        raise ValueError('Unexpected or potentially approved v2 input')
    if frozen_snapshot is None:
        frozen_snapshot = (source.parent.parent/'20261118T093606Z'/
                           'current-schema-snapshot.PRIVATE.csv')
    previews = source_previews(doc, frozen_snapshot)
    out = source.parent / OUTPUT_NAME
    if out.exists():
        raise FileExistsError('Refusing to overwrite existing private portal: ' + str(out))
    # Creation is exclusive; new file is PRIVATE; no evidence manifests modified.
    fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as stream:
            stream.write(portal(doc, previews))
    except BaseException:
        out.unlink(missing_ok=True)
        raise
    print('PASS: verified source-suggestion PRIVATE portal created (no migration authorised)')
    print('Occurrences with verified original HTML:', len(previews))
    print('Portal:', out)
    print('Original SHA256SUMS, frozen evidence and v2 draft were not modified')
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('sealed_v2_draft', type=Path, help='Original SHA256SUMS-verified v2 draft')
    ap.add_argument('--frozen-snapshot', type=Path,
                    help='Override frozen snapshot path (default: sibling 20261118T093606Z)')
    a = ap.parse_args()
    refresh(a.sealed_v2_draft, a.frozen_snapshot)


if __name__ == '__main__':
    main()
