#!/usr/bin/env python3
"""0028 Step 1: read-only current-schema inventory and UNAPPROVED review drafts.

Run on mango from the Diaries parent repository. The SQL executes on the
production PostgreSQL service via pluto SSH; no executable is copied to pluto.
Outputs contain private diary HTML and must remain uncommitted/access-controlled.
Python 3 stdlib only; does not change PostgreSQL, Files or MQTT.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

DISPOSITION_HEADER = [
    'fragment_id', 'expected_fragment_version', 'page_id', 'marquee_id',
    'fragment_type_before', 'year', 'month', 'day', 'sequence',
    'original_html_sha256', 'embedded_image_count', 'disposition',
    'review_note', 'reviewed_by', 'reviewed_at',
]
OCCURRENCE_HEADER = [
    'fragment_id', 'embedded_image_ordinal', 'original_src',
    'original_src_sha256', 'resolved_relative_path', 'match_method',
    'resolved_image_id', 'expected_image_checksum', 'occurrence_action',
    'image_text', 'review_note',
]

# One read-only COPY statement is a single PostgreSQL statement-level snapshot.
# Do not silently add UPDATE, DDL, or any command that creates database objects.
COPY_SQL = r"""COPY (
SELECT kind, payload
FROM (
    SELECT 'fragment'::text AS kind, f.id AS sort_id,
           json_build_object(
             'fragment_id',f.id, 'version',f.version, 'page_id',f.page_id,
             'type',f.type, 'image_id',f.image_id,
             'year',f.year,'month',f.month,'day',f.day,
             'sequence',f.sequence::text,'text',f.text,
             'lock_user_id',f.lock_user_id,'lock_session_id',f.lock_session_id,
             'lock_timestamp',f.lock_timestamp,
             'marquees', COALESCE((SELECT json_agg(json_build_object(
                          'id',m.id,'page_id',m.page_id,
                          'version',m.version,'x',m.x,'y',m.y,
                          'width',m.width,'height',m.height) ORDER BY m.id)
                        FROM marquee m WHERE m.fragment_id=f.id), '[]'::json)
           )::text AS payload
    FROM fragment f
    UNION ALL
    SELECT 'image'::text, i.id,
           json_build_object('image_id',i.id, 'version',i.version,
             'relative_path',i.relative_path, 'checksum',i.checksum,
             'mime_type',i.mime_type, 'width',i.width, 'height',i.height
           )::text
    FROM image i
    UNION ALL
    SELECT 'identity'::text, 0::bigint,
           json_build_object('database',current_database(),
             'postgres_version',current_setting('server_version'),
             'snapshot_at',transaction_timestamp())::text
) inventory
ORDER BY kind, sort_id
) TO STDOUT WITH (FORMAT CSV, HEADER TRUE)"""


def digest(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda: f.read(1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


class ImgParser(HTMLParser):
    """Discovery ONLY. Not safe for HTML source-span edits in Step 2."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.sources: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'img':
            self.sources.append(next((v if v is not None else ''
                          for k, v in attrs if k.lower() == 'src'), ''))

    handle_startendtag = handle_starttag


def image_sources(html: str) -> list[str]:
    parser = ImgParser()
    parser.feed(html)
    parser.close()
    return parser.sources


def write_csv(path: Path, header: list[str], rows: list[dict]):
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=header, extrasaction='ignore', lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def read_ids(path: Path | None, alternatives: tuple[str, ...]) -> set[int] | None:
    if path is None:
        return None
    with path.open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fields = set(reader.fieldnames or ())
        key = next((k for k in alternatives if k in fields), None)
        if key is None:
            raise ValueError(f'{path.name}: missing ID column; expected {alternatives}')
        ids = set()
        for n, row in enumerate(reader, 2):
            value = (row.get(key) or '').strip()
            if not value:
                raise ValueError(f'{path.name} row {n}: empty {key}')
            try:
                ident = int(value)
            except ValueError as exc:
                raise ValueError(f'{path.name} row {n}: invalid {key}') from exc
            if ident in ids:
                raise ValueError(f'{path.name} row {n}: duplicate ID {ident}')
            ids.add(ident)
        return ids


