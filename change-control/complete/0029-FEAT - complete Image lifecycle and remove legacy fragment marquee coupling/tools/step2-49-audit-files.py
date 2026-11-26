#!/usr/bin/env python3
"""0029 read-only audit: catalogue file SHA-256 and legacy img src resolution.
Usage: python3 script.py --files-root /path/to/diaries-content/files --manifest ... --output ...
No database connections or writes to the supplied Files root.
"""
import argparse,csv,hashlib,os,pathlib,sys
from collections import Counter

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def safe(root,relative):
    rel=pathlib.PurePosixPath(relative.replace('\\','/'))
    if rel.is_absolute() or '..' in rel.parts or not rel.parts:return None
    out=(root / pathlib.Path(*rel.parts)).resolve()
    try:out.relative_to(root)
    except ValueError:return None
    return out

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--files-root',required=True,type=pathlib.Path)
    ap.add_argument('--manifest',required=True,type=pathlib.Path)
    ap.add_argument('--output',required=True,type=pathlib.Path)
    a=ap.parse_args()
    root=a.files_root.expanduser().resolve()
    if not root.is_dir():ap.error('Files root not a directory: '+str(root))
    try:
        a.output.resolve().relative_to(root)
    except ValueError:
        pass
    else:
        ap.error('Evidence output must be OUTSIDE Files root')
    if a.output.exists():ap.error('Refusing to overwrite existing evidence: '+str(a.output))
    with a.manifest.open(newline='',encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
    if len(rows)!=49 or len({r['source_fragment_id'] for r in rows})!=49:ap.error('Manifest must have exactly 49 unique source rows')
    results=[]
    for r in rows:
        path=safe(root,r['catalogue_path'])
        state='UNSAFE_PATH' if path is None else ('MISSING' if not path.is_file() else 'PRESENT')
        actual=''
        if state=='PRESENT':
            try:actual=sha(path)
            except OSError:state='UNREADABLE'
            else:state='SHA256_PASS' if actual.lower()==r['catalogue_checksum'].lower() else 'SHA256_MISMATCH'
        # Legacy relative src is anchored at the diary directory; filenames can be
        # same physical path as catalogue. This alone DOES NOT establish original-byte equivalence.
        diary_prefix=pathlib.PurePosixPath(r['catalogue_path']).parent.parent.as_posix()
        old=safe(root,diary_prefix+'/'+r['legacy_src'].lstrip('/'))
        legacy_state='UNSAFE_PATH' if old is None else ('PRESENT' if old.is_file() else 'MISSING')
        legacy_sha=''
        if legacy_state=='PRESENT':
            try:legacy_sha=sha(old)
            except OSError:legacy_state='UNREADABLE'
        result=dict(source_fragment_id=r['source_fragment_id'],catalogue_id=r['catalogue_id'],proposed_page_id=r['proposed_page_id'],catalogue_path=r['catalogue_path'],catalogue_expected_sha256=r['catalogue_checksum'],catalogue_actual_sha256=actual,catalogue_file_status=state,legacy_src=r['legacy_src'],legacy_resolved_relative_path=old.relative_to(root).as_posix() if old is not None else '',legacy_src_status=legacy_state,legacy_src_sha256=legacy_sha,legacy_and_catalogue_same_path='YES' if old is not None and path==old else 'NO',legacy_and_catalogue_bytes_match='YES' if actual and legacy_sha and actual==legacy_sha else ('NO' if actual and legacy_sha else 'NOT_CHECKED'),original_historical_image_equivalence='NOT_ESTABLISHED',migration_approval='PENDING')
        results.append(result)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=results[0].keys());writer.writeheader();writer.writerows(results)
    counts=Counter(x['catalogue_file_status'] for x in results)
    print('Files root:',root)
    print('Evidence:',a.output)
    print('Catalogue statuses:',dict(counts))
    print('Legacy same-path count:',sum(r['legacy_and_catalogue_same_path']=='YES' for r in results))
    print('Historical byte equivalence: NOT ESTABLISHED from this audit')
    if counts.get('SHA256_PASS',0)==49:print('PASS: 49/49 catalogue-file checksums match database manifest (48 distinct Images)')
    else:
        print('FAIL: not all 49 catalogue checksums verified');return 1
    return 0
if __name__=='__main__':sys.exit(main())
