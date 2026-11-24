#!/usr/bin/env python3
"""0028 Step 1: compare approved draft, frozen sources and post-0052 catalogue.

Read-only OFFLINE check of files produced by the existing production inventory
collector. No DB/MQTT/Files calls, no mutation, no migration approval.
Python 3.7+ standard library only. Output contains PRIVATE image-path mapping;
keep it under the 0028 feature's ignored Step 1/private evidence directory.
"""
import argparse
import csv
import hashlib
import json
import os
import sys
from pathlib import Path
from datetime import datetime

CORRECTED_IMAGE_IDS = {3, 18}  # Exact, accepted scope of 0052-DEF.
PROTECTED_IMAGE_IDS = {20, 21, 25}
SRC_FIELDS = ('version', 'page_id', 'type', 'image_id', 'year', 'month', 'day', 'sequence',
              'lock_user_id', 'lock_session_id', 'lock_timestamp')


def sha(b):
    return hashlib.sha256(b).hexdigest()


def rows(path):
    with path.open('r', encoding='utf-8-sig', newline='') as file:
        return list(csv.DictReader(file))


def snapshot(path):
    fragments, images, identity = {}, {}, []
    data = rows(path)
    if not data or set(data[0]) != {'kind', 'payload'}:
        raise ValueError('Invalid inventory CSV columns')
    for row in data:
        item = json.loads(row['payload'])
        kind = row['kind']
        if kind == 'identity':
            identity.append(item)
        elif kind in ('fragment', 'image'):
            dest = fragments if kind == 'fragment' else images
            key = str(item['fragment_id'] if kind == 'fragment' else item['image_id'])
            if key in dest:
                raise ValueError('Duplicate snapshot '+kind+': '+key)
            dest[key] = item
        else:
            raise ValueError('Unexpected inventory kind: '+str(kind))
    if len(identity) != 1:
        raise ValueError('Expected one inventory identity row')
    return {'fragments': fragments, 'images': images, 'identity': identity[0]}


def index(rows_, name):
    out = {}
    for row in rows_:
        key = (str(row['fragment_id']), str(row['embedded_image_ordinal']))
        if key in out:
            raise ValueError('Duplicate '+name+' occurrence: '+str(key))
        out[key] = row
    return out


