#!/usr/bin/env python3
"""Assemble a private, inert 0028 Step 1 review workbook from frozen evidence.

The outputs are NOT approved migration manifests and contain no automatic
conversion decisions. No network/DB access; hash verification before reading.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import html
import json
import os
from pathlib import Path
import re

MANDATORY_FROZEN = {
    '0028-dispositions.UNREVIEWED.csv', '0028-image-decisions.UNREVIEWED.csv',
    '0028-structural-exceptions.csv', '0028-summary.json',
    'current-schema-snapshot.PRIVATE.csv',
}
MANDATORY_DERIVED = {'0028-0024-candidates.PRIVATE.csv', '0028-page-ownership-summary.json'}
MANDATORY_0024 = {
    '0024-candidate-cross-reference.csv', '0024-file-inventory.csv',
    '0024-summary.json', '0024-create-plan.json',
    '0024-post-apply-verification.json', '0024-conflicts.csv',
}
REVIEW_COLUMNS = [
    'fragment_id', 'embedded_image_ordinal', 'date', 'sequence',
    'fragment_type_before', 'page_id', 'marquee_id', 'page_ownership',
    'expected_fragment_version', 'original_html_sha256',
    'original_src_sha256', '0024_status', '0024_match_method',
    'catalogue_image_id_hint', 'catalogue_relative_path_hint',
    'catalogue_checksum_hint', 'file_integrity_status',
    'catalogue_cross_check', 'structural_flags', 'review_blockers',
    'review_disposition', 'review_occurrence_action',
    'review_page_resolution', 'review_suffix_mapping', 'review_text_allocation',
    'review_notes', 'reviewed_by', 'reviewed_at',
]

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def verified(directory: Path, required: set[str]) -> dict[str, str]:
    if not directory.is_dir() or directory.is_symlink():
        raise ValueError(f'Missing/non-directory evidence: {directory}')
    checks = directory/'SHA256SUMS.txt'
    if not checks.is_file() or checks.is_symlink():
        raise ValueError(f'Missing evidence checksum list: {directory}')
    seen: dict[str, str] = {}
    for line in checks.read_text(encoding='utf-8').splitlines():
        matched = re.fullmatch(r'([0-9a-f]{64})  ([^/\\]+)', line)
        if not matched:
            raise ValueError('Malformed evidence checksum line')
        digest, name = matched.groups()
        if name in ('', '.', '..', 'SHA256SUMS.txt') or name in seen:
            raise ValueError('Duplicate/invalid checksum item')
        target = directory / name
        if not target.is_file() or target.is_symlink() or sha(target) != digest:
            raise ValueError(f'Missing/mismatched evidence file: {name}')
        seen[name] = digest
    if not required.issubset(seen):
        raise ValueError(f'Missing required hashed evidence: {sorted(required - set(seen))}')
    return seen

def rows(path: Path, needed: set[str]) -> list[dict[str, str]]:
    with path.open(newline='', encoding='utf-8-sig') as f:
        rd = csv.DictReader(f)
        if not needed.issubset(set(rd.fieldnames or [])):
            raise ValueError(f'Missing columns in {path.name}: {sorted(needed-set(rd.fieldnames or []))}')
        items = list(rd)
    if any(None in item or any(v is None for v in item.values()) for item in items):
        raise ValueError(f'Malformed CSV row in {path.name}')
    return items

def as_id(value: str) -> str:
    if not str(value).isdecimal() or int(value) < 1:
        raise ValueError('Invalid numeric ID or occurrence ordinal')
    return str(int(value))

def capture(snapshot: Path):
    out_f, out_i, identity = {}, {}, []
    for r in rows(snapshot, {'kind','payload'}):
        data = json.loads(r['payload'])
        if r['kind'] == 'fragment':
            key = as_id(str(data['fragment_id']))
            if key in out_f:
                raise ValueError('Duplicate fragment snapshot ID')
            out_f[key] = data
        elif r['kind'] == 'image':
            key = as_id(str(data['image_id']))
            if key in out_i:
                raise ValueError('Duplicate image snapshot ID')
            out_i[key] = data
        elif r['kind'] == 'identity':
            identity.append(data)
        else:
            raise ValueError('Unexpected snapshot kind')
    if len(identity) != 1:
        raise ValueError('Expected one snapshot identity')
    return out_f, out_i, identity[0]

def esc(v):
    return html.escape(str(v if v is not None else ''), quote=True)

def page_status(fragment):
    direct = fragment.get('page_id')
    marquees = fragment.get('marquees') or []
    if len(marquees) > 1:
        return 'MULTIPLE_MARQUEES_REVIEW'
    via = marquees[0].get('page_id') if marquees else None
    if direct is not None and via is not None:
        return 'DIRECT_AND_MARQUEE_AGREE' if direct == via else 'DIRECT_MARQUEE_DISAGREE'
    if direct is not None:
        return 'DIRECT_PAGE_PRESENT_NOT_FK_VERIFIED'
    if via is not None:
        return 'MARQUEE_ONLY_PAGE_NOT_FK_VERIFIED'
    return 'NO_PAGE_NO_MARQUEE' if not marquees else 'NO_PAGE_MARQUEE_WITHOUT_PAGE'

def assemble(frozen: Path, derived: Path, output: Path) -> dict:
    if output.exists():
        raise ValueError('Output already exists; refusing overwrite')
    source_hashes = verified(frozen, MANDATORY_FROZEN)
    input_hashes = verified(derived, MANDATORY_DERIVED)
    result_dir = derived/'0024-dry-run'
    xref_hashes = verified(result_dir, MANDATORY_0024)
    summary = json.loads((frozen/'0028-summary.json').read_text(encoding='utf-8'))
    page_summary = json.loads((derived/'0028-page-ownership-summary.json').read_text(encoding='utf-8'))
    reconcile = json.loads((result_dir/'0024-summary.json').read_text(encoding='utf-8'))
    if summary.get('candidateCoverage') != 'UNREVIEWED - no mutation authorised':
        raise ValueError('Frozen inventory is no longer an unreviewed snapshot')
    if page_summary.get('sourceInventorySnapshotSha256') != source_hashes['current-schema-snapshot.PRIVATE.csv']:
        raise ValueError('Derived Page report references a different source snapshot')
    if page_summary.get('sourceOccurrenceSha256') != source_hashes['0028-image-decisions.UNREVIEWED.csv']:
        raise ValueError('Derived Page report references different occurrences')
    if page_summary.get('sourceDispositionSha256') != source_hashes['0028-dispositions.UNREVIEWED.csv']:
        raise ValueError('Derived Page report references different dispositions')
    if page_summary.get('sourceInventorySummarySha256') != source_hashes['0028-summary.json']:
        raise ValueError('Derived Page report references a different summary')
    if (reconcile.get('mode') != 'dry-run' or
            reconcile.get('outcome') != 'DRY_RUN_COMPLETE' or
            reconcile.get('insertedRows', 0) != 0):
        raise ValueError('0024 evidence does not attest read-only DRY_RUN_COMPLETE')
    verification = json.loads((result_dir/'0024-post-apply-verification.json').read_text(encoding='utf-8'))
    if verification.get('verified') is not True or verification.get('candidateCrossReferenceComplete') is not True:
        raise ValueError('0024 verification is not complete')
    dispositions = rows(frozen/'0028-dispositions.UNREVIEWED.csv', {'fragment_id','embedded_image_count','disposition','original_html_sha256','page_id','marquee_id','expected_fragment_version'})
    occurrences = rows(frozen/'0028-image-decisions.UNREVIEWED.csv', {'fragment_id','embedded_image_ordinal','original_src_sha256','original_src','occurrence_action'})
    refs = rows(result_dir/'0024-candidate-cross-reference.csv', {'fragmentId','candidateIndex','sourceSha256','imageId','relativePath','status','matchMethod'})
    file_inv = rows(result_dir/'0024-file-inventory.csv', {'relativePath','imageId','status','sha256'})
    flags = rows(frozen/'0028-structural-exceptions.csv', {'fragment_id','issue'})
    frags, imgs, identity = capture(frozen/'current-schema-snapshot.PRIVATE.csv')
    by_disp, by_occ, by_ref = {}, {}, {}
    flagged = defaultdict(set)
    for r in flags:
        flagged[as_id(r['fragment_id'])].add(r['issue'])
    for r in dispositions:
        fid = as_id(r['fragment_id'])
        if fid in by_disp or r['disposition'].strip():
            raise ValueError('Duplicate or already-approved disposition row')
        if fid not in frags:
            raise ValueError('Disposition not in snapshot')
        f = frags[fid]
        if str(f['version']) != str(r['expected_fragment_version']):
            raise ValueError('Stale fragment version')
        text_hash = hashlib.sha256((f.get('text') or '').encode('utf-8')).hexdigest()
        if text_hash != r['original_html_sha256']:
            raise ValueError('Fragment HTML hash mismatch')
        if str(f.get('page_id') or '') != r['page_id']:
            raise ValueError('Fragment Page differs from frozen disposition')
        marquees = f.get('marquees') or []
        expected_marquee = str(marquees[0]['id']) if len(marquees) == 1 else ''
        if expected_marquee != r['marquee_id']:
            raise ValueError('Marquee identity differs from frozen disposition')
        by_disp[fid] = r
    for r in occurrences:
        key = (as_id(r['fragment_id']), int(as_id(r['embedded_image_ordinal'])))
        if key in by_occ or r['occurrence_action'].strip() or key[0] not in by_disp:
            raise ValueError('Duplicate/preapproved/unknown occurrence')
        if hashlib.sha256(r['original_src'].encode('utf-8')).hexdigest() != r['original_src_sha256']:
            raise ValueError('Source hash mismatch')
        by_occ[key] = r
    for r in refs:
        key = (as_id(r['fragmentId']), int(as_id(r['candidateIndex'])))
        if key in by_ref:
            raise ValueError('Duplicate 0024 cross-reference identity')
        by_ref[key] = r
    if set(by_ref) != set(by_occ):
        raise ValueError('0024 cross-reference coverage mismatch')
    if {fid for fid, _ in by_occ} != set(by_disp):
        raise ValueError('Disposition/occurrence candidate coverage mismatch')
    for fid, r in by_disp.items():
        seq = sorted(n for key, n in by_occ if key == fid)
        if seq != list(range(1, len(seq)+1)) or int(r['embedded_image_count']) != len(seq):
            raise ValueError('Occurrence ordinals/count drift')
    if len(by_disp) != summary['counts']['unreviewed_legacy_candidates'] or len(by_occ) != summary['counts']['total_legacy_occurrences']:
        raise ValueError('Current occurrence totals changed')
    if len(by_disp) != page_summary['candidateRows'] or len(by_occ) != page_summary['occurrenceRows']:
        raise ValueError('Derived evidence totals changed')
    file_by_path = defaultdict(list)
    for r in file_inv:
        file_by_path[r['relativePath']].append(r)
    workbook = []
    tally = Counter()
    invalid_fids = set()
    for key in sorted(by_occ, key=lambda k: (int(k[0]),k[1])):
        fid, ordinal = key
        f = frags[fid]
        d = by_disp[fid]
        occ = by_occ[key]
        ref = by_ref[key]
        if ref['sourceSha256'] != occ['original_src_sha256']:
            raise ValueError('0024 cross-reference source SHA mismatch')
        page = page_status(f)
        tally['page_'+page] += 1
        status, method, path, image_id = (ref[k] for k in ('status','matchMethod','relativePath','imageId'))
        tally['match_'+status+'__'+method] += 1
        integrity = 'NOT_MATCHED'
        catalogue_check = 'NOT_RESOLVED'
        checksum = ''
        blockers = set()
        if status == 'MATCHED_ONE_IMAGE':
            if not image_id:
                raise ValueError('0024 matched status without Image ID')
            image_rec = imgs.get(as_id(image_id))
            if image_rec is None:
                blockers.add('IMAGE_ROW_NOT_IN_FROZEN_SNAPSHOT')
                catalogue_check = 'SNAPSHOT_IMAGE_MISSING'
            else:
                inventory_rows = [row for row in file_by_path.get(path, []) if row['imageId'] == image_id]
                if len(inventory_rows) != 1:
                    blockers.add('FILE_EVIDENCE_NOT_UNIQUE')
                    integrity = 'MISSING_OR_DUPLICATE_FILE_EVIDENCE'
                else:
                    integrity = inventory_rows[0]['status']
                    if integrity != 'CATALOGUED_MATCH':
                        blockers.add('FILE_INTEGRITY_NOT_CATALOGUED_MATCH')
                checksum = image_rec.get('checksum') or ''
                if image_rec.get('relative_path') != path or not checksum or not inventory_rows or inventory_rows[0]['sha256'] != checksum:
                    blockers.add('CATALOGUE_OR_FILE_MISMATCH')
                    catalogue_check = 'MISMATCH'
                else:
                    catalogue_check = 'MATCHED_SNAPSHOT_AND_FILE'
        else:
            blockers.add('IMAGE_REFERENCE_UNRESOLVED')
            invalid_fids.add(fid)
        if method != 'EXACT':
            blockers.add('SUFFIX_MAPPING_REVIEW_REQUIRED')
        if page in ('NO_PAGE_NO_MARQUEE','NO_PAGE_MARQUEE_WITHOUT_PAGE'):
            blockers.add('PAGE_OWNERSHIP_UNRESOLVED')
        if page.endswith('NOT_FK_VERIFIED') or page == 'DIRECT_AND_MARQUEE_AGREE':
            blockers.add('PAGE_FK_NOT_VERIFIED')
        if page == 'DIRECT_MARQUEE_DISAGREE' or page == 'MULTIPLE_MARQUEES_REVIEW':
            blockers.add('PAGE_RELATION_CONFLICT')
        if f.get('lock_user_id') is not None or f.get('lock_session_id'):
            blockers.add('LOCK_FIELDS_PRESENT')
        for item in flagged[fid]:
            if item not in {'UNEXPECTED_FRAGMENT_TYPE','MISSING_PAGE_ID'}:
                blockers.add('STRUCTURAL_'+item)
        tally['blocker_rows'] += bool(blockers)
        tally['catalogue_cross_check_'+catalogue_check] += 1
        tally['integrity_'+integrity] += 1
        line = {
            'fragment_id': fid, 'embedded_image_ordinal': ordinal,
            'date': f"{int(f.get('year') or 0):04d}-{int(f.get('month') or 0):02d}-{int(f.get('day') or 0):02d}",
            'sequence': str(f.get('sequence') or ''),
            'fragment_type_before': str(f.get('type') or 'NULL'),
            'page_id': str(f.get('page_id') or ''),
            'marquee_id': d['marquee_id'], 'page_ownership': page,
            'expected_fragment_version': d['expected_fragment_version'],
            'original_html_sha256': d['original_html_sha256'],
            'original_src_sha256': occ['original_src_sha256'],
            '0024_status': status, '0024_match_method': method,
            'catalogue_image_id_hint': image_id,
            'catalogue_relative_path_hint': path,
            'catalogue_checksum_hint': checksum, 'file_integrity_status': integrity,
            'catalogue_cross_check': catalogue_check,
            'structural_flags': '|'.join(sorted(flagged[fid])),
            'review_blockers': '|'.join(sorted(blockers)),
            'review_disposition': '', 'review_occurrence_action': '',
            'review_page_resolution': '', 'review_suffix_mapping': '',
            'review_text_allocation': '', 'review_notes': '',
            'reviewed_by': '', 'reviewed_at': '',
        }
        workbook.append(line)
    if invalid_fids:
        tally['fragments_with_unresolved_image'] = len(invalid_fids)
    # These outputs may contain private paths and text: never print them.
    os.umask(0o077)
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    worksheet_path = output/'0028-review-worksheet.PRIVATE.csv'
    with worksheet_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_COLUMNS, lineterminator='\n', extrasaction='raise')
        writer.writeheader()
        writer.writerows({k: ("'" + str(v) if str(v).lstrip().startswith(('=', '+', '-', '@')) else v) for k, v in row.items()} for row in workbook)
    dossier_path = output/'0028-review-dossier.PRIVATE.html'
    cells = [
        '<!doctype html><html lang="en"><head><meta charset="utf-8">',
        '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; img-src \'none\'; form-action \'none\';">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<title>0028 Step 1 — PRIVATE review dossier</title>',
        '<style>body{font:15px system-ui,sans-serif;line-height:1.45;max-width:1100px;margin:2em auto;padding:0 1em;color:#20242a}article{border:1px solid #bbb;margin:1em 0;padding:1em;border-radius:8px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f4f6;padding:1em;border-radius:4px}dl{display:grid;grid-template-columns:max-content 1fr;gap:.25em 1em}dt{font-weight:bold}.warn{color:#a54b09}a{color:#154a80}</style>',
        '</head><body><h1>0028 Step 1 — PRIVATE, UNREVIEWED dossier</h1>',
        '<p>This document is read-only evidence for human review. HTML from legacy fragments is shown as escaped text, not rendered. No images, scripts, remote resources, forms or active links are loaded. The CSV worksheet holds blank decisions. Do not commit this private dossier to Git.</p>',
        f'<p>Fragments: {len(by_disp)}; occurrences: {len(by_occ)}. No conversion authorised.</p>',
    ]
    for line in workbook:
        fid, ordinal = line['fragment_id'], line['embedded_image_ordinal']
        fragment = frags[fid]
        occ = by_occ[(fid, int(ordinal))]
        cells.extend([
            f'<article id="f{fid}-{ordinal}"><h2>Fragment {esc(fid)} · image {esc(ordinal)}</h2>',
            f'<p><strong>Date:</strong> {esc(line["date"])} · <strong>Page:</strong> {esc(line["page_id"] or "(missing)")} · <strong>Marquee:</strong> {esc(line["marquee_id"] or "(missing)")}</p>',
            '<dl>',
        ])
        for k in ('page_ownership','0024_status','0024_match_method','catalogue_image_id_hint','catalogue_relative_path_hint','catalogue_checksum_hint','file_integrity_status','catalogue_cross_check','review_blockers'):
            cells.append(f'<dt>{esc(k)}</dt><dd>{esc(line[k])}</dd>')
        cells.extend(['</dl><h3>Original source URL (inert text)</h3>',f'<pre>{esc(occ["original_src"])}</pre>',
                      '<h3>Original fragment HTML (inert escaped text)</h3>',f'<pre>{esc(fragment.get("text") or "")}</pre>',
                      '<p class="warn">Decision remains UNREVIEWED; edit only the separate CSV review worksheet, not frozen evidence.</p></article>'])
    cells.append('</body></html>')
    dossier_path.write_text(''.join(cells)+'\n', encoding='utf-8')
    result = {
        'schemaVersion': 1, 'purpose': '0028 Step 1 review aids; NOT executable manifests',
        'approvalStatus': 'UNREVIEWED', 'generatedUtc': datetime.now(timezone.utc).isoformat(),
        'counts': {'candidateFragments': len(by_disp), 'occurrences': len(by_occ), **dict(sorted(tally.items()))},
        'inputEvidenceSha256': {
            'frozenSummary': source_hashes['0028-summary.json'],
            'frozenSnapshot': source_hashes['current-schema-snapshot.PRIVATE.csv'],
            'derivedPageSummary': input_hashes['0028-page-ownership-summary.json'],
            '0024CrossReference': xref_hashes['0024-candidate-cross-reference.csv'],
            '0024FileInventory': xref_hashes['0024-file-inventory.csv'],
        },
        'limits': [
            'All 0024 source matches are review hints, not approval',
            'Page referential integrity cannot be independently proved by the frozen snapshot',
            'Historical 0022 candidate CSV is not established by these inputs',
            'This document is not a migration manifest and the reviewer fields remain blank',
            'Any input changes require regeneration and separate review; no automatic transformation',
        ],
    }
    summary_path = output/'0028-review-summary.json'
    summary_path.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    (output/'SHA256SUMS.txt').write_text(''.join(
        f'{sha(p)}  {p.name}\n' for p in (worksheet_path, dossier_path, summary_path)), encoding='utf-8')
    return result

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--frozen', type=Path, required=True)
    p.add_argument('--derived', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    report = assemble(a.frozen,a.derived,a.output)
    print('PASS: PRIVATE, UNREVIEWED review aids generated')
    print(json.dumps(report['counts'], indent=2))
    print('Evidence dir:', a.output)
    print('NO migration approval or database mutation')

if __name__ == '__main__':
    main()
