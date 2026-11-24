#!/usr/bin/env python3
"""Fail-closed, offline comparison of the freshly collected PRODUCTION inventory.

Input files are private, tool makes NO DB/MQTT/HTTP calls and changes no media.
Only Marquee geometry and monotonic Marquee versions may drift since review.
Run via the Cygwin read-only wrapper, not from an extracted source ZIP.
"""
import argparse
import csv
import hashlib
import json
import math
import os
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from pathlib import Path

HEXDIGEST = re.compile(r'^[a-f0-9]{64}$')


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as src:
        for block in iter(lambda: src.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def text_hash(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def csv_rows(path):
    with Path(path).open('r', newline='', encoding='utf-8-sig') as src:
        reader = csv.DictReader(src)
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError('Missing/duplicate columns in ' + Path(path).name)
        result = list(reader)
        if any(None in row for row in result):
            raise ValueError('Malformed row in ' + Path(path).name)
        return result


class ImageParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.srcs = []
    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'img':
            self.srcs.append(dict(attrs).get('src') or '')
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)


def image_sources(s):
    p = ImageParser()
    p.feed(s)
    p.close()
    return p.srcs


def nonempty(value):
    return '' if value is None else str(value)


def equal_integer(a, b):
    try:
        return int(a) == int(b)
    except (TypeError, ValueError):
        return False


def same_nullable_integer(actual, reviewed):
    """Match SQL NULL to the CSV empty field without equating either to 0.

    The Step 1 manifest writes a blank page_id for legacy Fragments with no
    source Page. The PostgreSQL JSON inventory represents that field as null.
    Only the *Page* comparison uses this nullable interpretation; versions,
    identities and other integer fields must still be present and equal.
    """
    if actual is None or reviewed is None or str(reviewed) == '':
        return actual is None and (reviewed is None or str(reviewed) == '')
    return equal_integer(actual, reviewed)


def same_decimal(a, b):
    try:
        return Decimal(str(a)) == Decimal(str(b))
    except (InvalidOperation, ValueError, TypeError):
        return False


def index_by_id(rows, name):
    result = {}
    for row in rows:
        fid = nonempty(row.get('fragment_id'))
        if not fid.isdigit() or fid in result:
            raise ValueError('Invalid or duplicate ID in ' + name)
        result[fid] = row
    return result


def index_occurrences(rows, name):
    result = {}
    for row in rows:
        key = (nonempty(row.get('fragment_id')), nonempty(row.get('embedded_image_ordinal')))
        if not key[0].isdigit() or not key[1].isdigit() or key in result:
            raise ValueError('Invalid or duplicate key in ' + name)
        result[key] = row
    return result


def snapshot_rows(path):
    fragments, images, identities = {}, {}, []
    for row in csv_rows(path):
        item = json.loads(row['payload'])
        kind = row['kind']
        if kind == 'identity':
            identities.append(item)
        elif kind in ('fragment', 'image'):
            key = str(item['fragment_id'] if kind == 'fragment' else item['image_id'])
            target = fragments if kind == 'fragment' else images
            if key in target:
                raise ValueError('Duplicate production snapshot identity')
            target[key] = item
        else:
            raise ValueError('Unexpected production snapshot kind')
    if len(identities) != 1:
        raise ValueError('Expected one production identity record')
    return fragments, images, identities[0]


def protected_file(files_root, relpath):
    pieces = relpath.replace('\\', '/').split('/')
    if not pieces or any(not p or p in ('.', '..') or ':' in p or '\x00' in p for p in pieces):
        raise ValueError('Unsafe catalogue path')
    root = Path(files_root).resolve(strict=True)
    path = root.joinpath(*pieces)
    actual = path.resolve(strict=True)
    try:
        actual.relative_to(root)
    except ValueError:
        raise ValueError('Image path escapes Files root')
    cursor = root
    for piece in pieces:
        cursor = cursor / piece
        if cursor.is_symlink():
            raise ValueError('Image path includes symlink')
    if not actual.is_file():
        raise ValueError('Image missing or not a regular file')
    return actual


def inspect(manifest, baseline_snapshot, current_snapshot, current_candidates, files_root, now=None):
    manifest = Path(manifest)
    preparation = json.loads((manifest/'PREPARATION-RESULT.json').read_text(encoding='utf-8'))
    if (preparation.get('schema') != '0028-step1-prepared-migration-inputs-v1'
            or preparation.get('status') != 'PREPARED_NOT_APPROVED'
            or preparation.get('productionApplyAllowed') is not False
            or preparation.get('migrationApproved') is not False):
        raise ValueError('Missing or unexpectedly authorised frozen manifest receipt')
    names = ['0028-dispositions.csv','0028-image-decisions.csv','0028-v2-preservation-decisions.PRIVATE.csv']
    for name in names:
        expected = preparation.get('output_sha256', {}).get(name)
        if not expected or not HEXDIGEST.fullmatch(expected) or file_hash(manifest/name) != expected:
            raise ValueError('Frozen manifest checksum mismatch: '+name)
    dispositions = index_by_id(csv_rows(manifest/names[0]), 'dispositions')
    images = index_occurrences(csv_rows(manifest/names[1]), 'image decisions')
    preservation = index_occurrences(csv_rows(manifest/names[2]), 'preservation')
    if (len(dispositions)!=72 or len(images)!=72 or len(preservation)!=72
            or set(images) != {(fid, '1') for fid in dispositions}
            or set(preservation) != set(images)):
        raise ValueError('Frozen 72-item manifest shape changed')
    conversions = [fid for fid, d in dispositions.items() if d.get('disposition')=='CONVERT_TO_IMAGE']
    deferred = [fid for fid, d in dispositions.items() if d.get('disposition')=='DEFER']
    if len(conversions)!=71 or deferred!=['1564']:
        raise ValueError('Frozen 71/1 disposition scope changed')
    _, _, old_identity = snapshot_rows(baseline_snapshot)
    live_frags, live_images, identity = snapshot_rows(current_snapshot)
    live_occ = index_occurrences(csv_rows(current_candidates), 'current legacy candidates')
    errors, informational = [], []
    def fail(code, fid=''):
        errors.append(code+((':'+fid) if fid else ''))
    expected_occ = set(images)
    if set(live_occ) != expected_occ:
        for fid, ordinal in sorted(set(live_occ)-expected_occ): fail('NEW_OR_UNREVIEWED_LEGACY_OCCURRENCE',fid)
        for fid, ordinal in sorted(expected_occ-set(live_occ)): fail('REVIEWED_LEGACY_OCCURRENCE_MISSING',fid)
    snapshot_time = identity.get('snapshot_at')
    try:
        dt = datetime.fromisoformat(snapshot_time.replace('Z','+00:00'))
        current = now or datetime.now(timezone.utc)
        if dt.tzinfo is None or (current-dt).total_seconds() > 1800 or (dt-current).total_seconds() > 120:
            fail('PRODUCTION_SNAPSHOT_NOT_FRESH')
    except (TypeError, AttributeError, ValueError):
        fail('PRODUCTION_SNAPSHOT_TIMESTAMP_INVALID')
    if not old_identity.get('database') or identity.get('database') != old_identity.get('database'):
        fail('PRODUCTION_DATABASE_NAME_CHANGED')
    if not old_identity.get('postgres_version') or identity.get('postgres_version', '').split('.')[0] != old_identity['postgres_version'].split('.')[0]:
        fail('PRODUCTION_POSTGRES_MAJOR_VERSION_CHANGED')
    links = marquees = image_hashes = marquee_geometry_drift = 0
    distinct_files = {}
    for fid, d in sorted(dispositions.items(), key=lambda p: int(p[0])):
        i, v = images[(fid,'1')], preservation[(fid,'1')]
        f = live_frags.get(fid)
        if not f:
            fail('REVIEWED_FRAGMENT_MISSING', fid)
            continue
        if not (equal_integer(f.get('version'), d['expected_fragment_version'])
                and same_nullable_integer(f.get('page_id'), d['page_id'])
                and str(f.get('type') or '') == d['fragment_type_before']
                and f.get('image_id') is None):
            fail('FRAGMENT_ID_VERSION_PAGE_TYPE_DRIFT', fid)
        if not (equal_integer(f.get('year'), d['year']) and equal_integer(f.get('month'),d['month'])
                and equal_integer(f.get('day'),d['day']) and same_decimal(f.get('sequence'),d['sequence'])):
            fail('FRAGMENT_DATE_OR_ORDER_DRIFT', fid)
        raw = f.get('text') or ''
        if text_hash(raw)!=d['original_html_sha256'] or v.get('original_html_sha256')!=d['original_html_sha256']:
            fail('SOURCE_HTML_CHANGED', fid)
        srcs = image_sources(raw)
        if (len(srcs)!=1 or text_hash(srcs[0]) != i.get('original_src_sha256')
                or text_hash(srcs[0]) != v.get('source_img_sha256')):
            fail('SOURCE_IMAGE_OCCURRENCE_CHANGED', fid)
        if f.get('lock_user_id') is not None or f.get('lock_session_id'):
            fail('REVIEWED_FRAGMENT_LOCKED', fid)
        marr = f.get('marquees') or []
        old_id = d.get('marquee_id') or ''
        if len(marr) != (1 if old_id else 0):
            fail('MARQUEE_PRESENCE_CHANGED',fid)
        elif old_id:
            m=marr[0]
            if not (equal_integer(m.get('id'),old_id)
                    and equal_integer(m.get('page_id'),v.get('source_marquee_page_id'))
                    and equal_integer(m.get('page_id'),v.get('approved_page_id'))):
                fail('MARQUEE_ID_OR_PAGE_CHANGED',fid)
            try:
                ver=int(m['version']); old_ver=int(v['source_marquee_version'])
                if ver < old_ver: fail('MARQUEE_VERSION_REVERSED',fid)
                values=[float(m[key]) for key in ('x','y','width','height')]
                if not all(math.isfinite(x) for x in values): fail('MARQUEE_GEOMETRY_INVALID',fid)
                if ver>old_ver:
                    marquee_geometry_drift += 1
            except (KeyError,TypeError,ValueError): fail('MARQUEE_VERSION_OR_GEOMETRY_INVALID',fid)
        if fid not in conversions:
            if i.get('occurrence_action')!='DEFER': fail('DEFER_DECISION_CHANGED',fid)
            continue
        if v.get('marquee_handling')=='PRESERVE':
            marquees+=1
            if not old_id or v.get('source_marquee_id')!=old_id: fail('PRESERVED_MARQUEE_CHANGED',fid)
        elif v.get('marquee_handling') != 'NOT_APPLICABLE': fail('UNREVIEWED_MARQUEE_ACTION',fid)
        if v.get('link_handling')=='PRESERVE':
            links+=1
            url=v.get('image_link_url_PRIVATE') or ''
            if not url or text_hash(url) != v.get('source_link_url_sha256'):
                fail('PRESERVED_LINK_REVIEW_CHANGED',fid)
        elif v.get('link_handling') != 'NOT_PRESENT' or v.get('image_link_url_PRIVATE'):
            fail('UNREVIEWED_LINK_ACTION',fid)
        iid=i.get('resolved_image_id') or ''
        img=live_images.get(iid)
        if (not img or img.get('relative_path')!=i.get('resolved_relative_path')
                or img.get('checksum')!=i.get('expected_image_checksum')):
            fail('CATALOGUE_IMAGE_ID_PATH_OR_HASH_DRIFT',fid)
        else:
            path = i['resolved_relative_path']
            if path in distinct_files and distinct_files[path] != i['expected_image_checksum']:
                fail('CONFLICTING_CATALOGUE_PATH_HASH', fid)
            else:
                distinct_files[path]=i['expected_image_checksum']
    if links!=30 or marquees!=22: fail('PRESERVATION_SCOPE_COUNT_CHANGED')
    for rel, expected in sorted(distinct_files.items()):
        try:
            if file_hash(protected_file(files_root,rel)) != expected:
                fail('NAS_FILES_CHECKSUM_CHANGED')
            else: image_hashes += 1
        except (ValueError, OSError):
            fail('NAS_FILES_MISSING_OR_UNREADABLE')
    global_locks=sum(1 for f in live_frags.values() if f.get('lock_user_id') is not None or f.get('lock_session_id'))
    report={
        'schema':'0028-step3-fresh-production-preflight-v1',
        'status':'PASS_SOURCE_FRESHNESS' if not errors else 'BLOCKED_SOURCE_DRIFT',
        'productionApplyAllowed':False,'productionApplyAuthorised':False,
        'productionSnapshotSha256':file_hash(current_snapshot),
        'snapshot_at':snapshot_time, 'database':identity.get('database'),
        'fragment_count':len(live_frags),'catalogue_image_count':len(live_images),
        'reviewed_fragments':len(dispositions),'planned_conversions':len(conversions),
        'explicit_deferred':deferred,'preserved_links':links,'preserved_marquees':marquees,
        'valid_NAS_files':image_hashes,'distinct_reviewed_files':len(distinct_files),
        'permitted_marquee_version_increments':marquee_geometry_drift,
        'all_fragment_locks_observed':global_locks,
        'writer_stop_confirmed':False,'production_backup_verified':False,
        'production_runtime_compatible_confirmed':False,'formal_owner_signoff_recorded':False,
        'errors':sorted(set(errors)),
        'note':'Read-only point-in-time snapshot only. No writer stop, fresh recovery point, production Files mount identity or actual apply permission.'}
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--snapshot',type=Path,required=True)
    p.add_argument('--baseline-snapshot',type=Path,required=True)
    p.add_argument('--candidates',type=Path,required=True)
    p.add_argument('--files-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():
        p.error('Cannot overwrite an existing private preflight result')
    report=inspect(args.manifest,args.baseline_snapshot,args.snapshot,args.candidates,args.files_root)
    args.output.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print('Production snapshot:',report['snapshot_at'])
    print('Read-only reviewed scope: {} conversions, {} DEFER; {} links, {} Marquees'.format(
        report['planned_conversions'],len(report['explicit_deferred']),report['preserved_links'],report['preserved_marquees']))
    print('Reviewed NAS Files checks: {}/{}'.format(report['valid_NAS_files'], report['distinct_reviewed_files']))
    print('Marquee versions advanced since review:',report['permitted_marquee_version_increments'])
    print('Current Fragment locks observed across production inventory:',report['all_fragment_locks_observed'])
    print('SOURCE PREFLIGHT:',report['status'])
    if report['errors']:
        print('BLOCKERS (no source text/URLs): '+', '.join(report['errors']),file=sys.stderr)
        return 1
    print('PRODUCTION APPLY NOT AUTHORISED; writer gate and backup verification still open')
    return 0

if __name__ == '__main__':
    try: sys.exit(main())
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError) as ex:
        sys.exit('FAIL: 0028 production freshness check could not complete: '+str(ex))
