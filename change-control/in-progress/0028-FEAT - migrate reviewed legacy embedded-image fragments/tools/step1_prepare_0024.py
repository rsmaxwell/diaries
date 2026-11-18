#!/usr/bin/env python3
"""Prepare 0028 Step 1 evidence for the *existing* 0024 read-only reconciler.

Converts current 0028 occurrence drafts to the legacy 0022-compatible CSV input
expected by Migration0024ImageCatalogue --0022-candidates. No approval is inferred.
Also reports how Page ownership is represented for the current candidates.

Run on mango; inputs and outputs contain private diary material. Python 3 stdlib.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from collections import Counter, defaultdict
from pathlib import Path


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    with path.open('rb') as stream:
        h = hashlib.sha256()
        for part in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(part)
        return h.hexdigest()


def checked_inputs(directory: Path) -> None:
    checksums = directory / 'SHA256SUMS.txt'
    if not checksums.is_file():
        raise ValueError('Missing input evidence SHA256SUMS.txt')
    entries = checksums.read_text(encoding='utf-8').splitlines()
    if not entries:
        raise ValueError('Input evidence checksum manifest is empty')
    seen = set()
    for entry in entries:
        if '  ' not in entry:
            raise ValueError('Malformed checksum manifest entry')
        digest, name = entry.split('  ', 1)
        if not (len(digest) == 64 and all(c in '0123456789abcdef' for c in digest)):
            raise ValueError('Malformed checksum digest')
        if not name or Path(name).name != name or name in seen:
            raise ValueError('Unexpected or duplicate checksum filename')
        seen.add(name)
        target = directory / name
        if not target.is_file() or sha_file(target) != digest:
            raise ValueError(f'Input evidence SHA256 mismatch: {name}')
    required = {'0028-dispositions.UNREVIEWED.csv', '0028-image-decisions.UNREVIEWED.csv',
                'current-schema-snapshot.PRIVATE.csv', '0028-summary.json'}
    if not required.issubset(seen):
        raise ValueError('Input evidence lacks a required hashed file')


def read_csv(path: Path, required: set[str]) -> list[dict[str, str]]:
    with path.open(newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream)
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f'{path.name}: missing required columns {required}')
        rows = list(reader)
        if any(None in row for row in rows):
            raise ValueError(f'{path.name}: unexpected extra columns')
        return rows


def prepare(inventory: Path, output: Path) -> dict:
    checked_inputs(inventory)
    summary = json.loads((inventory/'0028-summary.json').read_text(encoding='utf-8'))
    if summary.get('candidateCoverage') != 'UNREVIEWED - no mutation authorised':
        raise ValueError('Expected frozen UNREVIEWED collector output')
    disp = read_csv(inventory/'0028-dispositions.UNREVIEWED.csv',
                    {'fragment_id', 'disposition', 'embedded_image_count'})
    occur = read_csv(inventory/'0028-image-decisions.UNREVIEWED.csv',
                    {'fragment_id', 'embedded_image_ordinal', 'original_src',
                     'original_src_sha256', 'occurrence_action'})
    if not disp or not occur:
        raise ValueError('No candidate rows/occurrences available')
    disp_by_id = {}
    for row in disp:
        fid = row['fragment_id']
        if not fid.isdecimal() or fid in disp_by_id:
            raise ValueError('Duplicate or invalid disposition fragment ID')
        if row['disposition'].strip():
            raise ValueError('Source dispositions are no longer unreviewed')
        disp_by_id[fid] = row
    grouped = defaultdict(list)
    for row in occur:
        fid = row['fragment_id']
        if fid not in disp_by_id or not row['embedded_image_ordinal'].isdecimal():
            raise ValueError('Occurrence has unexpected fragment ID or ordinal')
        source = row['original_src']
        if sha_bytes(source.encode('utf-8')) != row['original_src_sha256']:
            raise ValueError('Occurrence source hash mismatch')
        if ' | ' in source:
            raise ValueError('Source contains legacy 0024 separator; requires separate review')
        if row['occurrence_action'].strip():
            raise ValueError('Source occurrences are no longer unreviewed')
        grouped[fid].append((int(row['embedded_image_ordinal']), source))
    if set(grouped) != set(disp_by_id):
        raise ValueError('Candidate/occurrence coverage mismatch')
    rows = []
    for fid in sorted(disp_by_id, key=int):
        entries = sorted(grouped[fid])
        ordinals = [ordinal for ordinal, _ in entries]
        if ordinals != list(range(1, len(entries) + 1)):
            raise ValueError(f'Nonconsecutive/duplicate ordinals for fragment {fid}')
        if int(disp_by_id[fid]['embedded_image_count']) != len(entries):
            raise ValueError('Occurrence count disagrees with disposition')
        rows.append({'database_fragment_id': fid,
                     'legacy_image_reference': ' | '.join(src for _, src in entries)})
    reported_counts = summary.get('counts', {})
    if len(rows) != reported_counts.get('unreviewed_legacy_candidates') or len(occur) != reported_counts.get('total_legacy_occurrences'):
        raise ValueError('Candidate counts differ from frozen inventory summary')
    snapshot = inventory/'current-schema-snapshot.PRIVATE.csv'
    by_id = {}
    with snapshot.open(newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ['kind','payload']:
            raise ValueError('Unexpected snapshot format')
        for row in reader:
            if row['kind'] != 'fragment':
                continue
            data = json.loads(row['payload'])
            fid = str(data['fragment_id'])
            if fid in disp_by_id:
                if fid in by_id:
                    raise ValueError('Duplicate fragment in inventory snapshot')
                by_id[fid] = data
    if set(by_id) != set(disp_by_id):
        raise ValueError('Candidate disappeared from inventory snapshot')
    ownership = Counter()
    for f in by_id.values():
        page = f.get('page_id')
        marquees = f.get('marquees') or []
        if page is not None:
            ownership['direct_page_id_populated'] += 1
            if len(marquees) == 1 and marquees[0].get('page_id') is not None:
                ownership['direct_page_and_marquee_page_both_populated'] += 1
                if page != marquees[0]['page_id']:
                    ownership['direct_marquee_page_mismatch'] += 1
        elif len(marquees) == 0:
            ownership['missing_page_no_marquee'] += 1
        elif len(marquees) > 1:
            ownership['missing_page_multiple_marquees'] += 1
        elif marquees[0].get('page_id') is None:
            ownership['missing_page_marquee_without_page'] += 1
        else:
            ownership['missing_page_one_marquee_with_page'] += 1
    result = {
        'schemaVersion': 1,
        'purpose': '0028 current candidate evidence converted to 0024 legacy input shape; NOT the historical 0022 inventory',
        'status': 'UNREVIEWED; DRY-RUN ONLY; NO MIGRATION AUTHORISED',
        'candidateRows': len(rows),
        'occurrenceRows': len(occur),
        'pageOwnership': dict(sorted(ownership.items())),
        'sourceInventorySummarySha256': sha_file(inventory/'0028-summary.json'),
        'sourceInventorySnapshotSha256': sha_file(snapshot),
        'sourceOccurrenceSha256': sha_file(inventory/'0028-image-decisions.UNREVIEWED.csv'),
        'sourceDispositionSha256': sha_file(inventory/'0028-dispositions.UNREVIEWED.csv'),
        'warning': 'Populated Page and Marquee IDs have NOT been verified against the Page table. All inferred associations need validation.',
    }
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    candidates = output/'0028-0024-candidates.PRIVATE.csv'
    with candidates.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=['database_fragment_id','legacy_image_reference'], lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    report = output/'0028-page-ownership-summary.json'
    report.write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    (output/'SHA256SUMS.txt').write_text(''.join(
        f'{sha_file(path)}  {path.name}\n' for path in (candidates, report)), encoding='utf-8')
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory', type=Path, required=True, help='Frozen 0028 private Step 1 inventory directory')
    parser.add_argument('--output', type=Path, required=True, help='New private Step 1 evidence directory')
    args = parser.parse_args()
    os.umask(0o077)
    result = prepare(args.inventory, args.output)
    print('PASS: prepared 0024 DRY-RUN candidate input', result['candidateRows'],
          'fragments /', result['occurrenceRows'], 'occurrences')
    print('Page ownership categories:', json.dumps(result['pageOwnership'], sort_keys=True))
    print('Output is PRIVATE and UNREVIEWED:', args.output)


if __name__ == '__main__':
    main()
