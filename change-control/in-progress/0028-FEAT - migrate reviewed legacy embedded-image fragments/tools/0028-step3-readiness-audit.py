#!/usr/bin/env python3
"""Read-only, offline audit of previously reviewed 0028 migration inputs.

No database, network or Docker access; output is private metadata only.
Not a production authorisation, production dry-run or freshness check.
Python 3.8-compatible.
"""
import argparse
import csv
import hashlib
import json
import pathlib
import re

EXPECTED = ('0028-dispositions.csv', '0028-image-decisions.csv',
            '0028-v2-preservation-decisions.PRIVATE.csv')
HEXDIGEST = re.compile(r'^[0-9a-f]{64}$')


def require(ok, msg):
    if not ok:
        raise ValueError(msg)


def file_sha(path):
    h = hashlib.sha256()
    with pathlib.Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def csv_rows(path):
    with pathlib.Path(path).open('r', encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames and not any(name is None for name in reader.fieldnames),
                'Missing CSV header: ' + pathlib.Path(path).name)
        rows = list(reader)
        require(all(None not in row for row in rows),
                'Unexpected number of CSV columns: ' + pathlib.Path(path).name)
    return rows


def row_key(row):
    fid = row.get('fragment_id', '')
    require(fid.isdigit(), 'Missing/invalid reviewed Fragment ID')
    ordinal = row.get('embedded_image_ordinal', '')
    require(ordinal.isdigit(), 'Missing/invalid embedded image ordinal')
    return (fid, ordinal)


