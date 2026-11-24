#!/usr/bin/env python3
"""0028/0051 inert reviewer: snapshot-bound link and Marquee preservation checks.

This tool NEVER writes PostgreSQL, MQTT, Files, or the original 0028 evidence.
All generated HTML/JSON is PRIVATE and UNAPPROVED. Python standard library only.
"""
import argparse
import csv
import hashlib
import html
import json
import re
from collections import Counter
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

SCHEMA = '0028-0051-review-v2'
DISPOSITIONS = ('CONVERT_TO_IMAGE', 'SPLIT_MARQUEE_AND_IMAGE', 'KEEP_LEGACY', 'DEFER')
ACTIONS = ('REMOVE_AS_IMAGE', 'KEEP_INLINE', 'DEFER')
LINK_ACTIONS = ('NOT_PRESENT', 'PRESERVE', 'CLEAR_CONFIRMED', 'DEFER')
MARQUEE_ACTIONS = ('NOT_APPLICABLE', 'PRESERVE', 'REMOVE_CONFIRMED', 'DEFER')
GEOMETRY_KEYS = ('id', 'version', 'page_id', 'x', 'y', 'width', 'height')


def sha(data):
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def read_rows(path):
    with path.open(encoding='utf-8-sig', newline='') as fh:
        reader = csv.DictReader(fh)
        return list(reader)


def verify_source_checksums(directory):
    path = directory/'SHA256SUMS.txt'
    if not path.is_file():
        raise ValueError('Source SHA256SUMS.txt missing')
    for line in path.read_text(encoding='utf-8').splitlines():
        expected, filename = line.split(maxsplit=1)
        filename = filename.lstrip('*')
        if '/' in filename or '\\' in filename or filename in ('', '.', '..'):
            raise ValueError('Unsafe source checksum filename')
        f = directory/filename
        if sha(f.read_bytes()) != expected:
            raise ValueError('Source checksum mismatch')


def snapshot_index(path):
    frags = {}
    for row in read_rows(path):
        if row['kind'] != 'fragment':
            continue
        p = json.loads(row['payload'])
        key = str(p['fragment_id'])
        if key in frags:
            raise ValueError('Duplicate snapshot Fragment identity')
        frags[key] = p
    return frags


