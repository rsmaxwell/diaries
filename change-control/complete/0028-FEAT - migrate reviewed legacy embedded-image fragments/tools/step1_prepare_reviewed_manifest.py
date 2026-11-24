#!/usr/bin/env python3
"""Assemble frozen, reviewed, read-only inputs for 0028 Step 2.

Python 3.7+; writes ONLY within a new private output directory.
Never calls a database, filesystem-root or MQTT mutator and never enables apply.
"""
import argparse
import csv
import hashlib
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

D_FIELDS = ['fragment_id','expected_fragment_version','page_id','marquee_id',
            'fragment_type_before','year','month','day','sequence',
            'original_html_sha256','embedded_image_count','disposition',
            'review_note','reviewed_by','reviewed_at']
I_FIELDS = ['fragment_id','embedded_image_ordinal','original_src',
            'original_src_sha256','resolved_relative_path','match_method',
            'resolved_image_id','expected_image_checksum','occurrence_action',
            'image_text','review_note']
V_FIELDS = ['fragment_id','embedded_image_ordinal','approved_page_id',
            'page_provenance','suffix_verified','text_allocation','caption_override',
            'v2_review_confirmed','reviewed_by','reviewed_at',
            'link_handling','source_link_url_sha256','image_link_url_PRIVATE',
            'review_clear_confirmed','marquee_handling','source_marquee_status',
            'source_marquee_id','source_marquee_page_id','source_marquee_version',
            'source_marquee_geometry_sha256','review_remove_marquee_confirmed',
            'original_html_sha256','source_img_sha256','review_note']

