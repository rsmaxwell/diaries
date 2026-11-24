#!/usr/bin/env python3
"""Offline proposals only for 0028 Step 1. NEVER fills review_* approval fields.

Requires verified 2026-11-18 frozen/0024/triage evidence. Output is PRIVATE.
No database/SSH/MQTT operations are performed.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path


def sha256(content):
    return hashlib.sha256(content).hexdigest()


def evidence_check(directory, skip=()):
    manifest = directory / "SHA256SUMS.txt"
    if not manifest.is_file():
        raise ValueError(f"Missing evidence manifest: {manifest}")
    errors = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, name = line.split(maxsplit=1)
        file = directory / name.lstrip('*')
        if file.name in skip:
            if not file.is_file() or sha256(file.read_bytes()) != expected:
                errors.append(file.name)
            continue
        if not file.is_file() or sha256(file.read_bytes()) != expected:
            raise ValueError(f"Input evidence HASH MISMATCH: {file}")
    return errors


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


class HtmlInventory(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.figure_depth = 0
        self.caption_depth = 0
        self.images = []
        self.caption_parts = []
        self.other_parts = []
        self.links = 0
        self.caption_links = 0
        self.active_anchor_hrefs = []
        self.image_wrapping_hrefs = []
        self.figure_count = 0
        self.caption_count = 0

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "figure":
            self.figure_depth += 1
            self.figure_count += 1
        elif tag == "figcaption":
            self.caption_depth += 1
            self.caption_count += 1
        elif tag == "img":
            self.images.append(attributes.get("src", ""))
            self.image_wrapping_hrefs.extend(self.active_anchor_hrefs)
        elif tag == "a":
            self.links += 1
            self.active_anchor_hrefs.append(attributes.get("href", ""))
            if self.caption_depth:
                self.caption_links += 1

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag == "a" and self.active_anchor_hrefs:
            self.active_anchor_hrefs.pop()
        if tag == "figcaption" and self.caption_depth:
            self.caption_depth -= 1
        if tag == "figure" and self.figure_depth:
            self.figure_depth -= 1

    def handle_data(self, value):
        if self.caption_depth:
            self.caption_parts.append(value)
        else:
            self.other_parts.append(value)

    @property
    def caption(self):
        return ' '.join(' '.join(self.caption_parts).split())

    @property
    def other_text(self):
        return ' '.join(' '.join(self.other_parts).split())


def review_proposal(row, html_info):
    """Return *suggestion* only, never executable authorisation."""
    if row['0024_status'] != 'MATCHED_ONE_IMAGE' or row['catalogue_cross_check'] != 'MATCHED_SNAPSHOT_AND_FILE':
        return 'DEFER', 'BLOCKED_IMAGE_AMBIGUOUS'
    if row['page_ownership'] == 'NO_PAGE_NO_MARQUEE':
        if html_info.image_wrapping_hrefs:
            return 'CONVERT_TO_IMAGE', 'BLOCKED_PAGE_AND_EXTERNAL_LINK'
        return 'CONVERT_TO_IMAGE', 'BLOCKED_AUTHORITATIVE_PAGE_REQUIRED'
    if row['page_ownership'] == 'DIRECT_AND_MARQUEE_AGREE':
        if html_info.image_wrapping_hrefs:
            return 'CONVERT_TO_IMAGE', 'BLOCKED_MARQUEE_AND_EXTERNAL_LINK'
        return 'CONVERT_TO_IMAGE', 'BLOCKED_MARQUEE_ANCHOR_AND_SUFFIX_REVIEW'
    return 'DEFER', 'BLOCKED_UNEXPECTED_PAGE_RELATIONSHIP'


def analyse(frozen, derived, review, triage, working):
    for directory in (frozen, derived, derived / '0024-dry-run', triage):
        evidence_check(directory)
    warnings = evidence_check(review, skip=('0028-review-dossier.PRIVATE.html',))
    if working.read_bytes() != (triage / '0028-context-triage.PRIVATE.csv').read_bytes():
        raise ValueError('Working review differs from frozen triage; analyse edited decisions separately')

    fragments = {}
    images = {}
    for row in read_csv(frozen / 'current-schema-snapshot.PRIVATE.csv'):
        item = json.loads(row['payload'])
        if row['kind'] == 'fragment':
            key = str(item['fragment_id'])
            if key in fragments:
                raise ValueError('Duplicate source fragment')
            fragments[key] = item
        elif row['kind'] == 'image':
            key = str(item['image_id'])
            if key in images:
                raise ValueError('Duplicate source Image')
            images[key] = item

    original_images = {(r['fragment_id'], r['embedded_image_ordinal']): r for r in
                       read_csv(frozen / '0028-image-decisions.UNREVIEWED.csv')}
    xref = {(r['fragmentId'], r['candidateIndex']): r for r in
            read_csv(derived / '0024-dry-run/0024-candidate-cross-reference.csv')}
    worksheet = {(r['fragment_id'], r['embedded_image_ordinal']): r for r in
                 read_csv(review / '0028-review-worksheet.PRIVATE.csv')}
    rows = read_csv(working)
    identities = [(r['fragment_id'], r['embedded_image_ordinal']) for r in rows]
    if len(rows) != 72 or len(set(identities)) != 72:
        raise ValueError('Expected exactly 72 unique occurrences from frozen evidence')
    if set(identities) != set(original_images) or set(identities) != set(xref) or set(identities) != set(worksheet):
        raise ValueError('Occurrence cross-reference coverage mismatch')

    counts = Counter()
    enhanced = []
    for row in rows:
        key = (row['fragment_id'], row['embedded_image_ordinal'])
        orig = original_images[key]
        cross = xref[key]
        stored = worksheet[key]
        fragment = fragments.get(row['fragment_id'])
        if fragment is None:
            raise ValueError('Missing original fragment')
        html = fragment.get('text') or ''
        inv = HtmlInventory()
        inv.feed(html)
        if (sha256(html.encode('utf8')) != row['original_html_sha256'] or
                sha256(orig['original_src'].encode('utf8')) != row['original_src_sha256'] or
                inv.images != [orig['original_src']]):
            raise ValueError('Original HTML/src identity mismatch')
        if (row['original_src_sha256'] != cross['sourceSha256'] or
                row['0024_status'] != cross['status'] or
                row['0024_match_method'] != cross['matchMethod']):
            raise ValueError('0024 cross-reference differs from working review')
        if (row['original_html_sha256'] != stored['original_html_sha256'] or
                row['catalogue_cross_check'] != stored['catalogue_cross_check']):
            raise ValueError('Review worksheet differs from working review')
        if row['catalogue_image_id_hint']:
            image = images.get(row['catalogue_image_id_hint'])
            if image is None or image['relative_path'] != row['catalogue_relative_path_hint'] or image['checksum'] != row['catalogue_checksum_hint']:
                raise ValueError('Catalogue snapshot differs from review Image suggestion')
            if cross['imageId'] != row['catalogue_image_id_hint']:
                raise ValueError('Image ID differs from 0024')
        if any(row.get(c) for c in ('review_disposition','review_occurrence_action','review_page_resolution',
                                   'review_suffix_mapping','review_text_allocation','reviewed_by','reviewed_at')):
            raise ValueError('Source working review already contains manual decisions; refuse auto-proposal')
        proposed, status = review_proposal(row, inv)
        issues = []
        if row['0024_match_method'] == 'UNIQUE_LOCAL_SUFFIX':
            issues.append('REVIEW_SUFFIX_IMAGE_ID_PATH_AND_CHECKSUM')
        if not row['page_id']:
            issues.append('REQUIRE_VERIFIED_PAGE_OWNER_NOT_DATE_HINT')
        if row['marquee_id']:
            issues.append('APPROVE_MARQUEE_GEOMETRY_REMOVAL_IF_CONVERTED')
        if inv.image_wrapping_hrefs:
            issues.append('PRESERVE_EXTERNAL_HYPERLINK_ON_IMAGE_OR_EXPLICITLY_DEFER')
        if inv.caption_links:
            issues.append('PRESERVE_CAPTION_HYPERLINKS')
        if inv.other_text:
            issues.append('REVIEW_TEXT_OUTSIDE_CAPTION_NO_SILENT_LOSS')
        if not inv.caption:
            issues.append('APPROVE_EMPTY_IMAGE_TEXT')
        if proposed == 'DEFER':
            issues.append('RESOLVE_AMBIGUOUS_FILE_OR_KEEP_AS_LEGACY')
        issues.append('VERIFY_EDITOR_AND_READER_PRESENTATION')
        # Work copy fields are preserved exactly; nothing is signed off.
        output = dict(row)
        output.update({
            'proposal_disposition_NOT_APPROVED': proposed,
            'proposal_state': status,
            'proposal_occurrence_action_NOT_APPROVED': 'DEFER' if proposed == 'DEFER' else 'REMOVE_AS_IMAGE',
            'proposal_caption_plaintext_PRIVATE': inv.caption,
            'proposal_unallocated_text_PRIVATE': inv.other_text,
            'proposal_caption_link_count': str(inv.caption_links),
            'proposal_external_image_link_count': str(len(inv.image_wrapping_hrefs)),
            'proposal_external_image_hrefs_PRIVATE': '|'.join(inv.image_wrapping_hrefs),
            'proposal_figure_count': str(inv.figure_count),
            'proposal_html_img_count': str(len(inv.images)),
            'proposal_required_checks': '|'.join(issues),
            'proposal_note': ('DO NOT APPLY: recommendation only; Page, markup, suffix match and source ID require signoff'),
        })
        enhanced.append(output)
        counts['total'] += 1
        counts['proposal_' + proposed] += 1
        counts['state_' + status] += 1
        counts['captioned_figures' if inv.figure_count and inv.caption else 'bare_image_or_other'] += 1
        if inv.caption_links: counts['caption_with_links'] += 1
        if inv.image_wrapping_hrefs: counts['image_wrapped_in_external_link'] += 1
        if inv.other_text: counts['other_text_review'] += 1
        if not inv.caption: counts['without_caption'] += 1
        if not row['page_id']: counts['missing_page'] += 1
        if row['marquee_id']: counts['has_marquee'] += 1
        if row['candidate_page_context'] == 'NO_PAGE_MULTIPLE_DATE_PAGES_HINT_ONLY':counts['multiple_date_page_hints'] += 1
        if row['candidate_page_context'] == 'NO_PAGE_ONE_DATE_PAGE_HINT_ONLY':counts['one_date_page_hint'] += 1
    enhanced.sort(key=lambda r: ({'P0':0,'P2':1,'P4':2}.get(r['triage_priority'][:2],9),r['date'],float(r['sequence']),int(r['fragment_id'])))
    return enhanced, dict(sorted(counts.items())), warnings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('frozen','derived','review','triage','working','output'):
        parser.add_argument('--'+name,required=True,type=Path)
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error('Output directory exists: never overwrite evidence')
    rows, counts, warnings = analyse(args.frozen,args.derived,args.review,args.triage,args.working)
    args.output.mkdir(parents=True, exist_ok=False, mode=0o700)
    csvname = '0028-proposed-review.PRIVATE.csv'
    with (args.output/csvname).open('w',encoding='utf8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0].keys()),lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)
    summary={
        'generatedUtc':datetime.now(timezone.utc).isoformat(),
        'status':'UNREVIEWED_PROPOSALS_ONLY',
        'source':'Frozen production inventory + 0024 dry-run + checked working/triage CSV',
        'counts':counts,
        'reviewDossierChecksumMismatch': bool(warnings),
        'reviewDossierChecksumWarnings': warnings,
        'reviewApproval':None,
        'migrationAllowed':False,
        'notes':['No review_* fields were modified','Suffix-only matches require independent review',
                 'All Page IDs and Marquee removals require explicit approval',
                 'HTML dossier hash discrepancy must be resolved before Step 1 acceptance'],
    }
    (args.output/'0028-proposal-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8')
    with (args.output/'SHA256SUMS.txt').open('w',encoding='utf8') as stream:
        for filename in (csvname,'0028-proposal-summary.json'):
            stream.write(f'{sha256((args.output/filename).read_bytes())}  {filename}\n')
    print('PASS: private proposed review (not approved), input evidence verified except reported dossier mismatch')
    print(json.dumps(summary['counts'],indent=2))
    print('REVIEW DOSSIER SHA256 MISMATCH:',bool(warnings))
    print('OUTPUT:',args.output)


if __name__=='__main__':
    main()
