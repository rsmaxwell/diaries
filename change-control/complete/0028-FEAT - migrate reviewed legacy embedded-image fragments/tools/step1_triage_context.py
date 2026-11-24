#!/usr/bin/env python3
"""0028 Step 1: offline, NON-AUTHORITATIVE same-date Page and 0022 history hints.

Consumes hash-verified, private, already collected evidence; zero DB/network calls.
Never changes reviewed decisions or writes a migration manifest.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path

from step1_make_review import (
    MANDATORY_FROZEN, MANDATORY_DERIVED, MANDATORY_0024,
    REVIEW_COLUMNS, as_id, capture, rows, sha, verified,
)

REVIEW_REQUIRED = {
    '0028-review-worksheet.PRIVATE.csv',
    '0028-review-dossier.PRIVATE.html',
    '0028-review-summary.json',
}

ADDED = [
    'triage_priority', 'candidate_page_context', 'date_other_page_count',
    'date_other_page_ids_HINT_ONLY', 'nearest_before_fragment_Hint',
    'nearest_before_page_Hint', 'nearest_after_fragment_Hint',
    'nearest_after_page_Hint', 'adjacent_page_agreement_HINT_ONLY',
    'historic_link_strength_HINT_ONLY', 'historic_source_key_HINT_ONLY',
    'historic_resolution_HINT_ONLY', 'historic_fragment_type_HINT_ONLY',
    'historic_review_date_HINT_ONLY', 'triage_required_checks',
]


def fragment_date(f: dict) -> str:
    return date(int(f['year']), int(f['month']), int(f['day'])).isoformat()


def order_key(f: dict):
    try:
        sequence = Decimal(str(f['sequence']))
    except (InvalidOperation, KeyError, TypeError) as exc:
        raise ValueError('Invalid fragment sequence in frozen snapshot') from exc
    if not sequence.is_finite():
        raise ValueError('Non-finite fragment sequence in frozen snapshot')
    return (sequence, int(as_id(str(f['fragment_id']))))


def page_anchor(f: dict) -> str:
    """Page from one unambiguous relationship; still NOT FK verification."""
    direct = f.get('page_id')
    marquees = f.get('marquees') or []
    if len(marquees) > 1:
        return ''
    via = marquees[0].get('page_id') if marquees else None
    if direct is not None and via is not None and direct != via:
        return ''
    page = direct if direct is not None else via
    return as_id(str(page)) if page is not None else ''


def date_context(f: dict, same_day: list[dict]) -> dict[str, str]:
    """No inferred owner; context from *other* fragments on the date only."""
    ordered = sorted(same_day, key=order_key)
    fkey = as_id(str(f['fragment_id']))
    if sum(as_id(str(x['fragment_id'])) == fkey for x in ordered) != 1:
        raise ValueError('Candidate must appear exactly once in same-date cohort')
    idx = next(i for i, x in enumerate(ordered) if as_id(str(x['fragment_id'])) == fkey)
    others = [x for x in ordered if as_id(str(x['fragment_id'])) != fkey]
    unique_pages = sorted({page_anchor(x) for x in others if page_anchor(x)}, key=int)
    left = next((x for x in reversed(ordered[:idx]) if page_anchor(x)), None)
    right = next((x for x in ordered[idx+1:] if page_anchor(x)), None)
    lpage, rpage = page_anchor(left) if left else '', page_anchor(right) if right else ''
    if f.get('page_id') is not None:
        category = 'HAS_DIRECT_PAGE_NOT_FK_VERIFIED'
    elif len(unique_pages) == 0:
        category = 'NO_PAGE_NO_DATE_ANCHORS'
    elif len(unique_pages) == 1:
        category = 'NO_PAGE_ONE_DATE_PAGE_HINT_ONLY'
    else:
        category = 'NO_PAGE_MULTIPLE_DATE_PAGES_HINT_ONLY'
    return {
        'candidate_page_context': category,
        'date_other_page_count': str(len(unique_pages)),
        'date_other_page_ids_HINT_ONLY': '|'.join(unique_pages),
        'nearest_before_fragment_Hint': str(left['fragment_id']) if left else '',
        'nearest_before_page_Hint': lpage,
        'nearest_after_fragment_Hint': str(right['fragment_id']) if right else '',
        'nearest_after_page_Hint': rpage,
        'adjacent_page_agreement_HINT_ONLY': ('BOTH_NEAREST_AGREE_NOT_PROOF' if lpage and lpage == rpage
                                              else 'NEAREST_DIFFER' if lpage and rpage else 'INSUFFICIENT'),
    }


def historic_index(ledger: dict) -> tuple[dict, dict]:
    if not isinstance(ledger, dict) or not isinstance(ledger.get('decisions'), list):
        raise ValueError('Historical 0022 review ledger has no decisions list')
    by_id = defaultdict(list)
    by_sha_date = defaultdict(list)
    for decision in ledger['decisions']:
        if not isinstance(decision, dict):
            raise ValueError('Malformed historical 0022 decision')
        provenance = decision.get('provenance') or {}
        if not isinstance(provenance, dict):
            raise ValueError('Malformed historical provenance')
        manifest = provenance.get('source_manifest') or {}
        if not isinstance(manifest, dict):
            raise ValueError('Malformed historical source manifest')
        ids = set()
        for value in (
            decision.get('database_fragment_id'),
            (provenance.get('database_reconciliation') or {}).get('database_fragment_id'),
            (provenance.get('source_reconciliation') or {}).get('database_fragment_id'),
        ):
            if value is not None and str(value) != '':
                ids.add(as_id(str(value)))
        # Contradictory old evidence is not strong identification.
        if len(ids) == 1:
            by_id[next(iter(ids))].append(decision)
        if ids:
            # Never apply a text-only hint to a different Fragment when
            # historical evidence already names a particular Fragment ID.
            continue
        digest = str(manifest.get('html_sha256') or '')
        day = str(manifest.get('date') or '')
        if len(digest) == 64 and all(ch in '0123456789abcdef' for ch in digest) and day:
            by_sha_date[(digest, day)].append(decision)
    return by_id, by_sha_date


def history(f: dict, index: tuple[dict, dict]) -> dict[str, str]:
    by_id, by_sha_date = index
    fid = as_id(str(f['fragment_id']))
    digest = hashlib.sha256((f.get('text') or '').encode('utf-8')).hexdigest()
    day = fragment_date(f)
    direct = by_id.get(fid, [])
    sha_matches = by_sha_date.get((digest, day), [])
    if len(direct) > 1:
        return history_blank('MULTIPLE_HISTORICAL_ID_RECORDS')
    if direct:
        decision = direct[0]
        source = (decision.get('provenance') or {}).get('source_manifest') or {}
        if str(source.get('date') or '') != day:
            status = 'ID_LINK_DATE_CONFLICT_REVIEW'
        elif source.get('html_sha256') == digest:
            status = 'ID_AND_HTML_SHA_AGREE_HISTORY_ONLY'
        else:
            status = 'ID_LINK_HTML_NOT_MATCHED_HISTORY_ONLY'
    elif len(sha_matches) > 1:
        return history_blank('MULTIPLE_HISTORICAL_SHA_RECORDS')
    elif sha_matches:
        decision = sha_matches[0]
        status = 'SAME_DATE_HTML_SHA_ONLY_HISTORY_ONLY'
    else:
        return history_blank('NO_UNIQUE_HISTORY_LINK')
    source = (decision.get('provenance') or {}).get('source_manifest') or {}
    return {
        'historic_link_strength_HINT_ONLY': status,
        'historic_source_key_HINT_ONLY': str(source.get('source_key') or ''),
        'historic_resolution_HINT_ONLY': str(decision.get('resolution') or ''),
        'historic_fragment_type_HINT_ONLY': str(decision.get('fragment_type') or ''),
        'historic_review_date_HINT_ONLY': str(decision.get('reviewed_at') or ''),
    }


def history_blank(status: str) -> dict[str, str]:
    return {
        'historic_link_strength_HINT_ONLY': status,
        'historic_source_key_HINT_ONLY': '',
        'historic_resolution_HINT_ONLY': '',
        'historic_fragment_type_HINT_ONLY': '',
        'historic_review_date_HINT_ONLY': '',
    }


def priority(row: dict, context: dict) -> tuple[str, str]:
    checks = ['REVIEW_ORIGINAL_HTML_AND_EMBEDDED_SOURCE', 'VALIDATE_SUFFIX_IMAGE_ID_PATH_CHECKSUM',
              'CHOOSE_DISPOSITION_AND_OCCURRENCE_ACTION', 'RECORD_REVIEWER_AND_EVIDENCE']
    if row['0024_status'] != 'MATCHED_ONE_IMAGE' or row['catalogue_cross_check'] != 'MATCHED_SNAPSHOT_AND_FILE':
        checks.append('RESOLVE_UNMATCHED_IMAGE_OR_DEFER')
        p = 'P0_IMAGE_AMBIGUOUS_OR_INVALID'
    elif row['page_ownership'] == 'NO_PAGE_NO_MARQUEE':
        checks.append('ESTABLISH_PAGE_OWNERSHIP_OR_DEFER')
        p = ('P1_UNOWNED_NO_DATE_PAGE_HINT' if context['date_other_page_count'] == '0'
             else 'P2_UNOWNED_DATE_CONTEXT_HINT_ONLY')
    elif row['page_ownership'] != 'DIRECT_AND_MARQUEE_AGREE':
        checks.append('INVESTIGATE_PAGE_RELATIONSHIP')
        p = 'P3_PAGE_RELATIONSHIP_REVIEW'
    else:
        checks.append('CONFIRM_PAGE_FK_AND_KEEP_OR_SPLIT_OR_CONVERT')
        p = 'P4_PAGE_AGREES_BUT_SUFFIX_UNREVIEWED'
    return p, '|'.join(checks)


def assemble(frozen: Path, derived: Path, review: Path, ledger: Path, output: Path) -> dict:
    if output.exists() or output.is_symlink():
        raise ValueError('Output directory already exists; refusing overwrite')
    # Keep generated private material alongside the existing private evidence.
    private_root = frozen.resolve().parent
    if not output.resolve().is_relative_to(private_root):
        raise ValueError('Output must be inside the existing private Step 1 evidence directory')
    frozen_hashes = verified(frozen, MANDATORY_FROZEN)
    derived_hashes = verified(derived, MANDATORY_DERIVED)
    xref_hashes = verified(derived/'0024-dry-run', MANDATORY_0024)
    review_hashes = verified(review, REVIEW_REQUIRED)
    report = json.loads((review/'0028-review-summary.json').read_text(encoding='utf-8'))
    if report.get('approvalStatus') != 'UNREVIEWED':
        raise ValueError('Unexpected review approval status')
    linked = report.get('inputEvidenceSha256') or {}
    expected = {
        'frozenSummary': frozen_hashes['0028-summary.json'],
        'frozenSnapshot': frozen_hashes['current-schema-snapshot.PRIVATE.csv'],
        'derivedPageSummary': derived_hashes['0028-page-ownership-summary.json'],
        '0024CrossReference': xref_hashes['0024-candidate-cross-reference.csv'],
        '0024FileInventory': xref_hashes['0024-file-inventory.csv'],
    }
    if linked != expected:
        raise ValueError('Review workbook references different input evidence')
    if not ledger.is_file() or ledger.is_symlink():
        raise ValueError('Historical 0022 review ledger unavailable')
    with ledger.open(encoding='utf-8-sig') as f:
        historic = json.load(f)
    by_historic = historic_index(historic)
    frags, _, _ = capture(frozen/'current-schema-snapshot.PRIVATE.csv')
    frozen_dispositions = rows(frozen/'0028-dispositions.UNREVIEWED.csv',
                                {'fragment_id','original_html_sha256'})
    canonical_ids = {as_id(r['fragment_id']) for r in frozen_dispositions}
    if len(canonical_ids) != len(frozen_dispositions):
        raise ValueError('Duplicate frozen candidate ID')
    data = rows(review/'0028-review-worksheet.PRIVATE.csv', set(REVIEW_COLUMNS))
    keys = [(as_id(r['fragment_id']), int(as_id(r['embedded_image_ordinal']))) for r in data]
    if len(keys) != len(set(keys)):
        raise ValueError('Duplicate review row identity')
    if {f for f, _ in keys} != canonical_ids:
        raise ValueError('Review rows do not cover candidate fragments')
    if len(data) != report['counts']['occurrences']:
        raise ValueError('Review occurrence count differs from evidence')
    cohorts = defaultdict(list)
    for f in frags.values():
        cohorts[fragment_date(f)].append(f)
    tally = Counter()
    extra_rows = []
    for row in data:
        fid = as_id(row['fragment_id'])
        f = frags.get(fid)
        if not f or hashlib.sha256((f.get('text') or '').encode('utf-8')).hexdigest() != row['original_html_sha256']:
            raise ValueError('Review HTML no longer matches frozen fragment')
        context = date_context(f, cohorts[fragment_date(f)])
        h = history(f, by_historic)
        pri, checks = priority(row, context)
        extras = {**context, **h, 'triage_priority': pri, 'triage_required_checks': checks}
        extra_rows.append({**row, **extras})
        tally[pri] += 1
        tally[context['candidate_page_context']] += 1
        tally['history_'+h['historic_link_strength_HINT_ONLY']] += 1
    extra_rows.sort(key=lambda r: (r['triage_priority'], r['date'], Decimal(r['sequence']), int(r['fragment_id']), int(r['embedded_image_ordinal'])))
    os.umask(0o077)
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    path = output/'0028-context-triage.PRIVATE.csv'
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_COLUMNS + ADDED,
                                lineterminator='\n', extrasaction='raise')
        writer.writeheader()
        for r in extra_rows:
            # Safe for spreadsheet viewers; original HTML and embedded URL are not
            # present here, but legacy source keys may be user-supplied strings.
            writer.writerow({k: "'"+str(v) if str(v).lstrip().startswith(('=', '+', '-', '@')) else v
                             for k, v in r.items()})
    summary = {
        'schemaVersion': 1,
        'purpose': 'Read-only 0028 Step 1 triage hints; NOT migration approval',
        'approvalStatus': 'UNREVIEWED',
        'generatedUtc': datetime.now(timezone.utc).isoformat(),
        'candidateOccurrences': len(data),
        'candidateFragments': len(canonical_ids),
        'counts': dict(sorted(tally.items())),
        'inputEvidenceSha256': {**expected, 'reviewWorksheet':review_hashes['0028-review-worksheet.PRIVATE.csv'],
                                'historicLedger': sha(ledger)},
        'interpretation': [
            'No date neighbour is proof of Page ownership; no FK Page-table lookup has occurred',
            'Historical 0022 ledger concerns a different earlier review and never authorises 0028',
            'All suffix-based Image matches require human validation of Image ID, path and checksum',
            'All decisions remain blank; this file is not an executable migration manifest',
            'Do not use P0-P4 as an automatic conversion priority or Page inference',
        ],
    }
    summary_file = output/'0028-context-summary.json'
    summary_file.write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    (output/'SHA256SUMS.txt').write_text(''.join(
        f'{sha(p)}  {p.name}\n' for p in (path, summary_file)), encoding='utf-8')
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--frozen', type=Path, required=True)
    p.add_argument('--derived', type=Path, required=True)
    p.add_argument('--review', type=Path, required=True)
    p.add_argument('--ledger', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    s = assemble(a.frozen,a.derived,a.review,a.ledger,a.output)
    print('PASS: read-only, private, UNREVIEWED triage complete')
    print('Candidates:', s['candidateFragments'], 'occurrences:', s['candidateOccurrences'])
    print('=== Aggregate triage only (no private IDs/paths) ===')
    for k, v in s['counts'].items():
        print(f'{k}: {v}')
    print('Evidence directory:', a.output)
    print('NO Page assignment, 0028 decision approval, database write or MQTT change')


if __name__ == '__main__':
    main()