def check(a):
    before = snapshot(a.frozen_snapshot)
    old = snapshot(a.previous_snapshot)
    current = snapshot(a.current_snapshot)
    review_bytes = a.review.read_bytes()
    review = json.loads(review_bytes.decode('utf-8-sig'))
    proposals_bytes = a.proposals.read_bytes()
    proposals = index(rows(a.proposals), 'proposal')
    reviewed = index(review['decisions'], 'review')
    now = index(rows(a.current_candidates), 'fresh candidate')

    errors = []
    changes = []
    mapping = []
    if review.get('schema') != '0028-0051-review-v2':
        errors.append('REVIEW_SCHEMA_UNEXPECTED')
    if review.get('productionApplyAllowed') is not False:
        errors.append('REVIEW_UNEXPECTEDLY_ALLOWS_APPLY')
    if review.get('fingerprints', {}).get('proposals_sha256') != sha(proposals_bytes):
        errors.append('PROPOSALS_HASH_MISMATCH')
    if review.get('fingerprints', {}).get('inventory_sha256') != sha(a.frozen_snapshot.read_bytes()):
        errors.append('FROZEN_INVENTORY_HASH_MISMATCH')
    if len(proposals) != 72 or len(reviewed) != 72:
        errors.append('REVIEW_COUNT_NOT_72')
    if set(proposals) != set(reviewed):
        errors.append('REVIEW_PROPOSAL_KEY_MISMATCH')
    if set(proposals) != set(now):
        errors.append('LIVE_CANDIDATE_COVERAGE_CHANGED')
    if current['identity'].get('database') != old['identity'].get('database'):
        errors.append('DATABASE_IDENTITY_CHANGED')
    try:
        stamp = datetime.fromisoformat(current['identity']['snapshot_at'].replace('Z', '+00:00'))
        if not stamp.tzinfo or stamp < datetime.fromisoformat('2026-11-23T10:00:00+00:00'):
            errors.append('SNAPSHOT_NOT_AFTER_0052')
    except (ValueError, KeyError, TypeError):
        errors.append('SNAPSHOT_TIMESTAMP_INVALID')

    reviewed_conversions = 0
    reviewed_deferred = 0
    for key, rev in sorted(reviewed.items(), key=lambda kv: (int(kv[0][0]), int(kv[0][1]))):
        fid, ordinal = key
        prop, fresh = proposals.get(key), now.get(key)
        oldfrag = before['fragments'].get(fid)
        curfrag = current['fragments'].get(fid)
        if not prop or not fresh or not oldfrag or not curfrag:
            errors.append('SOURCE_OR_CANDIDATE_MISSING_'+fid)
            continue
        if (sha((curfrag.get('text') or '').encode('utf-8')) != rev['source_html_sha256'] or
            str(curfrag.get('version')) != rev['expected_fragment_version'] or
            str(curfrag.get('page_id') or '') != rev['expected_page_id']):
            errors.append('SOURCE_HTML_VERSION_OR_PAGE_DRIFT_'+fid)
        for field in SRC_FIELDS:
            if oldfrag.get(field) != curfrag.get(field):
                errors.append('SOURCE_METADATA_DRIFT_'+fid+'_'+field)
        if fresh.get('original_src_sha256') != rev['source_img_sha256']:
            errors.append('LIVE_OCCURRENCE_DRIFT_'+fid)
        priorfrag = old['fragments'].get(fid)
        if not priorfrag or priorfrag.get('marquees') != curfrag.get('marquees'):
            errors.append('LIVE_MARQUEE_DRIFT_'+fid)
        if (rev.get('disposition') == 'DEFER' and rev.get('occurrence_action') == 'DEFER'):
            reviewed_deferred += 1
            continue
        if not (rev.get('disposition') == 'CONVERT_TO_IMAGE' and
                rev.get('occurrence_action') == 'REMOVE_AS_IMAGE' and
                rev.get('v2_review_confirmed') == 'YES' and
                rev.get('suffix_verified') == 'YES'):
            errors.append('REVIEW_CONVERSION_INCOMPLETE_'+fid)
            continue
        reviewed_conversions += 1
        iid = prop.get('catalogue_image_id_hint') or ''
        if not iid.isdigit():
            errors.append('CATALOGUE_IMAGE_ID_UNRESOLVED_'+fid)
            continue
        img = current['images'].get(iid)
        oldimg = old['images'].get(iid)
        if not img or not oldimg:
            errors.append('CATALOGUE_IMAGE_NOT_FOUND_'+iid)
            continue
        if img.get('relative_path') != prop['catalogue_relative_path_hint']:
            errors.append('CATALOGUE_IMAGE_PATH_CHANGED_'+fid)
        if oldimg.get('relative_path') != prop['catalogue_relative_path_hint']:
            errors.append('FROZEN_PROPOSAL_PATH_CONFLICT_'+fid)
        original = prop.get('catalogue_checksum_hint') or ''
        if original != oldimg.get('checksum'):
            errors.append('FROZEN_PROPOSAL_CHECKSUM_CONFLICT_'+fid)
        if int(iid) in CORRECTED_IMAGE_IDS:
            if img.get('checksum') == oldimg.get('checksum'):
                errors.append('0052_IMAGE_STILL_HAS_OLD_CHECKSUM_'+iid)
        elif img.get('checksum') != oldimg.get('checksum'):
            errors.append('UNEXPECTED_CATALOGUE_CHECKSUM_CHANGE_'+iid)
        mapping.append({
            'fragment_id': fid, 'embedded_image_ordinal': ordinal,
            'approved_page_id': rev.get('approved_page_id') or '',
            'reviewed_image_id': iid, 'current_relative_path_PRIVATE': img.get('relative_path') or '',
            'pre0052_checksum': original, 'current_checksum': img.get('checksum') or '',
            'checksum_change': '0052_APPROVED_CORRECTION' if int(iid) in CORRECTED_IMAGE_IDS else 'UNCHANGED',
            'source_html_sha256': rev.get('source_html_sha256') or '',
            'reviewed_caption_override': rev.get('caption_override') or '',
        })

    # Any other catalogue row change is unexpected, including missing/added IDs.
    if set(old['images']) != set(current['images']):
        errors.append('CATALOGUE_IMAGE_ID_SET_CHANGED')
    for iid in set(old['images']) & set(current['images']):
        before_image, image = old['images'][iid], current['images'][iid]
        if int(iid) not in CORRECTED_IMAGE_IDS and before_image != image:
            errors.append('NON_0052_CATALOGUE_METADATA_CHANGED_'+iid)
        if int(iid) in CORRECTED_IMAGE_IDS:
            if before_image.get('relative_path') != image.get('relative_path'):
                errors.append('0052_IMAGE_PATH_CHANGED_'+iid)
            if before_image != image:
                changes.append({'image_id': iid,
                    'previous_checksum': before_image.get('checksum'),
                    'current_checksum': image.get('checksum'),
                    'previous_dimensions': [before_image.get('width'), before_image.get('height')],
                    'current_dimensions': [image.get('width'), image.get('height')]})
    for iid in PROTECTED_IMAGE_IDS:
        if current['images'].get(str(iid)) != old['images'].get(str(iid)):
            errors.append('PROTECTED_IMAGE_METADATA_CHANGED_'+str(iid))
    if current['images'].get('18', {}).get('checksum') == current['images'].get('25', {}).get('checksum'):
        errors.append('HERMITAGE_STILL_MATCHES_ST_ISAAC_CHECKSUM')
    if reviewed_conversions != 71 or reviewed_deferred != 1 or len(mapping) != 71:
        errors.append('REVIEWED_MAPPING_COUNTS_WRONG')

    # Persist evidence even on semantic failures. Never print private HTML or links.
    errors = sorted(set(errors))
    summary = {'schema': '0028-step1-post0052-reconciliation-v1',
               'status': 'PASS' if not errors else 'FAIL',
               'review_sha256': sha(review_bytes),
               'current_snapshot_sha256': sha(a.current_snapshot.read_bytes()),
               'snapshot_timestamp': current['identity'].get('snapshot_at'),
               'database': current['identity'].get('database'),
               'reviewed_occurrences': len(reviewed),
               'reviewed_conversions': reviewed_conversions,
               'explicit_deferred': reviewed_deferred,
               'current_legacy_occurrences': len(now),
               'catalogue_images': len(current['images']),
               'catalogue_metadata_changed_image_ids': sorted(item['image_id'] for item in changes),
               'approved_0052_image_changes': changes,
               'errors': errors,
               'migrationApproved': False, 'productionApplyAllowed': False}
    a.output.mkdir(parents=True, mode=0o700, exist_ok=False)
    files = {'0028-post0052-reconciliation-summary.json': json.dumps(summary,indent=2)+'\n'}
    dest = a.output/'0028-current-catalogue-mapping.PRIVATE.csv'
    with dest.open('w', encoding='utf-8', newline='') as stream:
        header = ['fragment_id','embedded_image_ordinal','approved_page_id',
                  'reviewed_image_id','current_relative_path_PRIVATE','pre0052_checksum',
                  'current_checksum','checksum_change','source_html_sha256','reviewed_caption_override']
        writer = csv.DictWriter(stream, fieldnames=header, lineterminator='\n')
        writer.writeheader(); writer.writerows(mapping)
    (a.output/'0028-post0052-reconciliation-summary.json').write_text(files['0028-post0052-reconciliation-summary.json'],encoding='utf-8')
    with (a.output/'SHA256SUMS.txt').open('w', encoding='utf-8') as stream:
        for p in sorted(a.output.iterdir()):
            if p.is_file() and p.name != 'SHA256SUMS.txt':
                stream.write(sha(p.read_bytes())+'  '+p.name+'\n')
    print('Post-0052 reconciliation: '+summary['status'])
    print('Reviewed: {} conversions, {} DEFER; catalogue changed Image IDs: {}'.format(
        reviewed_conversions, reviewed_deferred,
        ','.join(summary['catalogue_metadata_changed_image_ids']) or '(none)'))
    if errors:
        print('ERRORS (no private content): '+', '.join(errors), file=sys.stderr)
    print('PRIVATE evidence: '+str(a.output))
    print('Production migration NOT authorised')
    return 0 if not errors else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('frozen-snapshot','previous-snapshot','current-snapshot',
                 'current-candidates','proposals','review','output'):
        ap.add_argument('--'+name, type=Path, required=True)
    a = ap.parse_args()
    for name in ('frozen_snapshot','previous_snapshot','current_snapshot',
                 'current_candidates','proposals','review'):
        if not getattr(a,name).is_file():
            ap.error('Missing input: '+name)
    if a.output.exists():
        ap.error('Refusing to overwrite evidence directory')
    os.umask(0o077)
    try:
        return check(a)
    except (OSError, KeyError, ValueError, TypeError, json.JSONDecodeError) as ex:
        print('FAIL: Reconciliation could not complete: '+str(ex),file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