def audit(manifest):
    manifest = pathlib.Path(manifest)
    require(manifest.is_dir(), 'Prepared manifest directory is missing')
    report_path = manifest / 'PREPARATION-RESULT.json'
    require(report_path.is_file(), 'Prepared manifest receipt missing')
    report = json.loads(report_path.read_text(encoding='utf-8'))
    require(report.get('schema') == '0028-step1-prepared-migration-inputs-v1',
            'Unexpected prepared manifest schema')
    require(report.get('status') == 'PREPARED_NOT_APPROVED'
            and report.get('productionApplyAllowed') is False
            and report.get('migrationApproved') is False,
            'Prepared manifest must not claim authorisation')
    output_hashes = report.get('output_sha256', {})
    for filename in EXPECTED:
        path = manifest / filename
        require(path.is_file() and HEXDIGEST.fullmatch(output_hashes.get(filename, '')),
                'Manifest file/recorded SHA missing: ' + filename)
        require(file_sha(path) == output_hashes[filename],
                'Frozen manifest SHA mismatch: ' + filename)
    dispositions = csv_rows(manifest / EXPECTED[0])
    images = csv_rows(manifest / EXPECTED[1])
    preserve = csv_rows(manifest / EXPECTED[2])
    require(len(dispositions) == len(images) == len(preserve) == 72,
            'Expected 72 decisions in each CSV')
    by_fragment = {}
    for row in dispositions:
        fid = row.get('fragment_id', '')
        require(fid.isdigit() and fid not in by_fragment,
                'Duplicate/invalid reviewed Fragment')
        require(row.get('embedded_image_count') == '1',
                'Unexpected multi-image conversion scope for Fragment ' + fid)
        require(HEXDIGEST.fullmatch(row.get('original_html_sha256', '')),
                'Missing original HTML identity')
        require(row.get('expected_fragment_version', '').isdigit(),
                'Missing original Fragment version')
        by_fragment[fid] = row
    conversions = [r for r in dispositions if r.get('disposition') == 'CONVERT_TO_IMAGE']
    deferred = [r for r in dispositions if r.get('disposition') == 'DEFER']
    require(len(conversions) == 71 and len(deferred) == 1
            and deferred[0]['fragment_id'] == '1564',
            'Unexpected reviewed conversion/defer scope')
    img_by_key = {}
    for row in images:
        key = row_key(row)
        require(key not in img_by_key and key[1] == '1',
                'Duplicate/unsupported reviewed image occurrence')
        require(HEXDIGEST.fullmatch(row.get('original_src_sha256', '')),
                'Missing embedded image identity')
        img_by_key[key] = row
    v2_by_key = {}
    for row in preserve:
        key = row_key(row)
        require(key not in v2_by_key and key[1] == '1',
                'Duplicate/unsupported V2 preservation occurrence')
        require(row.get('link_handling') in ('PRESERVE', 'NOT_PRESENT')
                and row.get('marquee_handling') in ('PRESERVE', 'NOT_APPLICABLE'),
                'Destructive/unreviewed V2 decision rejected')
        v2_by_key[key] = row
    expected = set((fid, '1') for fid in by_fragment)
    require(set(img_by_key) == expected and set(v2_by_key) == expected,
            'Review/IMAGE/V2 occurrence identities differ')
    for fid, disposition in by_fragment.items():
        i = img_by_key[(fid, '1')]
        v = v2_by_key[(fid, '1')]
        require(v.get('original_html_sha256') == disposition.get('original_html_sha256'),
                'Frozen HTML identity mismatch on Fragment ' + fid)
        require(v.get('source_img_sha256') == i.get('original_src_sha256'),
                'Frozen image identity mismatch on Fragment ' + fid)
        if fid == '1564':
            require(i.get('occurrence_action') == 'DEFER'
                    and not i.get('resolved_image_id'),
                    'Deferred Fragment has unintended image action')
            continue
        require(i.get('resolved_image_id', '').isdigit()
                and bool(i.get('resolved_relative_path'))
                and HEXDIGEST.fullmatch(i.get('expected_image_checksum', '')),
                'Conversion lacks approved Image ID/path/checksum')
        require(v.get('v2_review_confirmed') == 'YES',
                'Conversion lacks V2 confirmation')
        if v.get('link_handling') == 'PRESERVE':
            require(bool(v.get('image_link_url_PRIVATE')),
                    'Reviewed hyperlink unexpectedly missing')
        else:
            require(not v.get('image_link_url_PRIVATE'),
                    'Unapproved image hyperlink')
        if v.get('marquee_handling') == 'PRESERVE':
            require(v.get('source_marquee_status') == 'COMPLETE'
                    and v.get('source_marquee_id', '').isdigit()
                    and v.get('source_marquee_id') == disposition.get('marquee_id'),
                    'Expected original Marquee missing/replaced')
        else:
            require(v.get('source_marquee_status') == 'ABSENT'
                    and not disposition.get('marquee_id'),
                    'Unexpected original Marquee')
    links = sum(row.get('link_handling') == 'PRESERVE'
                for row in preserve if row['fragment_id'] != '1564')
    marquees = sum(row.get('marquee_handling') == 'PRESERVE'
                   for row in preserve if row['fragment_id'] != '1564')
    require(links == 30 and marquees == 22,
            'Preservation coverage unexpectedly changed')
    counts = report.get('counts', {})
    require(counts.get('CONVERT_TO_IMAGE') == 71 and counts.get('DEFER') == 1
            and counts.get('links_preserved') == 30
            and counts.get('marquees_preserved') == 22,
            'Prepared receipt counts differ from reviewed scope')
    return {
        'status': 'OFFLINE_FROZEN_INPUTS_PASS_PRODUCTION_NOT_APPROVED',
        'checked': 'prepared-0028-manifest-only',
        'countFragments': 72, 'convertToImage': 71, 'defer': 1,
        'deferredFragmentId': 1564,
        'preservedLinks': links, 'preservedMarquees': marquees,
        'sha256': {name: output_hashes[name] for name in EXPECTED},
        'productionSourceFreshnessVerified': False,
        'productionBackupVerified': False,
        'productionWriterStopVerified': False,
        'formalStep1ApprovalRecorded': False,
        'step2ManualLinkClickRecorded': False,
        'productionApplyAuthorised': False,
        'limitations': 'This is an OFFLINE readiness audit. It does not connect to production or verify live source versions, media, backups, active locks, deployment revisions, MQTT or browser results.'
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--output', required=True)
    args = ap.parse_args()
    output = pathlib.Path(args.output)
    require(output.is_dir(), 'Output evidence directory must already exist')
    report = audit(args.manifest)
    target = output / 'FROZEN-INPUT-READINESS.json'
    require(not target.exists(), 'Refusing to overwrite prior readiness evidence')
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print('PASS: offline reviewed 72 occurrences: 71 conversions; 1 DEFER (1564); 30 links; 22 Marquees')
    print('PASS: prepared manifest SHA-256 values match frozen review receipt')
    print('PENDING: owner Step 1 acceptance; hyperlink click; current production preflight and backups')
    print('PRODUCTION APPLY NOT AUTHORISED')
    print('Private audit result: ' + str(target))


if __name__ == '__main__':
    main()