def collect(host: str, compose_dir: str, db_service: str, target: Path):
    # SSH command uses stdin as a non-interactive script; no /tmp transfer.
    # psql is inside the deployed database service and takes credentials from
    # that service's own environment. PGOPTIONS prohibits even accidental writes.
    # Compose directory uses $HOME expansion on the remote; do not pass shell
    # expansions from untrusted CLI inputs into this script.
    if not (compose_dir.startswith('$HOME/') and all(
            ch.isalnum() or ch in '_./-' for ch in compose_dir[6:])):
        raise ValueError('--compose-dir must be $HOME/<simple relative path>')
    if not (db_service.replace('-', '').replace('_', '').isalnum()):
        raise ValueError('--db-service must be alphanumeric, hyphen or underscore')
    directory_suffix = compose_dir[len('$HOME/'):]
    remote = f'''#!/bin/sh
set -eu
cd "$HOME/{directory_suffix}"
test -r compose.yaml
test -r .env
sql=$(cat <<'STEP1_COPY_SQL'
{COPY_SQL}
STEP1_COPY_SQL
)
docker compose --file compose.yaml --env-file .env exec -T {db_service} sh -c 'export PGOPTIONS="-c default_transaction_read_only=on -c statement_timeout=600000"; exec psql -X -q -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$1"' sh "$sql"
'''
    with target.open('wb') as f:
        run = subprocess.run(['ssh', '-T', host, 'sh', '-s'], input=remote.encode('utf-8'),
                             stdout=f, stderr=subprocess.PIPE, timeout=900)
    if run.returncode:
        raise RuntimeError(f'SSH/Compose/psql failed ({run.returncode}); stderr: '
                           + run.stderr.decode('utf-8', errors='replace')[:3000])


def read_review_ledger(path: Path | None) -> set[int] | None:
    if path is None:
        return None
    data = json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(data.get('decisions'), list):
        raise ValueError('Historic review ledger missing decisions list')
    # Supplemental historical hints, NOT the actual 0022 candidates report.
    ids = set()
    for item in data['decisions']:
        if item.get('fragment_type') != 'IMAGE':
            continue
        fid = item.get('database_fragment_id')
        if fid is not None:
            if int(fid) in ids:
                raise ValueError('Historic review ledger contains duplicate IMAGE Fragment ID')
            ids.add(int(fid))
    return ids


def read_0024_hints(path: Path | None) -> list[dict] | None:
    if path is None:
        return None
    with path.open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        required = {'fragmentId', 'sourceSha256', 'imageId', 'relativePath', 'status', 'matchMethod'}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError(f'{path.name}: missing 0024 cross-reference fields')
        return list(reader)