class LinkedImageParser(HTMLParser):
    """Read-only HTML parse: pairs each IMG with its one unambiguous anchor."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.anchors = []
        self.images = []
        self.malformed = False

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == 'a':
            hrefs = [v for k, v in attrs if k.lower() == 'href']
            if self.anchors:
                self.malformed = True
            self.anchors.append({'href': hrefs[0] if len(hrefs)==1 else None,
                                 'valid':len(hrefs)==1, 'images':[]})
        elif tag == 'img':
            sources = [v for k,v in attrs if k.lower() == 'src']
            link = self.anchors[-1] if self.anchors else None
            image = {'ordinal':len(self.images)+1,
                     'src':sources[0] if len(sources)==1 and sources[0] is not None else '',
                     'src_valid':len(sources)==1,
                     'link_url':link['href'] if link else '',
                     'link_state':'LINKED' if link and link['valid'] and link['href'] else 'NONE',
                     'source_ambiguous':len(sources)!=1 or bool(self.malformed)}
            if link:
                link['images'].append(image)
                if not link['valid'] or not link['href']:
                    image['link_state']='AMBIGUOUS'
            self.images.append(image)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag.lower() == 'a':
            self.handle_endtag('a')

    def handle_endtag(self, tag):
        if tag.lower() == 'a':
            if not self.anchors:
                self.malformed = True
                return
            link = self.anchors.pop()
            if len(link['images']) > 1:
                for image in link['images']:
                    image['link_state'] = 'AMBIGUOUS'
            if self.malformed:
                for image in link['images']:
                    image['link_state'] = 'AMBIGUOUS'

    def finish(self, source):
        self.feed(source)
        self.close()
        if self.anchors or self.malformed:
            for im in self.images:
                if im['link_state'] != 'NONE':
                    im['link_state']='AMBIGUOUS'
        return self.images


def extract_images(source):
    return LinkedImageParser().finish(source or '')


def valid_url(url):
    if not isinstance(url, str) or not url or len(url) > 4096:
        return False
    if any(ord(c) <= 32 or ord(c) == 127 or c in '<>\\"{}|^' for c in url) or re.search(r'%(?![a-fA-F0-9]{2})', url):
        return False
    try:
        p = urlsplit(url)
        if p.scheme.lower() not in ('http','https') or not p.netloc or not p.hostname:
            return False
        if p.username is not None or p.password is not None:
            return False
        if p.port is not None and p.port > 65535:
            return False
    except (ValueError, AttributeError):
        return False
    return True


def marquee_evidence(fragment):
    ms = fragment.get('marquees') or []
    if len(ms) > 1:
        return {'status':'MULTIPLE', 'id':'', 'page_id':'', 'version':'', 'geometry_sha256':''}
    if not ms:
        return {'status':'ABSENT', 'id':'', 'page_id':'', 'version':'', 'geometry_sha256':''}
    m = ms[0]
    complete = all(k in m and m[k] is not None for k in GEOMETRY_KEYS)
    geo_hash = sha(json.dumps({k:m[k] for k in GEOMETRY_KEYS},sort_keys=True,separators=(',',':'))) if complete else ''
    return {'status':'COMPLETE' if complete else 'GEOMETRY_NOT_IN_SOURCE',
            'id':str(m.get('id') or ''), 'page_id':str(m.get('page_id') or ''),
            'version':str(m.get('version')) if m.get('version') is not None else '',
            'geometry_sha256':geo_hash}


def from_sources(proposals, frozen, current=None):
    verify_source_checksums(proposals.parent)
    verify_source_checksums(frozen)
    snapshot = frozen/'current-schema-snapshot.PRIVATE.csv'
    fragments = snapshot_index(snapshot)
    by_occ = {}
    for row in read_rows(frozen/'0028-image-decisions.UNREVIEWED.csv'):
        key = (row['fragment_id'], str(row['embedded_image_ordinal']))
        if key in by_occ: raise ValueError('Duplicate frozen occurrence')
        by_occ[key] = row
    data = []
    for row in read_rows(proposals):
        fid = str(row['fragment_id'])
        ordinal = int(row['embedded_image_ordinal'])
        fragment = fragments.get(fid)
        if fragment is None: raise ValueError('Missing frozen Fragment')
        original = fragment.get('text') or ''
        if sha(original) != row['original_html_sha256']:
            raise ValueError('Frozen HTML mismatch')
        imgs = extract_images(original)
        if ordinal < 1 or ordinal > len(imgs):
            raise ValueError('Occurrence ordinal drift')
        image = imgs[ordinal-1]
        frozen_img = by_occ.get((fid,str(ordinal)))
        if not frozen_img or sha(image['src']) != row['original_src_sha256'] or image['src'] != frozen_img['original_src']:
            raise ValueError('Frozen image source drift')
        m = marquee_evidence(fragment)
        live_drift = False
        if current is not None:
            live = current.get(fid)
            if (not live or str(live.get('version')) != str(fragment['version']) or
                sha(live.get('text') or '') != row['original_html_sha256'] or
                str(live.get('page_id') or '') != str(fragment.get('page_id') or '')):
                live_drift = True
            else:
                live_m = marquee_evidence(live)
                if live_m['id'] != m['id'] or live_m['page_id'] != m['page_id']:
                    live_drift = True
                elif live_m['status'] == 'COMPLETE':
                    m = live_m  # Fresh, matching, read-only geometry evidence.
        data.append({
            'fragment_id':fid, 'embedded_image_ordinal':str(ordinal),
            'source_html_sha256':row['original_html_sha256'],
            'source_img_sha256':row['original_src_sha256'],
            'expected_fragment_version':str(fragment['version']),
            'expected_page_id':str(fragment.get('page_id') or ''),
            'source_marquee':m,
            'source_link_state':image['link_state'],
            'source_link_url_PRIVATE':image['link_url'] or '',
            'source_link_url_sha256':sha(image['link_url'] or ''),
            'source_ambiguous':image['source_ambiguous'],
            'live_source_drift':live_drift,
            'source_status':row.get('0024_status') or '',
            'catalogue_cross_check':row.get('catalogue_cross_check') or '',
            'source_caption_status':row.get('verified_caption_status') or '',
            'legacy_review':{},
            'disposition':'', 'occurrence_action':'', 'link_handling':'',
            'image_link_url_PRIVATE':'', 'marquee_handling':'',
            'approved_page_id':'', 'page_provenance':'', 'suffix_verified':'',
            'caption_override':'', 'text_allocation':'', 'review_note':'', 'reviewed_by':'', 'reviewed_at':'',
            'v2_review_confirmed':'',
        })
    if len(data) != len(by_occ) or len(set((r['fragment_id'],r['embedded_image_ordinal']) for r in data)) != len(data):
        raise ValueError('Frozen occurrence coverage incomplete')
    return data, {'proposals_sha256':sha(proposals.read_bytes()),
                  'inventory_sha256':sha(snapshot.read_bytes())}


def prepare(proposals, frozen, prior=None, current=None):
    rows, fingerprints = from_sources(proposals, frozen, current)
    if prior:
        old = json.loads(prior.read_text(encoding='utf-8'))
        if old.get('schema') != '0028-human-review-v1' or \
            old.get('source_sha256') != fingerprints['proposals_sha256'] or \
            old.get('source_inventory_sha256') != fingerprints['inventory_sha256']:
            raise ValueError('Old draft source mismatch; no automatic migration')
        oldrows={}
        for r in old.get('decisions',[]):
            key=(str(r.get('fragment_id')),str(r.get('embedded_image_ordinal')))
            if key in oldrows: raise ValueError('Duplicate prior reviewer entry')
            oldrows[key]=r
        if len(oldrows)!=len(rows): raise ValueError('Prior decision coverage changed')
        for row in rows:
            prior_row=oldrows.get((row['fragment_id'],row['embedded_image_ordinal']))
            if prior_row is None or prior_row.get('original_html_sha256') != row['source_html_sha256'] or prior_row.get('original_src_sha256') != row['source_img_sha256']:
                raise ValueError('Historical reviewer identity mismatch')
            # Preserve ALL previous review choices as hints only; do NOT promote.
            row['legacy_review']=prior_row
    return {'schema':SCHEMA, 'fingerprints':fingerprints,
            'review_status':'UNREVIEWED_V2', 'productionApplyAllowed':False,
            'decisions':rows}


def _timestamp_good(value):
    try:
        t=datetime.fromisoformat(str(value).replace('Z','+00:00'))
        return bool(t.tzinfo)
    except (ValueError, TypeError):return False


def validate(prepared, provided, current=None):
    if provided.get('schema')!=SCHEMA or provided.get('fingerprints')!=prepared['fingerprints']:
        raise ValueError('Changed review schema or source fingerprint')
    ref={(r['fragment_id'],r['embedded_image_ordinal']):r for r in prepared['decisions']}
    supplied={}
    for d in provided.get('decisions',[]):
        key=(str(d.get('fragment_id')),str(d.get('embedded_image_ordinal')))
        if key in supplied or key not in ref:
            raise ValueError('Duplicate/unknown review row identity')
        supplied[key]=d
    if set(supplied)!=set(ref):raise ValueError('Missing reviewed occurrence rows')
    checks=Counter(); outcomes=Counter(); blocked_rows=0
    group_blockers={}
    grouped={}
    for key,d in supplied.items():
        grouped.setdefault(key[0], []).append(d)
    for fid, rows in grouped.items():
        if len({(r.get('disposition'),r.get('marquee_handling'),
                 r.get('approved_page_id'),r.get('page_provenance')) for r in rows}) != 1:
            group_blockers[fid]='CONFLICTING_SOURCE_FRAGMENT_DECISIONS'
        elif rows[0].get('disposition')=='CONVERT_TO_IMAGE' and sum(
                r.get('occurrence_action')=='REMOVE_AS_IMAGE' for r in rows)>1:
            group_blockers[fid]='MULTIPLE_IMAGES_FOR_SINGLE_FRAGMENT'
    for key, source in ref.items():
        d=supplied[key]
        for field in ('source_html_sha256','source_img_sha256', 'source_link_state',
                      'source_link_url_PRIVATE','source_link_url_sha256',
                      'source_marquee','expected_fragment_version','expected_page_id','live_source_drift'):
            if d.get(field)!=source[field]:
                raise ValueError('Source identity or link/Marquee evidence drift')
        # V2 caption overrides are reviewer-owned, never copied from historical v1.
        # Old V2 JSONs do not contain this field; they remain valid without edits.
        override = d.get('caption_override', '')
        if (not isinstance(override, str) or len(override) > 2000 or
                (override and (not override.strip() or
                               any(ord(ch) < 32 or ord(ch) == 127 or ch in '<>' for ch in override)))):
            raise ValueError('Invalid V2 caption override: must be plain, single-line text (max 2000 characters)')
        decision=d.get('disposition') or ''
        action=d.get('occurrence_action') or ''
        outcomes[decision or 'UNREVIEWED']+=1
        blockers=[]
        if key[0] in group_blockers: blockers.append(group_blockers[key[0]])
        if decision not in DISPOSITIONS:blockers.append('NO_REVIEWED_DISPOSITION')
        if action not in ACTIONS:blockers.append('INVALID_OCCURRENCE_ACTION')
        if not str(d.get('reviewed_by') or '').strip() or not _timestamp_good(d.get('reviewed_at')) or not str(d.get('review_note') or '').strip():
            blockers.append('REVIEW_IDENTITY_OR_REASON_MISSING')
        if override and decision in ('DEFER', 'KEEP_LEGACY'):
            blockers.append('CAPTION_OVERRIDE_WITHOUT_CONVERSION')
        if decision in ('DEFER','KEEP_LEGACY'):
            if action != ('DEFER' if decision=='DEFER' else 'KEEP_INLINE'):
                blockers.append('NOOP_ACTION_MISMATCH')
        elif decision in ('CONVERT_TO_IMAGE','SPLIT_MARQUEE_AND_IMAGE'):
            if action != 'REMOVE_AS_IMAGE':blockers.append('REMOVE_ACTION_REQUIRED')
            if d.get('v2_review_confirmed')!='YES':blockers.append('V2_RECONFIRMATION_REQUIRED')
            if source['source_status']!='MATCHED_ONE_IMAGE' or source['catalogue_cross_check']!='MATCHED_SNAPSHOT_AND_FILE':
                blockers.append('IMAGE_MATCH_UNRESOLVED')
            if d.get('suffix_verified')!='YES':blockers.append('FILE_RECONCILIATION_NOT_SIGNED_OFF')
            if source['source_ambiguous'] or source['source_link_state']=='AMBIGUOUS':
                blockers.append('AMBIGUOUS_ORIGINAL_IMAGE_LINK')
            link = d.get('link_handling')
            text = d.get('image_link_url_PRIVATE') or ''
            original = source['source_link_url_PRIVATE']
            if source['source_link_state']=='LINKED':
                if link=='PRESERVE':
                    if text != original or sha(text)!=source['source_link_url_sha256']:
                        blockers.append('IMAGE_LINK_EXACT_ROUNDTRIP_FAILED')
                    if not valid_url(text):blockers.append('UNSAFE_IMAGE_LINK_URL')
                elif link=='CLEAR_CONFIRMED':
                    if text or d.get('review_clear_confirmed')!='YES':
                        blockers.append('LINK_CLEAR_NOT_EXPLICITLY_CONFIRMED')
                else: blockers.append('LINK_PRESERVE_OR_CLEAR_REVIEW_REQUIRED')
            elif source['source_link_state']=='NONE':
                if link!='NOT_PRESENT' or text:
                    blockers.append('ABSENT_LINK_STATE_MISMATCH')
            else:blockers.append('LINK_SOURCE_UNRESOLVED')
            m = source['source_marquee']; mh=d.get('marquee_handling')
            if m['status']=='ABSENT':
                if mh!='NOT_APPLICABLE':blockers.append('NO_MARQUEE_EXPECTED')
            else:
                if mh not in ('PRESERVE','REMOVE_CONFIRMED'):
                    blockers.append('MARQUEE_REVIEW_REQUIRED')
                if m['status']!='COMPLETE' or not m['geometry_sha256']:
                    blockers.append('MARQUEE_GEOMETRY_OR_VERSION_NOT_FROZEN')
                if m['page_id']!=(source['expected_page_id'] or str(d.get('approved_page_id') or '')):
                    blockers.append('CROSS_PAGE_MARQUEE')
                if decision=='SPLIT_MARQUEE_AND_IMAGE' and mh!='PRESERVE':
                    blockers.append('SPLIT_ORIGINAL_MARQUEE_MUST_REMAIN')
                if mh=='REMOVE_CONFIRMED' and d.get('review_remove_marquee_confirmed')!='YES':
                    blockers.append('MARQUEE_REMOVAL_NOT_EXPLICITLY_CONFIRMED')
            if not source['expected_page_id'] and (not str(d.get('approved_page_id') or '').isdigit() or not d.get('page_provenance')):
                blockers.append('PAGE_OWNERSHIP_UNRESOLVED')
            if not str(d.get('text_allocation') or '').strip():
                blockers.append('TEXT_CHRONOLOGY_ALLOCATION_UNREVIEWED')
            if source['live_source_drift']:
                blockers.append('LIVE_SOURCE_DRIFT_REQUIRES_NEW_REVIEW')
            if current is None:
                blockers.append('FRESH_READONLY_DB_SNAPSHOT_REQUIRED')
            else:
                fragment = current.get(source['fragment_id'])
                if (not fragment or str(fragment.get('version'))!=source['expected_fragment_version'] or
                    sha(fragment.get('text') or '')!=source['source_html_sha256'] or
                    str(fragment.get('page_id') or '')!=source['expected_page_id']):
                    blockers.append('STALE_OR_CHANGED_LIVE_FRAGMENT')
                elif marquee_evidence(fragment)!=m:
                    blockers.append('LIVE_MARQUEE_IDENTITY_OR_GEOMETRY_DRIFT')
        for b in set(blockers):checks[b]+=1
        if blockers:blocked_rows+=1
    return {'status':'DRAFT_REVIEW_ONLY','schema':SCHEMA,'rows':len(ref),
            'byDisposition':dict(sorted(outcomes.items())),
            'rowsWithBlockers':blocked_rows,'blockers':dict(sorted(checks.items())),
            'migrationApproved':False,'productionApplyAllowed':False}


def write_private(out, data):
    if out.exists():raise ValueError('Refusing to overwrite existing evidence directory')
    out.mkdir(parents=True, mode=0o700)
    hashes=[]
    for name, text in data.items():
        payload=text.encode('utf-8')
        path=out/name
        path.write_bytes(payload)
        path.chmod(0o600)
        hashes.append(sha(payload)+'  '+name)
    (out/'SHA256SUMS.txt').write_text('\n'.join(hashes)+'\n',encoding='utf-8')
    (out/'SHA256SUMS.txt').chmod(0o600)


def safe_json(obj):
    return json.dumps(obj,ensure_ascii=True).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')


class SimpleImageFragmentParser(HTMLParser):
    """Recognise ONLY lossless, one-image HTML with optional simple caption/link.

    All other text, unsafe wrappers, broken nesting, comments and multiple
    images require human allocation decisions. This is NOT an HTML sanitiser.
    """
    ALLOWED = frozenset(('figure', 'img', 'a', 'figcaption'))

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.invalid = False
        self.images = 0
        self.figures = 0
        self.anchors = 0
        self.captions = 0
        self.caption_parts = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.ALLOWED:
            self.invalid = True
            return
        if tag == 'img':
            # An unrecognised attribute may carry meaning that the migration
            # cannot promise to preserve (e.g. alt, title or JS handlers).
            if any(k.lower() not in ('src', 'width', 'height') for k, _ in attrs):
                self.invalid = True
            self.images += 1
            if 'figcaption' in self.stack or self.images != 1:
                self.invalid = True
            return  # IMG is a void element, even without an explicit />
        if tag == 'figure':
            self.figures += 1
            if self.figures > 1 or self.stack:
                self.invalid = True
        if tag == 'a':
            self.anchors += 1
            if self.anchors > 1 or (self.stack and self.stack[-1] != 'figure'):
                self.invalid = True
        if tag == 'figcaption':
            self.captions += 1
            if (self.captions > 1 or 'figure' not in self.stack or
                    self.stack[-1] not in ('figure', 'a')):
                self.invalid = True
        self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag != 'img':
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1] != tag:
            self.invalid = True
        else:
            self.stack.pop()

    def handle_data(self, data):
        if 'figcaption' in self.stack:
            self.caption_parts.append(data)
        elif data.strip():
            self.invalid = True  # Even a stray quote must receive review.

    def handle_comment(self, data):
        self.invalid = True

    def handle_decl(self, decl):
        self.invalid = True

    def unknown_decl(self, data):
        self.invalid = True

    def handle_pi(self, data):
        self.invalid = True

    def analyse(self, original):
        try:
            self.feed(original)
            self.close()
        except (ValueError, AssertionError):
            self.invalid = True
        return not self.invalid and not self.stack and self.images == 1


def image_page_prefix(src):
    """An imgNNNN filename is a Page *hint*, not verified ownership."""
    filename = (src or '').replace('\\', '/').rsplit('/', 1)[-1]
    match = re.match(r'(?i)^(img[0-9]{3,6})(?=[._-]|$)', filename)
    return match.group(1).lower() if match else ''


def source_suggestions(row, preview=None):
    """Unapproved, source-backed drafts. Never infer final human sign-off.

    The HTML-only conversion heuristic is active ONLY with a verified frozen
    preview from source_previews(), not with bare mutable review JSON.
    """
    hints = {}
    state = row.get('source_link_state')
    if not row.get('source_ambiguous'):
        if state == 'NONE' and not row.get('source_link_url_PRIVATE'):
            hints['link_handling'] = 'NOT_PRESENT'
            hints['image_link_url_PRIVATE'] = ''
        elif state == 'LINKED' and valid_url(row.get('source_link_url_PRIVATE')):
            hints['link_handling'] = 'PRESERVE'
            hints['image_link_url_PRIVATE'] = row['source_link_url_PRIVATE']
    marquee = row.get('source_marquee') or {}
    if marquee.get('status') == 'ABSENT' and not marquee.get('id'):
        hints['marquee_handling'] = 'NOT_APPLICABLE'
    elif (marquee.get('status') == 'COMPLETE' and marquee.get('geometry_sha256')
          and marquee.get('page_id') == row.get('expected_page_id')
          and marquee.get('id')):
        hints['marquee_handling'] = 'PRESERVE'

    if preview is None:
        return hints  # Older synthetic portals do not carry verified HTML.
    if (str(preview.get('fragment_id')) != str(row.get('fragment_id')) or
            str(preview.get('ordinal')) != str(row.get('embedded_image_ordinal')) or
            sha(preview.get('original_html_PRIVATE') or '') != row.get('source_html_sha256')):
        raise ValueError('Source suggestion preview identity/hash mismatch')
    original = preview['original_html_PRIVATE']
    imgs = extract_images(original)
    ordinal = int(row['embedded_image_ordinal'])
    if not (1 <= ordinal <= len(imgs)) or sha(imgs[ordinal-1]['src']) != row.get('source_img_sha256'):
        raise ValueError('Suggestion original IMG identity mismatch')
    prefix = image_page_prefix(imgs[ordinal-1]['src'])
    old_page = str((row.get('legacy_review') or {}).get('approved_page_id') or '')
    known_page = str(row.get('expected_page_id') or '')
    hints['_page_hint'] = ('Filename prefix: ' + prefix if prefix else 'No imgNNNN filename prefix') + (
        '; frozen source Page ID: ' + known_page if known_page else
        '; historical v1 Page ID hint: ' + old_page + ' (unverified)' if old_page else
        '; no Page ID available from snapshot')

    shape = SimpleImageFragmentParser()
    simple = shape.analyse(original) and ((state == 'NONE' and shape.anchors == 0) or
                                          (state == 'LINKED' and shape.anchors == 1))
    well_matched = (row.get('source_status') == 'MATCHED_ONE_IMAGE' and
                    row.get('catalogue_cross_check') == 'MATCHED_SNAPSHOT_AND_FILE' and
                    not row.get('source_ambiguous') and not row.get('live_source_drift') and
                    state in ('NONE', 'LINKED') and 'link_handling' in hints)
    # Existing Marquee needs an explicit choice between conversion and split.
    no_marquee = marquee.get('status') == 'ABSENT' and not marquee.get('id')
    if not (simple and well_matched and no_marquee and len(imgs) == 1):
        hints['_reason'] = ('Manual conversion review required: ' + ', '.join(
            part for condition, part in (
                (not simple or len(imgs) != 1, 'non-image text, complex markup or multiple images'),
                (not well_matched, 'catalogue/link match or live-source state unresolved'),
                (not no_marquee, 'existing Marquee needs a preservation/split decision'))
            if condition))
        return hints

    hints['disposition'] = 'CONVERT_TO_IMAGE'
    hints['occurrence_action'] = 'REMOVE_AS_IMAGE'
    date = ('{}-{:02d}-{:02d}'.format(int(preview['year']), int(preview['month']), int(preview['day']))
            if all(preview.get(k) is not None for k in ('year', 'month', 'day')) else '(not present in test source)')
    sequence = str(preview.get('sequence') or '(unrecorded)')
    caption = ''.join(shape.caption_parts).strip()
    if shape.captions:
        detail = 'Preserve the original figcaption exactly: ' + json.dumps(caption,ensure_ascii=False) + '.'
    else:
        detail = 'No original figcaption is present; do not invent a caption.'
    hints['text_allocation'] = (
        'The frozen HTML consists solely of one embedded image and its optional caption/link; '
        'there is no separate narrative text to split. ' + detail +
        ' On conversion preserve the original Fragment date ' + date +
        ' and sequence ' + sequence +
        ', and preserve the exact image hyperlink if present. Do not discard any original content.')
    if known_page:
        page = 'Frozen source Fragment already belongs to Page ID ' + known_page + '; preserve that relationship.'
    else:
        page = 'Frozen source Fragment has no Page association.'
    if prefix:
        page += ' The original image filename begins ' + prefix + ', a possible diary Page-name hint, not verified ownership.'
    if old_page:
        page += ' Previous v1 review proposed Page ID ' + old_page + '; this is historical guidance only.'
    page += ' Verify the intended Page in the editor before entering Approved Page ID or authorising conversion.'
    hints['page_provenance'] = page
    hints['_reason'] = 'Simple single-image source with verified catalogue/file match; conversion is a suggestion only.'
    return hints


class InertTextExtractor(HTMLParser):
    """Readable text only. Never render, load or evaluate original HTML."""
    BREAKS = frozenset(('p', 'div', 'section', 'article', 'header', 'footer',
                        'br', 'hr', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                        'figure', 'figcaption', 'blockquote', 'tr'))
    HIDDEN = frozenset(('script', 'style', 'template', 'noscript'))

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = []
        self.image_count = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.HIDDEN:
            self.hidden.append(tag)
        if self.hidden:
            return
        if tag in self.BREAKS:
            self.parts.append('\n')
        if tag == 'img':
            self.image_count += 1
            srcs = [v for k, v in attrs if k.lower() == 'src']
            src = srcs[0] if len(srcs) == 1 and srcs[0] else '(unknown source)'
            self.parts.append('[Image {}: {}]'.format(self.image_count, src))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.HIDDEN:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if self.hidden:
            if self.hidden[-1] == tag:
                self.hidden.pop()
            return
        if tag in self.BREAKS:
            self.parts.append('\n')

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)

    def text(self):
        lines = [' '.join(line.split()) for line in ''.join(self.parts).splitlines()]
        out = []
        for line in lines:
            if line or (out and out[-1]):
                out.append(line)
        return '\n'.join(out).strip()


def image_tag_ranges(original):
    """Exact character offsets of IMG opening tags, excluding comments and literals."""
    class TagFinder(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.ranges = []
            self.offsets = [0]
            for line in original.splitlines(keepends=True):
                self.offsets.append(self.offsets[-1] + len(line))

        def handle_starttag(self, tag, attrs):
            if tag != 'img':
                return
            line, col = self.getpos()
            start = self.offsets[line - 1] + col
            raw = self.get_starttag_text()
            if original[start:start + len(raw)] != raw:
                raise ValueError('Cannot locate exact frozen IMG tag in original HTML')
            self.ranges.append((start, start + len(raw)))

        def handle_startendtag(self, tag, attrs):
            self.handle_starttag(tag, attrs)

    finder = TagFinder()
    finder.feed(original)
    finder.close()
    return finder.ranges


def source_previews(prepared, frozen_snapshot):
    """Read-only preview data from the same SHA256-sealed inventory as v2.

    Never inject the original HTML into the decisions JSON: it is PRIVATE
    supporting evidence and must not alter the draft import/export schema.
    Fail closed on checksum, fingerprint, version or embedded image mismatch.
    """
    frozen_snapshot = Path(frozen_snapshot)
    if frozen_snapshot.name != 'current-schema-snapshot.PRIVATE.csv':
        raise ValueError('Unexpected frozen snapshot filename')
    verify_source_checksums(frozen_snapshot.parent)
    expected = prepared.get('fingerprints', {}).get('inventory_sha256')
    if not expected or expected != sha(frozen_snapshot.read_bytes()):
        raise ValueError('Frozen inventory SHA256 fingerprint mismatch')
    fragments = snapshot_index(frozen_snapshot)
    previews = []
    for decision in prepared['decisions']:
        fid = str(decision['fragment_id'])
        fragment = fragments.get(fid)
        if fragment is None:
            raise ValueError('Frozen Fragment {} not found'.format(fid))
        original = fragment.get('text') or ''
        if sha(original) != decision['source_html_sha256']:
            raise ValueError('Frozen original HTML SHA256 mismatch for Fragment {}'.format(fid))
        if (str(fragment['version']) != str(decision['expected_fragment_version']) or
                str(fragment.get('page_id') or '') != decision['expected_page_id']):
            raise ValueError('Frozen source version/Page mismatch for Fragment {}'.format(fid))
        ordinal = int(decision['embedded_image_ordinal'])
        images = extract_images(original)
        ranges = image_tag_ranges(original)
        if len(ranges) != len(images) or not 1 <= ordinal <= len(images):
            raise ValueError('Frozen image occurrence mismatch for Fragment {}'.format(fid))
        src = images[ordinal - 1]['src']
        if sha(src) != decision['source_img_sha256']:
            raise ValueError('Frozen IMG src SHA256 mismatch for Fragment {}'.format(fid))
        if (images[ordinal - 1]['link_state'] != decision['source_link_state'] or
                (images[ordinal - 1]['link_url'] or '') != decision['source_link_url_PRIVATE']):
            raise ValueError('Frozen link mismatch for Fragment {}'.format(fid))
        readable = InertTextExtractor()
        readable.feed(original)
        readable.close()
        start, end = ranges[ordinal - 1]
        previews.append({'fragment_id':fid, 'ordinal':str(ordinal),
                         'original_html_PRIVATE':original, 'readable_text_PRIVATE':readable.text(),
                         'image_start':start, 'image_end':end,
                         'year':fragment.get('year'), 'month':fragment.get('month'),
                         'day':fragment.get('day'), 'sequence':fragment.get('sequence')})
    return previews


def original_figcaption(preview):
    """Return original figcaption only for a verified simple, single-image source.

    Complex/multi-image fragments require manual original-HTML inspection;
    historical v1 caption overrides are never treated as frozen caption facts.
    """
    original = preview.get('original_html_PRIVATE') or ''
    parser = SimpleImageFragmentParser()
    if not parser.analyse(original) or parser.images != 1:
        return {'verified': False, 'value': ''}
    return {'verified': True, 'value': ''.join(parser.caption_parts).strip() if parser.captions else ''}


def portal(prepared, original_previews=None):
    """Offline, local-only v2 draft editor with explicit source-fact suggestions.

    The HTML is regenerated from fresh evidence; importing an older v2 draft is
    allowed only when its immutable source fields/fingerprints still match.
    """
    payload = safe_json(prepared)
    if original_previews and len(original_previews) != len(prepared['decisions']):
        raise ValueError('Source preview coverage does not match review rows')
    hints = safe_json([source_suggestions(r, (original_previews or [None]*len(prepared['decisions']))[i])
                       for i, r in enumerate(prepared['decisions'])])
    previews = safe_json(original_previews or [])
    captions = safe_json([original_figcaption(p) for p in original_previews] if original_previews else [])
    return r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src 'none'; connect-src 'none'; form-action 'none'; base-uri 'none'">
<title>0028 / 0051 PRIVATE review v2</title>
<style>
body{font:15px system-ui,sans-serif;max-width:980px;margin:22px auto;padding:0 16px;color:#202b36}
h1{font-size:25px}.notice{border:2px solid #8b6b3c;padding:12px;background:#fffaf0}
label{display:block;margin:12px 0 4px}input,textarea,select{box-sizing:border-box;font:inherit;width:100%;padding:6px}
textarea{min-height:48px}button{font:inherit;padding:8px 10px;margin:8px 8px 8px 0;cursor:pointer}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#eee;padding:12px;max-height:440px;overflow:auto}
pre[hidden]{display:none}
#originalHtml{max-height:490px;white-space:pre-wrap;tab-size:2}
#originalHtml mark{background:#f9df87;color:#182638;padding:2px 0}
#sourceButtons button[aria-pressed="true"]{background:#294b70;color:white}
#originalReadable{max-height:490px}
.panel{border:1px solid #b5b8bc;padding:12px 14px;margin:15px 0;border-radius:3px}
.meta,.hint{font-size:14px;color:#4b5563}.actions{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.actions button{margin:4px 0}.danger{color:#913d22}.good{color:#185b43}.two{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:700px){.two{grid-template-columns:1fr}}
#msg{min-height:24px;white-space:pre-wrap}#progress{font-weight:600}
</style></head><body>
<h1>0028 · 0051 compatibility review (PRIVATE)</h1>
<p class="notice"><strong>UNAPPROVED.</strong> The original v1 review is only historical guidance.
Source-derived conversion and Page suggestions are NOT human approvals. Every conversion requires explicit v2 re-confirmation
and a fresh source snapshot. Do not commit or upload this PRIVATE HTML/JSON to a public repository.</p>
<div class="panel">
  <label for="item">Occurrence <select id="item"></select></label>
  <div class="actions"><button id="previous" type="button">Previous</button><button id="next" type="button">Next</button><span id="progress"></span></div>
  <p id="facts" class="meta"></p>
  <details><summary>Source evidence and prior v1 review (PRIVATE)</summary><pre id="evidence"></pre></details>
</div>
<div class="panel">
  <strong>Suggested fields — not approvals</strong>
  <p id="suggestions" class="hint"></p>
  <div class="actions">
    <button id="fillSafe" type="button">Fill safe source fields here</button>
    <button id="fillAllSafe" type="button">Fill safe source fields for all occurrences*</button>
    <button id="copyPrior" type="button">Copy historical decision and note</button>
  </div>
  <p class="hint">*Source-verified simple one-image fragments may receive draft CONVERT_TO_IMAGE / REMOVE_AS_IMAGE choices,
  a standard text/chronology plan and provisional Page provenance. These are unapproved suggestions only;
  Page ID, suffix reconciliation, review reason, reviewer, timestamp, v2 confirmation and deletion approvals
  remain for explicit human review. Existing choices are never overwritten.</p>
</div>
<div class="panel" id="originalPanel">
  <strong>Original Fragment HTML (PRIVATE, read-only)</strong>
  <p id="sourceNote" class="hint">Verified against the frozen production snapshot. The current embedded-image occurrence is highlighted.</p>
  <div class="actions" id="sourceButtons">
    <button id="viewHtml" type="button" aria-pressed="true">HTML source</button>
    <button id="viewReadable" type="button" aria-pressed="false">Readable text</button>
    <button id="copyHtml" type="button">Copy complete original HTML</button>
  </div>
  <pre id="originalHtml" aria-label="Complete original HTML with image occurrence highlighted"></pre>
  <pre id="originalReadable" hidden aria-label="Readable text extracted from original HTML"></pre>
  <p class="hint">The source is inert text; images, hyperlinks and scripts are never loaded or executed. Readable text is a convenience view; use HTML source for exact markup.</p>
</div>
<div class="two">
 <div><label for="disposition">Disposition</label><select id="disposition"></select></div>
 <div><label for="occurrence_action">Occurrence action</label><select id="occurrence_action"></select></div>
 <div><label for="link_handling">Link handling</label><select id="link_handling"></select></div>
 <div><label for="marquee_handling">Marquee handling</label><select id="marquee_handling"></select></div>
</div>
<label for="image_link_url_PRIVATE">Exact decoded link to preserve (PRIVATE)</label><input id="image_link_url_PRIVATE">
<label for="suffix_verified">Suffix reconciliation (requires evidence)</label><select id="suffix_verified"></select>
<label for="text_allocation">Text/chronology allocation</label><textarea id="text_allocation"></textarea>
<div class="panel" id="captionPanel">
 <strong>IMAGE Fragment caption — editorial decision</strong>
 <p class="meta" id="originalCaption">Original caption from frozen source: loading…</p>
 <label for="caption_override">Caption override (optional — blank preserves original caption)</label>
 <input id="caption_override" maxlength="2000" placeholder="Leave blank to use the original figcaption">
 <p class="hint" id="effectiveCaption">Effective caption: loading…</p>
 <p class="hint">An override changes this occurrence's IMAGE Fragment text, not the reusable catalogue Image.
 Record the reason in the Review note. Changing it clears the review timestamp and V2 re-confirmation.</p>
</div>
<label for="approved_page_id">Approved Page ID (only if verified)</label><input id="approved_page_id">
<label for="page_provenance">Page ownership and provenance</label><textarea id="page_provenance"></textarea>
<label for="review_note">Review reason</label><textarea id="review_note"></textarea>
<div class="two">
 <div><label for="reviewed_by">Reviewer</label><input id="reviewed_by"></div>
 <div><label for="reviewed_at">UTC ISO8601 timestamp</label><input id="reviewed_at" placeholder="Click Record review time after making a decision"></div>
</div>
<button id="stamp" type="button">Record review time for this occurrence</button>
<p class="hint">The review time is recorded only on request, not by opening an occurrence.
If you edit an already timed review decision, its time and v2 reconfirmation are cleared for fresh review.</p>
<div class="two">
 <div><label for="review_clear_confirmed">Explicit link clear approval</label><select id="review_clear_confirmed"></select></div>
 <div><label for="review_remove_marquee_confirmed">Explicit Marquee deletion approval</label><select id="review_remove_marquee_confirmed"></select></div>
</div>
<label for="v2_review_confirmed">V2 compatibility re-confirmation (conversions only)</label><select id="v2_review_confirmed"></select>
<div class="panel">
 <strong>Private review draft</strong>
 <p class="hint">Export regularly. This offline page does not store your work in the browser.
 You can import a previously exported v2 draft only if its source evidence still matches.</p>
 <div class="actions"><button id="export" type="button">Export PRIVATE v2 draft</button>
 <label for="importFile" style="margin:0">Resume from exported PRIVATE JSON <input id="importFile" type="file" accept=".json,application/json"></label>
 </div>
</div>
<p id="msg" role="status" aria-live="polite"></p>
<script id="data" type="application/json">''' + payload + r'''</script>
<script id="hints" type="application/json">''' + hints + r'''</script>
<script id="originals" type="application/json">''' + previews + r'''</script>
<script id="captions" type="application/json">''' + captions + r'''</script>
<script>
'use strict';
const source=JSON.parse(document.getElementById('data').textContent);
const safeHints=JSON.parse(document.getElementById('hints').textContent);
const originals=JSON.parse(document.getElementById('originals').textContent);
const originalCaptions=JSON.parse(document.getElementById('captions').textContent);
const pristine=JSON.parse(JSON.stringify(source));
let rows=source.decisions, index=0, dirty=false, rememberedReviewer='', sourceMode='html';
const names=['disposition','occurrence_action','link_handling','image_link_url_PRIVATE',
  'marquee_handling','suffix_verified','caption_override','text_allocation','approved_page_id','page_provenance',
  'review_note','reviewed_by','reviewed_at','review_clear_confirmed',
  'review_remove_marquee_confirmed','v2_review_confirmed'];
const selects={disposition:['','CONVERT_TO_IMAGE','SPLIT_MARQUEE_AND_IMAGE','KEEP_LEGACY','DEFER'],
  occurrence_action:['','REMOVE_AS_IMAGE','KEEP_INLINE','DEFER'],
  link_handling:['','NOT_PRESENT','PRESERVE','CLEAR_CONFIRMED','DEFER'],
  marquee_handling:['','NOT_APPLICABLE','PRESERVE','REMOVE_CONFIRMED','DEFER'],
  suffix_verified:['','YES','NO'],review_clear_confirmed:['','YES','NO'],
  review_remove_marquee_confirmed:['','YES','NO'],v2_review_confirmed:['','YES','NO']};
const reviewFields=new Set(names);
const signingFields=new Set(['disposition','occurrence_action','link_handling','image_link_url_PRIVATE',
 'marquee_handling','suffix_verified','caption_override','text_allocation','approved_page_id','page_provenance',
 'review_note','reviewed_by','review_clear_confirmed','review_remove_marquee_confirmed']);
const item=document.getElementById('item'),msg=document.getElementById('msg');
for(const [k,vs] of Object.entries(selects)){
 const el=document.getElementById(k);
 for(const v of vs){const op=document.createElement('option');op.value=v;op.textContent=v||'— unreviewed —';el.appendChild(op);}
}
function setMessage(message,success=true){msg.textContent=message;msg.className=success?'good':'danger';}
function markDirty(){dirty=true;updateProgress();}
function updateProgress(){
 const reviewed=rows.filter(r=>r.disposition&&r.occurrence_action&&r.review_note&&r.reviewed_by&&r.reviewed_at).length;
 document.getElementById('progress').textContent=`${index+1} / ${rows.length} · ${reviewed} with recorded review time${dirty?' · unsaved edits':''}`;
}
function showSourceMode(mode){
 sourceMode=mode;
 document.getElementById('originalHtml').hidden=mode!=='html';
 document.getElementById('originalReadable').hidden=mode!=='readable';
 document.getElementById('viewHtml').setAttribute('aria-pressed',String(mode==='html'));
 document.getElementById('viewReadable').setAttribute('aria-pressed',String(mode==='readable'));
}
function showOriginal(r){
 const preview=originals[index];
 const source=document.getElementById('originalHtml');
 const readable=document.getElementById('originalReadable');
 source.replaceChildren();
 if(!preview){
  source.textContent='Original HTML is not included in this synthetic/legacy portal. Regenerate with the frozen source snapshot.';
  readable.textContent='Original HTML unavailable.';
  document.getElementById('sourceNote').textContent='Original source not attached; do not approve conversion from this preview.';
  document.getElementById('copyHtml').disabled=true;
  return;
 }
 if(preview.fragment_id!==r.fragment_id || preview.ordinal!==r.embedded_image_ordinal)
  throw new Error('Original HTML occurrence order mismatch');
 const html=preview.original_html_PRIVATE;
 const start=preview.image_start,end=preview.image_end;
 if(!Number.isInteger(start)||!Number.isInteger(end)||start<0||end<=start||end>html.length)
  throw new Error('Invalid IMG highlight range');
 source.appendChild(document.createTextNode(html.slice(0,start)));
 const mark=document.createElement('mark');mark.textContent=html.slice(start,end);
 source.appendChild(mark);
 source.appendChild(document.createTextNode(html.slice(end)));
 readable.textContent=preview.readable_text_PRIVATE;
 document.getElementById('sourceNote').textContent=`SHA-256 verified against frozen inventory · Fragment ${r.fragment_id} · embedded image #${r.embedded_image_ordinal} highlighted`;
 document.getElementById('copyHtml').disabled=false;
 source.scrollTop=0;readable.scrollTop=0;
 showSourceMode(sourceMode);
}
async function copyOriginal(){
 const original=originals[index];if(!original)return;
 const value=original.original_html_PRIVATE;
 try{
  if(navigator.clipboard && navigator.clipboard.writeText){
   await navigator.clipboard.writeText(value);
  }else{
   const helper=document.createElement('textarea');helper.value=value;
   helper.setAttribute('readonly','');helper.style.position='fixed';helper.style.left='-10000px';
   document.body.appendChild(helper);helper.select();
   let ok=false;try{ok=document.execCommand('copy');}finally{helper.remove();}
   if(!ok)throw new Error('Clipboard blocked');
  }
  setMessage('Copied complete original HTML. No review fields changed.');
 }catch(e){
  showSourceMode('html');
  const sel=window.getSelection(),range=document.createRange();
  range.selectNodeContents(document.getElementById('originalHtml'));
  sel.removeAllRanges();sel.addRange(range);
  setMessage('Clipboard permission unavailable: original HTML selected. Press Ctrl+C to copy.',false);
 }
}
function renderCaption(){
 const original=originalCaptions[index];
 const caption=document.getElementById('originalCaption');
 const effective=document.getElementById('effectiveCaption');
 const override=rows[index].caption_override||'';
 if(original && original.verified){
  caption.textContent='Frozen original figcaption: '+(original.value||'(none recorded)');
  effective.textContent='Effective IMAGE Fragment caption: '+(override.trim()||original.value||'(none recorded)');
 }else{
  caption.textContent='Frozen figcaption requires manual review: inspect the original HTML above.';
  effective.textContent='Effective IMAGE Fragment caption: '+(override.trim()||'(use reviewed original caption; inspect HTML)');
 }
}
function render(){
 const r=rows[index];item.value=String(index);
 const m=r.source_marquee||{};
 document.getElementById('facts').textContent=`Fragment ${r.fragment_id}, image ${r.embedded_image_ordinal} · link: ${r.source_link_state} · Marquee: ${m.status||'UNKNOWN'} · 0024: ${r.source_status||'not classified'}`;
 showOriginal(r);
 document.getElementById('evidence').textContent=JSON.stringify({
  fragment:r.fragment_id,ordinal:r.embedded_image_ordinal,sourceLink:r.source_link_url_PRIVATE,
  sourceMarquee:r.source_marquee,sourceStatus:r.source_status,catalogue:r.catalogue_cross_check,
  priorReview:r.legacy_review},null,2);
 for(const k of names)document.getElementById(k).value=r[k]||'';
 renderCaption();
 document.getElementById('reviewed_by').placeholder=rememberedReviewer?'Click to use '+rememberedReviewer:'Enter once; reused when recording another review';
 const h=safeHints[index];
 const values=Object.entries(h).filter(([k])=>['disposition','occurrence_action','link_handling','marquee_handling'].includes(k)).map(([k,v])=>`${k} = ${v}`);
 if(h.text_allocation)values.push('standard text/chronology plan available');
 if(h.page_provenance)values.push('provisional Page provenance available');
 const prior=r.legacy_review||{};
 document.getElementById('suggestions').textContent=(values.length?'Source evidence suggests: '+values.join('; '):'No unambiguous source-based suggestions')+
  (h._page_hint?' · '+h._page_hint:'')+
  (h._reason?' · '+h._reason:'')+
  (prior.disposition?' · Historical disposition: '+prior.disposition:' · No historical disposition')+
  '. Nothing is copied until you click a button. Review each inference before signing.';
 document.getElementById('copyPrior').disabled=!prior.disposition&&!prior.review_note;
 updateProgress();
}
function writeField(r,k,value){
 if((r[k]||'')===value)return false;
 r[k]=value;
 // Any material edit after signing invalidates the recorded time and conversion re-confirmation.
 if(signingFields.has(k)){
  if(r.reviewed_at)r.reviewed_at='';
  if(r.v2_review_confirmed)r.v2_review_confirmed='';
 }
 return true;
}
function safeFill(r,h){
 let changed=0;
 // Exact link URL and handling always travel together, and never overwrite edits.
 if(h.link_handling && !r.link_handling && !r.image_link_url_PRIVATE){
  if(writeField(r,'link_handling',h.link_handling))changed++;
  if(h.image_link_url_PRIVATE && writeField(r,'image_link_url_PRIVATE',h.image_link_url_PRIVATE))changed++;
 }
 if(h.marquee_handling && !r.marquee_handling && writeField(r,'marquee_handling',h.marquee_handling))changed++;
 // Only suggest conversion as a consistent pair; do not contradict an existing decision.
 const compatible=h.disposition && (!r.disposition || r.disposition===h.disposition) &&
  (!r.occurrence_action || r.occurrence_action===h.occurrence_action);
 if(compatible){
  if(!r.disposition && writeField(r,'disposition',h.disposition))changed++;
  if(!r.occurrence_action && writeField(r,'occurrence_action',h.occurrence_action))changed++;
  for(const k of ['text_allocation','page_provenance']){
   if(h[k] && !r[k] && writeField(r,k,h[k]))changed++;
  }
 }
 return changed;
}
function fillCurrent(){
 const n=safeFill(rows[index],safeHints[index]);if(n)markDirty();render();
 setMessage(n?`Filled ${n} blank source-derived draft field(s). Inspect and explicitly review; no conversion is approved.`:'Nothing changed; existing choices were preserved.');
}
function fillAll(){
 if(!confirm('Fill ONLY blank fields from verified frozen HTML for '+rows.length+' occurrences? This includes suggested conversion/action pairs and standard preservation text for SIMPLE image-only fragments. No Page ID, suffix approval, reviewer, timestamp or v2 conversion confirmation is added. Some signed reviews could lose their timestamp if blanks are filled. Continue?'))return;
 let edits=0,affected=0;
 rows.forEach((r,i)=>{const n=safeFill(r,safeHints[i]);edits+=n;if(n)affected++;});
 if(edits)markDirty();render();setMessage(`Filled ${edits} unapproved draft fields in ${affected} occurrences. Inspect each before signing; no migration approved.`);
}

function copyPrior(){
 const r=rows[index],p=r.legacy_review||{};let changes=0;
 if(p.disposition && selects.disposition.includes(p.disposition) && !r.disposition){
  if(writeField(r,'disposition',p.disposition))changes++;
  const action={DEFER:'DEFER',KEEP_LEGACY:'KEEP_INLINE',CONVERT_TO_IMAGE:'REMOVE_AS_IMAGE',SPLIT_MARQUEE_AND_IMAGE:'REMOVE_AS_IMAGE'}[p.disposition];
  if(action && !r.occurrence_action && writeField(r,'occurrence_action',action))changes++;
 }
 if(typeof p.review_note==='string' && p.review_note.trim() && !r.review_note && writeField(r,'review_note',p.review_note))changes++;
 if(changes)markDirty();render();setMessage(changes?
  'Copied historical suggestions to blank fields. You must inspect and re-confirm them; no reviewer, timestamp or migration approval set.':
  'No historical blank fields available; current decisions were preserved.');
}
function onEdit(k){
 const r=rows[index],value=document.getElementById(k).value;
 if(k==='reviewed_by' && value.trim())rememberedReviewer=value.trim();
 if(writeField(r,k,value))markDirty();
 if(k==='caption_override')renderCaption();
 // A changed signed review needs a fresh timestamp. Keep the on-screen controls in sync.
 if(signingFields.has(k)){
  document.getElementById('reviewed_at').value=r.reviewed_at||'';
  document.getElementById('v2_review_confirmed').value=r.v2_review_confirmed||'';
 }
}
function stamp(){
 const r=rows[index];
 if(!r.reviewed_by && rememberedReviewer){writeField(r,'reviewed_by',rememberedReviewer);}
 if(!r.reviewed_by || !r.review_note || !r.disposition || !r.occurrence_action){
  render();setMessage('Choose a disposition/action, explain your review and enter a reviewer before recording its time.',false);return;
 }
 r.reviewed_at=new Date().toISOString();markDirty();render();
 setMessage('Recorded current UTC review time for this occurrence. No migration approval was set.');
}
function importCompatible(incoming){
 if(!incoming || incoming.schema!==pristine.schema ||
   JSON.stringify(incoming.fingerprints)!==JSON.stringify(pristine.fingerprints) ||
   !Array.isArray(incoming.decisions) || incoming.decisions.length!==pristine.decisions.length)return false;
 const expected=new Map(pristine.decisions.map(r=>[r.fragment_id+':'+r.embedded_image_ordinal,r]));
 const seen=new Set();
 for(const candidate of incoming.decisions){
  if(!candidate || typeof candidate!=='object')return false;
  const key=candidate.fragment_id+':'+candidate.embedded_image_ordinal;
  if(seen.has(key)||!expected.has(key))return false;seen.add(key);
  const reference=expected.get(key);
  for(const k of Object.keys(reference)){
   if(!reviewFields.has(k) && JSON.stringify(candidate[k])!==JSON.stringify(reference[k]))return false;
  }
  if(Object.keys(candidate).some(k=>!(k in reference)&&!reviewFields.has(k)))return false;
  if(names.some(k=>candidate[k]!==undefined && typeof candidate[k]!=='string'))return false;
  const override=candidate.caption_override||'';
  if(override.length>2000 || (override && (!override.trim() || /[<>\x00-\x1f\x7f]/.test(override))))return false;
 }
 return true;
}
async function importDraft(file){
 try{
  const imported=JSON.parse(await file.text());
  if(!importCompatible(imported))throw new Error('Draft does not match this source snapshot, or immutable evidence changed.');
  if(dirty&&!confirm('Replace unsaved on-screen edits with the imported private draft?'))return;
  // Preserve the source metadata and evidence emitted by this generator, only importing editable review fields.
  const map=new Map(imported.decisions.map(r=>[r.fragment_id+':'+r.embedded_image_ordinal,r]));
  rows=pristine.decisions.map(base=>{
   const next=JSON.parse(JSON.stringify(base)),previous=map.get(base.fragment_id+':'+base.embedded_image_ordinal);
   for(const k of names)if(typeof previous[k]==='string')next[k]=previous[k];
   return next;
  });
  source.decisions=rows;dirty=false;
  rememberedReviewer=(rows.find(r=>r.reviewed_by)||{}).reviewed_by||'';
  index=0;render();setMessage('PRIVATE draft imported; no migration approval implied.');
 }catch(e){setMessage('Import rejected: '+e.message,false);}
}
function exportDraft(){
 // Download is the only persistence; fields with no value remain unreviewed.
 const blob=new Blob([JSON.stringify(source,null,2)+'\n'],{type:'application/json'});
 const a=document.createElement('a');a.href=URL.createObjectURL(blob);
 a.download='0028-0051-review-v2.DRAFT.PRIVATE.json';a.click();
 setTimeout(()=>URL.revokeObjectURL(a.href),1000);dirty=false;updateProgress();
 setMessage('Exported PRIVATE, UNAPPROVED draft. Validate with Python against fresh evidence.');
}
rows.forEach((r,i)=>{const op=document.createElement('option');op.value=String(i);
 op.textContent=`Fragment ${r.fragment_id} · image ${r.embedded_image_ordinal}`;item.appendChild(op);});
item.addEventListener('change',()=>{index=Number(item.value);render();});
document.getElementById('previous').addEventListener('click',()=>{if(index>0){index--;render();}});
document.getElementById('next').addEventListener('click',()=>{if(index<rows.length-1){index++;render();}});
for(const k of names){document.getElementById(k).addEventListener('input',()=>onEdit(k));
 if(selects[k])document.getElementById(k).addEventListener('change',()=>onEdit(k));}
document.getElementById('viewHtml').addEventListener('click',()=>showSourceMode('html'));
document.getElementById('viewReadable').addEventListener('click',()=>showSourceMode('readable'));
document.getElementById('copyHtml').addEventListener('click',copyOriginal);
document.getElementById('fillSafe').addEventListener('click',fillCurrent);
document.getElementById('fillAllSafe').addEventListener('click',fillAll);
document.getElementById('copyPrior').addEventListener('click',copyPrior);
document.getElementById('stamp').addEventListener('click',stamp);
document.getElementById('export').addEventListener('click',exportDraft);
document.getElementById('importFile').addEventListener('change',async(e)=>{
 const file=e.target.files[0];if(file)await importDraft(file);e.target.value='';});
render();
</script></body></html>'''


def main(args=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode',choices=('prepare','check'))
    ap.add_argument('--proposals',required=True,type=Path)
    ap.add_argument('--frozen',required=True,type=Path)
    ap.add_argument('--prior-v1-draft',type=Path)
    ap.add_argument('--decisions',type=Path)
    ap.add_argument('--current-snapshot',type=Path)
    ap.add_argument('--output',required=True,type=Path)
    a=ap.parse_args(args)
    current=snapshot_index(a.current_snapshot) if a.current_snapshot else None
    prepared=prepare(a.proposals,a.frozen,a.prior_v1_draft,current)
    if a.mode=='prepare':
        if a.decisions:ap.error('--decisions only in check mode')
        summary={'schema':SCHEMA,'status':'PRIVATE_UNAPPROVED_V2',
                 'candidateOccurrences':len(prepared['decisions']),
                 'observedLinked':sum(x['source_link_state']=='LINKED' for x in prepared['decisions']),
                 'observedWithMarquee':sum(x['source_marquee']['id']!='' for x in prepared['decisions']),
                 'geometryVersionAbsent':sum(x['source_marquee']['status']=='GEOMETRY_NOT_IN_SOURCE' for x in prepared['decisions']),
                 'sourceFingerprints':prepared['fingerprints'], 'migrationApproved':False,'productionApplyAllowed':False}
        prior_counts={}
        if a.prior_v1_draft:
            prior_counts=dict(sorted(Counter(
                (r['legacy_review'].get('disposition') or 'UNREVIEWED')
                for r in prepared['decisions']).items()))
        diff={'schema':SCHEMA,'status':'UNAPPROVED_V2_DIFFERENCES',
              'sourceOccurrences':len(prepared['decisions']),
              'priorV1DispositionCounts':prior_counts,
              'v2DispositionCounts':{'UNREVIEWED':len(prepared['decisions'])},
              'priorDecisionsAutomaticallyPromoted':0,
              'newLinkApprovalFieldsBlank':True,
              'newMarqueeApprovalFieldsBlank':True,
              'productionApplyAllowed':False}
        write_private(a.output,{
            '0028-0051-v2-draft-differences.json':json.dumps(diff,indent=2)+'\n',
            '0028-0051-review-v2.DRAFT.PRIVATE.json':json.dumps(prepared,indent=2,ensure_ascii=False)+'\n',
            '0028-0051-review-v2.PRIVATE.html':portal(prepared, source_previews(prepared, a.frozen/'current-schema-snapshot.PRIVATE.csv')),
            '0028-0051-compatibility-summary.json':json.dumps(summary,indent=2)+'\n'})
        print('PASS: PRIVATE unapproved v2 draft and offline portal generated; no migration authorised')
    else:
        if not a.decisions:ap.error('--decisions required in check mode')
        if a.current_snapshot and not a.current_snapshot.is_file():ap.error('--current-snapshot not found')
        report=validate(prepared,json.loads(a.decisions.read_text(encoding='utf-8')),current)
        write_private(a.output,{'0028-0051-v2-review-check.json':json.dumps(report,indent=2)+'\n'})
        print('PASS: review checker finished; {} blocked occurrences; production apply NEVER authorised'.format(report['rowsWithBlockers']))
    print('Evidence: {}'.format(a.output))


if __name__=='__main__':main()
