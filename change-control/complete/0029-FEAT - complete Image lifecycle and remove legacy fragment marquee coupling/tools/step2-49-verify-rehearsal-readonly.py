#!/usr/bin/env python3
# Validate 49 reviewed candidate placements; output psql read-only SQL or validate psql CSV.
import argparse,csv,hashlib,pathlib,sys
p=argparse.ArgumentParser();p.add_argument('action',choices=['generate','check']);p.add_argument('--mapping',required=True);p.add_argument('--source',required=True);p.add_argument('--pages',required=True);p.add_argument('--result');a=p.parse_args()
def read(path):
 with open(path,newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
m=read(a.mapping);s=read(a.source);pg=read(a.pages)
def fail(msg): raise SystemExit('FAIL: '+msg)
if len(m)!=49 or len(s)!=49 or len({x['source_fragment_id'] for x in m})!=49:fail('expected exactly 49 distinct mapping and source records')
S={x['source_fragment_id']:x for x in s};P={(x['source_fragment_id'],x['candidate_page_id']):x for x in pg}
for x in m:
 k=x['source_fragment_id'];v=S.get(k)
 if v is None:fail('missing source '+k)
 if v['source_unchanged']!='t' or v['source_html_md5']!=x['source_html_md5'] or hashlib.md5(v['original_html'].encode()).hexdigest()!=x['source_html_md5']:fail('HTML drift or checksum mismatch '+k)
 if v['catalogue_id']!=x['catalogue_id'] or v['catalogue_checksum']!=x['catalogue_checksum']:fail('catalogue identity drift '+k)
 if x['migration_approval']!='PENDING':fail('unexpected approval flag '+k)
 page=x['proposed_page_id']
 if not page or (k,page) not in P:fail('no supporting Page candidate '+k)
 ctx=P[k,page]
 if ctx['matched_page_id']!=page or ctx['diary_id']!=x['proposed_diary_id']:fail('Page/Diary mismatch '+k)
 if x['status']=='SEQUENCE_CONTEXT_PROVISIONAL' and (k not in ('611','612','613') or page!='756'):fail('unexpected sequence-based assignment '+k)
 if x['content_equivalence']!='NOT_VERIFIED' or x['source_image_byte_match']!='NOT_VERIFIED':fail('content claims not supported '+k)
print('PASS: local CSV cross-check 49/49; all migration approvals pending',file=sys.stderr)
if a.action=='generate':
 def q(v):return "'"+v.replace("'","''")+"'"
 rows=[]
 for x in m:
  rows.append('('+','.join([x['source_fragment_id'],x['catalogue_id'],x['proposed_page_id'],x['proposed_diary_id'],str(x['year']),str(x['month']),str(x['day']),q(x['sequence']),q(x['source_html_md5']),q(x['catalogue_checksum'])])+')')
 sql='''BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout='90s';
COPY (
WITH expected(fragment_id,image_id,page_id,diary_id,yr,mon,dy,seq,html_md5,catalogue_sha256) AS (
VALUES
'''+',\n'.join(rows)+'''
), live AS (
SELECT e.fragment_id,e.image_id,e.page_id,e.diary_id,
 CASE WHEN f.id IS NULL THEN 'MISSING_SOURCE'
      WHEN f.page_id IS NOT NULL OR f.type IS NOT NULL OR f.image_id IS NOT NULL THEN 'SOURCE_ALREADY_CHANGED'
      WHEN md5(coalesce(f.text,'')) <> e.html_md5 THEN 'SOURCE_HTML_CHANGED'
      WHEN f.year <> e.yr OR f.month <> e.mon OR f.day <> e.dy OR f.sequence::numeric <> e.seq::numeric THEN 'SOURCE_DATE_SEQUENCE_CHANGED'
      WHEN i.id IS NULL OR coalesce(i.checksum,'') <> e.catalogue_sha256 THEN 'CATALOGUE_CHANGED'
      WHEN p.id IS NULL OR p.diary_id <> e.diary_id THEN 'PAGE_OWNER_CHANGED'
      ELSE 'READY_FOR_FURTHER_REVIEW' END AS status
FROM expected e
LEFT JOIN fragment f ON f.id=e.fragment_id
LEFT JOIN image i ON i.id=e.image_id
LEFT JOIN page p ON p.id=e.page_id
)
SELECT fragment_id,image_id,page_id,diary_id,status FROM live ORDER BY fragment_id
) TO STDOUT WITH (FORMAT CSV, HEADER TRUE);
COMMIT;
'''
 sys.stdout.write(sql)
else:
 if not a.result:fail('--result required')
 result=read(a.result)
 if len(result)!=49 or len({x['fragment_id'] for x in result})!=49:fail('database result row count mismatch')
 bad=[(x['fragment_id'],x['status']) for x in result if x['status']!='READY_FOR_FURTHER_REVIEW']
 if bad:fail('database drift '+str(bad))
 print('PASS: development database read-only snapshot matches 49 provisional candidate rows; NOT migration approval')