def analyse(snapshot: Path, out: Path, historical: Path | None,
            ledger: Path | None = None, xref: Path | None = None):
    fragments = []
    images = []
    identity = []
    with snapshot.open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != ['kind', 'payload']:
            raise ValueError('Snapshot must have columns kind,payload')
        for lineno, row in enumerate(reader, 2):
            if row.get('kind') not in ('fragment', 'image', 'identity'):
                raise ValueError(f'Snapshot record {lineno}: unexpected kind')
            data = json.loads(row['payload'])
            if row['kind'] == 'fragment':
                fragments.append(data)
            elif row['kind'] == 'image':
                images.append(data)
            else:
                identity.append(data)
    if len(identity) != 1:
        raise ValueError('Expected exactly one database identity record')
    fragment_ids = [int(f['fragment_id']) for f in fragments]
    image_ids = [int(i['image_id']) for i in images]
    if len(fragment_ids) != len(set(fragment_ids)) or len(image_ids) != len(set(image_ids)):
        raise ValueError('Duplicate Fragment or Image IDs in snapshot')
    historical_ids = read_ids(historical, ('fragment_id', 'database_fragment_id'))
    historic_review_ids = read_review_ledger(ledger)
    crossref = read_0024_hints(xref)
    counts = Counter()
    issues = []
    disp = []
    occ = []
    current_candidates = set()
    current_image_with_embedded = set()
    image_lookup = {int(i['image_id']): i for i in images}
    rows_by_id = {int(r['fragment_id']): r for r in fragments}
    for f in sorted(fragments, key=lambda r: int(r['fragment_id'])):
        fid = int(f['fragment_id'])
        ftype = (f.get('type') or '').upper()
        html = f.get('text') or ''
        srcs = image_sources(html)
        marquee = f.get('marquees') or []
        counts['type_' + (ftype or 'NULL')] += 1
        if len(marquee) > 1:
            issues.append({'fragment_id': fid, 'issue': 'MULTIPLE_MARQUEES', 'detail': str(len(marquee))})
        # 0051 permits an IMAGE with one same-Page Marquee; this is no longer an anomaly.
        if ftype == 'MARQUEE' and f.get('image_id') is not None:
            issues.append({'fragment_id': fid, 'issue': 'MARQUEE_HAS_IMAGE_ID', 'detail': ''})
        if ftype not in ('MARQUEE', 'IMAGE'):
            issues.append({'fragment_id': fid, 'issue': 'UNEXPECTED_FRAGMENT_TYPE', 'detail': ftype or 'NULL'})
        if f.get('page_id') is None:
            issues.append({'fragment_id': fid, 'issue': 'MISSING_PAGE_ID', 'detail': ''})
        if len(marquee) == 1 and marquee[0].get('page_id') != f.get('page_id'):
            issues.append({'fragment_id': fid, 'issue': 'PAGE_MARQUEE_MISMATCH', 'detail': ''})
        if f.get('image_id') is not None and int(f['image_id']) not in image_lookup:
            issues.append({'fragment_id': fid, 'issue': 'MISSING_REFERENCED_IMAGE_ROW', 'detail': ''})
        if f.get('lock_user_id') is not None or f.get('lock_session_id'):
            issues.append({'fragment_id': fid, 'issue': 'LOCK_FIELDS_PRESENT', 'detail': 'review before apply'})
        if not srcs:
            continue
        counts['fragments_with_embedded_img'] += 1
        if len(srcs) > 1:
            counts['fragments_with_multiple_img'] += 1
        if ftype == 'IMAGE':
            current_image_with_embedded.add(fid)
            counts['existing_IMAGE_with_embedded_img'] += 1
            issues.append({'fragment_id': fid, 'issue': 'EXISTING_IMAGE_HAS_EMBEDDED_IMG', 'detail': 'excluded from 0028 draft; inspect'})
            continue
        current_candidates.add(fid)
        counts['unreviewed_legacy_candidates'] += 1
        disp.append({
            'fragment_id': fid, 'expected_fragment_version': f['version'],
            'page_id': f.get('page_id') or '',
            'marquee_id': marquee[0]['id'] if len(marquee) == 1 else '',
            'fragment_type_before': ftype,
            'year': f['year'], 'month': f['month'], 'day': f['day'],
            'sequence': f['sequence'], 'original_html_sha256': digest(html),
            'embedded_image_count': len(srcs),
            'disposition': '', 'review_note': '', 'reviewed_by': '', 'reviewed_at': '',
        })
        for ordinal, src in enumerate(srcs, 1):
            occ.append({'fragment_id': fid, 'embedded_image_ordinal': ordinal,
                        'original_src': src, 'original_src_sha256': digest(src),
                        'resolved_relative_path': '', 'match_method': '',
                        'resolved_image_id': '', 'expected_image_checksum': '',
                        'occurrence_action': '', 'image_text': '', 'review_note': ''})
    # Historic source candidates that no longer contain an embedded img remain
    # unresolved review work, rather than silently disappearing from coverage.
    if historical_ids is not None:
        for fid in sorted(historical_ids - current_candidates):
            f = rows_by_id.get(fid)
            if f is None or (f.get('type') or '').upper() == 'IMAGE':
                continue
            if image_sources(f.get('text') or ''):
                continue  # guarded against any unexpected classification change
            marquee = f.get('marquees') or []
            disp.append({
                'fragment_id': fid, 'expected_fragment_version': f['version'],
                'page_id': f.get('page_id') or '',
                'marquee_id': marquee[0]['id'] if len(marquee) == 1 else '',
                'fragment_type_before': (f.get('type') or '').upper(),
                'year': f['year'], 'month': f['month'], 'day': f['day'],
                'sequence': f['sequence'],
                'original_html_sha256': digest(f.get('text') or ''),
                'embedded_image_count': 0, 'disposition': '', 'review_note': '',
                'reviewed_by': '', 'reviewed_at': '',
            })
            issues.append({'fragment_id': fid,
                           'issue': 'HISTORIC_CANDIDATE_NOW_ZERO_IMG',
                           'detail': 'explicit zero-image review justification required'})
            counts['historic_candidates_with_zero_current_img'] += 1
    disp.sort(key=lambda r: int(r['fragment_id']))
    counts['unreviewed_disposition_rows'] = len(disp)
    # These are intentionally blank drafts. Reviewers must populate every field
    # before Step 2's manifest validator can approve a migration.
    write_csv(out / '0028-dispositions.UNREVIEWED.csv', DISPOSITION_HEADER, disp)
    write_csv(out / '0028-image-decisions.UNREVIEWED.csv', OCCURRENCE_HEADER, occ)
    write_csv(out / '0028-structural-exceptions.csv', ['fragment_id', 'issue', 'detail'], issues)
    counts['total_fragments'] = len(fragments)
    counts['total_images'] = len(images)
    counts['total_legacy_occurrences'] = len(occ)
    counts['structural_exceptions'] = len(issues)
    summary = {
        'schemaVersion': 1, 'tool': '0028-step1-readonly-inventory',
        'databaseIdentity': identity[0],
        'inputSnapshotSha256': file_hash(snapshot),
        'historic0022CandidateCsvPresent': historical is not None,
        'historic0022CandidateCsvSha256': file_hash(historical) if historical else None,
        'historic0022ReviewLedgerSha256': file_hash(ledger) if ledger else None,
        'historic0024CrossReferenceSha256': file_hash(xref) if xref else None,
        'counts': dict(sorted(counts.items())),
        'candidateCoverage': 'UNREVIEWED - no mutation authorised',
        '0024FileIntegrity': 'NOT CHECKED by this database-only tool',
        'warning': 'HTMLParser is for discovery only; not a source-span editing parser',
    }
    if historical_ids is not None:
        drift = []
        for fid in sorted(historical_ids - current_candidates):
            drift.append({'fragment_id': fid, 'status':
                          'NOW_IMAGE_WITH_EMBEDDED_IMG' if fid in current_image_with_embedded else
                          'NO_LONGER_CURRENT_LEGACY_CANDIDATE'})
        for fid in sorted(current_candidates - historical_ids):
            drift.append({'fragment_id': fid, 'status': 'NEW_CURRENT_LEGACY_CANDIDATE'})
        write_csv(out / '0028-0022-candidate-drift.csv', ['fragment_id', 'status'], drift)
        summary['historic0022Count'] = len(historical_ids)
        summary['historicStillCandidateCount'] = len(historical_ids & current_candidates)
        summary['historicalNoLongerCandidateCount'] = len(historical_ids - current_candidates)
        summary['newCurrentCandidateCount'] = len(current_candidates - historical_ids)
    if historic_review_ids is not None:
        summary['historicLedgerImageDecisionHints'] = len(historic_review_ids)
        summary['historicLedgerHintsStillCurrent'] = len(historic_review_ids & current_candidates)
        summary['historicLedgerHintsNotCurrent'] = len(historic_review_ids - current_candidates)
        summary['historicLedgerIsNot0022CandidateCsv'] = True
        drift = [
            {'fragment_id': fid, 'status':
             'REVIEW_HINT_STILL_CURRENT' if fid in current_candidates else 'REVIEW_HINT_NOT_CURRENT'}
            for fid in sorted(historic_review_ids)
        ]
        write_csv(out / '0028-historic-ledger-hints.csv', ['fragment_id', 'status'], drift)
    if crossref is not None:
        real_occ = {(str(item['fragment_id']), item['original_src_sha256']) for item in occ}
        matches = []
        for item in crossref:
            fid, srch = item['fragmentId'], item['sourceSha256']
            image = image_lookup.get(int(item['imageId'])) if item['imageId'] else None
            matches.append({
                'fragment_id': fid,
                'source_sha256': srch,
                'xref_status': item['status'],
                'xref_method': item['matchMethod'],
                'xref_relative_path': item['relativePath'],
                'xref_image_id': item['imageId'],
                'current_occurrence_sha256_match': (fid, srch) in real_occ,
                'current_catalogue_path_checksum_match': bool(image and
                    image.get('relative_path') == item['relativePath'] and image.get('checksum')),
                'current_catalogue_checksum': image.get('checksum') if image else '',
                'authorisation': 'HINT_ONLY_NOT_APPROVED',
            })
        write_csv(out / '0028-0024-crossreference-hints.csv',
                  ['fragment_id', 'source_sha256', 'xref_status', 'xref_method',
                   'xref_relative_path', 'xref_image_id', 'current_occurrence_sha256_match',
                   'current_catalogue_path_checksum_match', 'current_catalogue_checksum',
                   'authorisation'], matches)
        summary['xrefHints'] = len(matches)
        summary['xrefHintsWithCurrentSourceHash'] = sum(1 for m in matches
                        if m['current_occurrence_sha256_match'])
        summary['xrefHintsImageIdPathInCurrentCatalogue'] = sum(1 for m in matches
                        if m['current_catalogue_path_checksum_match'])
        summary['xrefAuthorisation'] = 'NONE; verify Files root and manually approve every occurrence'
    with (out / '0028-summary.json').open('w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        f.write('\n')
    files = [f for f in sorted(out.iterdir()) if f.is_file() and f.name != 'SHA256SUMS.txt']
    with (out / 'SHA256SUMS.txt').open('w', encoding='utf-8') as f:
        for path in files:
            f.write(f'{file_hash(path)}  {path.name}\n')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument('--ssh-host', help='SSH alias for production host, typically pluto')
    src.add_argument('--snapshot', type=Path, help='OFFLINE: CSV from an earlier read-only collection')
    parser.add_argument('--compose-dir', default='$HOME/projects/diaries',
                        help='on remote host (default: $HOME/projects/diaries)')
    parser.add_argument('--db-service', default='diaries-db')
    parser.add_argument('--output', required=True, type=Path, help='NEW directory, private/uncommitted')
    parser.add_argument('--historic-0022', type=Path, help='actual 0022-legacy-image-candidates.csv if recovered')
    parser.add_argument('--historic-ledger', type=Path, help='0022 historical review-ledger.json (hints only)')
    parser.add_argument('--xref-0024', type=Path, help='actual 0024-candidate-cross-reference.csv if recovered')
    args = parser.parse_args()
    os.umask(0o077)
    if args.historic_0022 and not args.historic_0022.is_file():
        parser.error('--historic-0022 file not found')
    for name, value in (('--historic-ledger', args.historic_ledger),
                        ('--xref-0024', args.xref_0024)):
        if value and not value.is_file():
            parser.error(f'{name} file not found')
    if args.snapshot and not args.snapshot.is_file():
        parser.error('--snapshot file not found')
    if args.output.exists():
        parser.error('--output must be a new, non-existing directory')
    args.output.mkdir(parents=True, mode=0o700)
    if args.ssh_host:
        snapshot = args.output / 'current-schema-snapshot.PRIVATE.csv'
        try:
            collect(args.ssh_host, args.compose_dir, args.db_service, snapshot)
        except Exception:
            # Remove a partial untrusted export; do not leak raw output.
            snapshot.unlink(missing_ok=True)
            raise
    else:
        snapshot = args.snapshot
    summary = analyse(snapshot, args.output, args.historic_0022, args.historic_ledger, args.xref_0024)
    print(f"Read-only inventory COMPLETE: {summary['counts']['total_fragments']} fragments, "
          f"{summary['counts']['unreviewed_legacy_candidates']} unreviewed legacy candidates, "
          f"{summary['counts']['total_legacy_occurrences']} occurrences, "
          f"{summary['counts']['structural_exceptions']} structural exceptions")
    print('Output is PRIVATE; Step 1 gate remains OPEN pending review, 0022/0024 reconciliation and approval.')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('Step 1 inventory FAILED: ' + str(error), file=sys.stderr)
        sys.exit(1)