def sha_file(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def sha_text(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()

def require(cond,msg):
    if not cond: raise ValueError(msg)

def read_csv(p):
    with Path(p).open('r',newline='',encoding='utf-8') as f:
        return list(csv.DictReader(f))

def read_json(p):
    with Path(p).open('r',encoding='utf-8') as f:
        return json.load(f)

class ImgParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.srcs=[]
    def handle_starttag(self,tag,attrs):
        if tag.lower()=='img':
            self.srcs.append(dict(attrs).get('src',''))
    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs)

def seq_key(key):
    return (int(key[0]),int(key[1]))

def assemble(review_path,snapshot_path,mapping_path,check_path,summary_path):
    review=read_json(review_path)
    check=read_json(check_path)
    summary=read_json(summary_path)
    require(review.get('schema')=='0028-0051-review-v2','Unknown review schema')
    require(review.get('productionApplyAllowed') is False,'Review appears authorised for production apply')
    require(check.get('rowsWithBlockers')==0 and check.get('productionApplyAllowed') is False,
            'Compatibility review has blockers or authorisation')
    require(summary.get('status')=='PASS' and summary.get('productionApplyAllowed') is False,
            'Live catalogue reconciliation not PASS/NO_APPLY')
    require(summary.get('review_sha256')==sha_file(review_path),
            'Live reconciliation used a different review JSON')
    require(summary.get('current_snapshot_sha256')==sha_file(snapshot_path),
            'Live reconciliation used a different production snapshot')
    require(set(map(str,summary.get('catalogue_metadata_changed_image_ids',[])))=={'3','18'},
            'Unexpected Image catalogue corrections')

    decisions=review.get('decisions',[])
    require(len(decisions)==72,'Expected exactly 72 reviewed occurrence entries')
    keys=[(str(d.get('fragment_id')),str(d.get('embedded_image_ordinal'))) for d in decisions]
    require(len(keys)==len(set(keys)),'Duplicate review occurrence key')
    require(Counter(d.get('disposition') for d in decisions)==
            Counter({'CONVERT_TO_IMAGE':71,'DEFER':1}),
            'Unexpected conversion/defer counts')
    require(check.get('rows')==72 and check.get('byDisposition')=={'CONVERT_TO_IMAGE':71,'DEFER':1},
            'Checker report does not describe reviewed decisions')

    frag={}
    for r in read_csv(snapshot_path):
        if r.get('kind')!='fragment': continue
        f=json.loads(r['payload'])
        fid=str(f['fragment_id'])
        require(fid not in frag,'Duplicate snapshot Fragment {}'.format(fid))
        frag[fid]=f
    mapping={}
    for m in read_csv(mapping_path):
        key=(m['fragment_id'],m['embedded_image_ordinal'])
        require(key not in mapping,'Duplicate mapping {}'.format(key))
        mapping[key]=m
    require(len(mapping)==71,'Expected 71 mapping records')

    frags_groups={}
    drows=[];irows=[];vrows=[]
    for d in sorted(decisions,key=lambda x:seq_key((x['fragment_id'],x['embedded_image_ordinal']))):
        fid=str(d['fragment_id']); ordinal=int(d['embedded_image_ordinal'])
        key=(fid,str(ordinal))
        require(fid in frag,'Source fragment missing from current snapshot: {}'.format(fid))
        f=frag[fid]
        raw=f.get('text') or ''
        require(sha_text(raw)==d['source_html_sha256'],
                'Source text changed: Fragment {}'.format(fid))
        require(str(f.get('version'))==str(d['expected_fragment_version']),
                'Fragment version changed: {}'.format(fid))
        p=ImgParser()
        p.feed(raw)
        require(0<ordinal<=len(p.srcs),'Embedded ordinal missing: {}'.format(key))
        src=p.srcs[ordinal-1]
        require(sha_text(src)==d['source_img_sha256'],
                'Embedded img src changed: {}'.format(key))
        frags_groups.setdefault(fid,[]).append(d)
        disp=d['disposition']; mar=d.get('source_marquee',{})
        if disp=='CONVERT_TO_IMAGE':
            require(d.get('v2_review_confirmed')=='YES' and d.get('reviewed_at') and d.get('reviewed_by'),
                    'V2 approval incomplete: {}'.format(key))
            require(key in mapping,'Missing reviewed current Image match: {}'.format(key))
            m=mapping[key]
            require(m.get('source_html_sha256')==d['source_html_sha256'],
                    'Mapping html hash changed: {}'.format(key))
            require(m.get('approved_page_id')==d.get('approved_page_id'),
                    'Mapping Page ownership differs: {}'.format(key))
            require(m.get('current_relative_path_PRIVATE') and m.get('reviewed_image_id'),
                    'Missing source Image ID/path: {}'.format(key))
            require(len(m.get('current_checksum',''))==64,
                    'Missing Image checksum: {}'.format(key))
            link=d.get('link_handling')
            require(link in ('NOT_PRESENT','PRESERVE'),
                    'Unexpected destructive or undecided link operation: {}'.format(key))
            if link=='PRESERVE':
                require(d.get('image_link_url_PRIVATE') and
                        d['image_link_url_PRIVATE']==d.get('source_link_url_PRIVATE'),
                        'Linked source URL not preserved exactly: {}'.format(key))
            else:
                require(not d.get('image_link_url_PRIVATE'),
                        'Unexpected URL on unlinked source: {}'.format(key))
            marquee=d.get('marquee_handling')
            require(marquee in ('NOT_APPLICABLE','PRESERVE'),
                    'Unexpected destructive or undecided Marquee handling: {}'.format(key))
            if marquee=='PRESERVE':
                require(mar.get('status')=='COMPLETE' and mar.get('id') and
                        mar.get('version')!='' and len(mar.get('geometry_sha256',''))==64,
                        'Incomplete existing Marquee geometry: {}'.format(key))
            else:
                require(mar.get('status')=='ABSENT','Marquee status unexpectedly present: {}'.format(key))
            caption = d.get('caption_override') or d.get('legacy_review',{}).get('caption_effective','')
            # Blank captions are a reviewed intentional possibility.
            irows.append(dict(fragment_id=fid,embedded_image_ordinal=str(ordinal),
               original_src=src,original_src_sha256=d['source_img_sha256'],
               resolved_relative_path=m['current_relative_path_PRIVATE'],
               match_method='REVIEWED_0024_SUFFIX_AND_CURRENT_CATALOGUE',
               resolved_image_id=m['reviewed_image_id'],
               expected_image_checksum=m['current_checksum'],
               occurrence_action=d.get('occurrence_action',''),image_text=caption,
               review_note=d.get('review_note','')))
        else:
            require(disp=='DEFER' and fid=='1564',
                    'Unapproved deferral {}'.format(key))
            require(key not in mapping,'Deferred row unexpectedly mapped {}'.format(key))
            irows.append(dict(fragment_id=fid,embedded_image_ordinal=str(ordinal),
               original_src=src,original_src_sha256=d['source_img_sha256'],
               resolved_relative_path='',match_method='UNRESOLVED_DEFER',
               resolved_image_id='',expected_image_checksum='',
               occurrence_action='DEFER',image_text='',review_note=d.get('review_note','')))
        vrows.append(dict(fragment_id=fid,embedded_image_ordinal=str(ordinal),
              approved_page_id=d.get('approved_page_id',''),
              page_provenance=d.get('page_provenance',''),
              suffix_verified=d.get('suffix_verified',''),
              text_allocation=d.get('text_allocation',''),
              caption_override=d.get('caption_override',''),
              v2_review_confirmed=d.get('v2_review_confirmed',''),
              reviewed_by=d.get('reviewed_by',''),reviewed_at=d.get('reviewed_at',''),
              link_handling=d.get('link_handling',''),
              source_link_url_sha256=d.get('source_link_url_sha256',''),
              image_link_url_PRIVATE=d.get('image_link_url_PRIVATE',''),
              review_clear_confirmed=d.get('review_clear_confirmed',''),
              marquee_handling=d.get('marquee_handling',''),
              source_marquee_status=mar.get('status',''),
              source_marquee_id=mar.get('id',''),
              source_marquee_page_id=mar.get('page_id',''),
              source_marquee_version=mar.get('version',''),
              source_marquee_geometry_sha256=mar.get('geometry_sha256',''),
              review_remove_marquee_confirmed=d.get('review_remove_marquee_confirmed',''),
              original_html_sha256=d.get('source_html_sha256',''),
              source_img_sha256=d.get('source_img_sha256',''),
              review_note=d.get('review_note','')))
    require(set(mapping)=={(r['fragment_id'],r['embedded_image_ordinal'])
                           for r in irows if r['occurrence_action']!='DEFER'},
            'Mapping coverage mismatch')
    for fid,dd in sorted(frags_groups.items(),key=lambda p:int(p[0])):
        f=frag[fid]
        dispositions={d['disposition'] for d in dd}
        require(len(dispositions)==1,'Multiple dispositions for same Fragment {}'.format(fid))
        # Source Page is intentionally distinct from reviewed destination Page.
        marqs=f.get('marquees') or []
        require(len(marqs)<=1,'Multiple source Marquees on Fragment {}'.format(fid))
        for d in dd:
            mar=d.get('source_marquee') or {}
            if mar.get('status')=='ABSENT':
                require(not marqs,'Unexpected live Marquee on {}'.format(fid))
            elif mar.get('status')=='COMPLETE':
                require(len(marqs)==1 and str(marqs[0].get('id'))==mar.get('id'),
                        'Live Marquee identity differs on {}'.format(fid))
        d=dd[0]
        disp=next(iter(dispositions))
        drows.append(dict(fragment_id=fid,expected_fragment_version=d['expected_fragment_version'],
                 page_id='' if f.get('page_id') is None else str(f['page_id']),
                 marquee_id='' if not marqs else str(marqs[0]['id']),
                 fragment_type_before='' if f.get('type') is None else str(f['type']),
                 year=str(f['year']),month=str(f['month']),day=str(f['day']),
                 sequence=str(f['sequence']),original_html_sha256=d['source_html_sha256'],
                 embedded_image_count=str(len(dd)),disposition=disp,
                 review_note=d.get('review_note',''),
                 reviewed_by=d.get('reviewed_by',''),reviewed_at=d.get('reviewed_at','')))
    require(len(drows)==72 and len(irows)==72 and len(vrows)==72,
            'Expected 72 unique source Fragments and occurrences')
    require(sum(1 for r in vrows if r['link_handling']=='PRESERVE')==30,
            'Expected 30 preserved links')
    require(sum(1 for r in vrows if r['marquee_handling']=='PRESERVE')==22,
            'Expected 22 preserved Marquees')
    return drows,irows,vrows,summary

def write_csv(p,fields,rows):
    with Path(p).open('w',encoding='utf-8',newline='') as stream:
        w=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n')
        w.writeheader();w.writerows(rows)

def main():
    ap=argparse.ArgumentParser()
    for name in ('review','snapshot','mapping','check','summary','output'):
        ap.add_argument('--'+name,required=True)
    a=ap.parse_args()
    input_paths={key:Path(getattr(a,key)) for key in ('review','snapshot','mapping','check','summary')}
    for key,path in input_paths.items():
        require(path.is_file(),'Missing {}: {}'.format(key,path))
    dest=Path(a.output)
    require(not dest.exists(),'Output already exists: {}'.format(dest))
    drows,irows,vrows,reconcile=assemble(input_paths['review'],input_paths['snapshot'],
                                          input_paths['mapping'],input_paths['check'],input_paths['summary'])
    dest.mkdir(parents=True,mode=0o700)
    os.chmod(str(dest),0o700)
    files={
        '0028-dispositions.csv':(D_FIELDS,drows),
        '0028-image-decisions.csv':(I_FIELDS,irows),
        '0028-v2-preservation-decisions.PRIVATE.csv':(V_FIELDS,vrows),
    }
    for name,(fields,rows) in files.items(): write_csv(dest/name,fields,rows)
    counts={'reviewed_fragments':len(drows),'reviewed_occurrences':len(irows),
            'CONVERT_TO_IMAGE':71,'DEFER':1,'links_preserved':30,
            'marquees_preserved':22,'image_ids_corrected_by_0052':['3','18']}
    report={'schema':'0028-step1-prepared-migration-inputs-v1',
            'status':'PREPARED_NOT_APPROVED',
            'productionApplyAllowed':False,'migrationApproved':False,
            'counts':counts,'source_production_snapshot_timestamp':reconcile.get('snapshot_timestamp'),
            'inputs_sha256':{k:sha_file(p) for k,p in input_paths.items()},
            'output_sha256':{n:sha_file(dest/n) for n in files},
            'requires':'Owner signoff + Step 2 validation and rehearsal + separate production apply approval',
            'notes':['Current values are source preimages. V2 sidecar supplies reviewed destination Page and preservation policy.',
                     'CSV paths and link URLs are PRIVATE evidence, do not add to public Git.',
                     'These files are an implementation input, NOT an apply plan or authorisation.']}
    (dest/'PREPARATION-RESULT.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    with (dest/'SHA256SUMS.txt').open('w',encoding='utf-8') as f:
        for name in sorted(list(files)+['PREPARATION-RESULT.json']):
            f.write('{}  {}\n'.format(sha_file(dest/name),name))
    print('PASS: PREPARED_NOT_APPROVED — 72 fragments, 71 conversions, 1 DEFER')
    print('PASS: preserving 30 original image links and 22 Marquees')
    print('PASS: frozen manifest inputs have file hashes and snapshot/review identities')
    print('Output (PRIVATE): {}'.format(dest))
    print('Production apply NOT authorised')

if __name__=='__main__':
    try: main()
    except (OSError,ValueError,KeyError,TypeError,IndexError) as exc:
        sys.exit('FAIL: '+str(exc))
