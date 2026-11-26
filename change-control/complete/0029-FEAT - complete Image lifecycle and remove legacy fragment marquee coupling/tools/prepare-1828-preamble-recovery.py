#!/usr/bin/env python3
"""0029 recovery PREPARATION ONLY. Reads pre-cutover archive; writes SQL for review, never executes SQL."""
import argparse
import hashlib
import pathlib
import re
import subprocess
import sys

FEATURE = pathlib.Path(__file__).resolve().parent.parent
ARCHIVE = FEATURE / 'evidence/step-2-live-development-cutover/diaries-development-before-cutover-20261125-203144.dump'
OUTPUT = FEATURE / 'evidence/step-2-1828-preamble-recovery'
EXPECTED = (1, 2, 3)

def decode_copy(field):
    if field == r'\N':
        return None
    res=[];i=0
    translate={'b':'\b','f':'\f','n':'\n','r':'\r','t':'\t','v':'\v','\\':'\\'}
    while i < len(field):
        if field[i] != '\\': res.append(field[i]);i+=1;continue
        i+=1
        if i >= len(field): raise ValueError('Trailing COPY backslash')
        c=field[i]
        if c in translate: res.append(translate[c]);i+=1
        elif c=='x':
            digits=field[i+1:i+3]
            if not re.fullmatch('[0-9a-fA-F]{1,2}',digits): raise ValueError('Bad COPY hex')
            res.append(chr(int(digits,16)));i+=1+len(digits)
        elif c in '01234567':
            m=re.match(r'[0-7]{1,3}',field[i:]);res.append(chr(int(m.group(),8)));i+=len(m.group())
        else: res.append(c);i+=1
    return ''.join(res)

def quote(v):
    if v is None: return 'NULL'
    return "'" + str(v).replace("'","''") + "'"

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=pathlib.Path,default=ARCHIVE)
    p.add_argument('--container',default='diaries-development-db')
    args=p.parse_args()
    if not args.archive.is_file(): sys.exit('FAIL: backup missing: '+str(args.archive))
    archive=args.archive.read_bytes()
    print('Backup:',args.archive)
    print('Backup size:',len(archive),'SHA256:',hashlib.sha256(archive).hexdigest())
    command=['docker','exec','-i',args.container,'pg_restore','--data-only','--table=fragment','--file=-']
    result=subprocess.run(command,input=archive,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if result.returncode:
        sys.exit('FAIL: pg_restore extraction: '+result.stderr.decode(errors='replace')[-1500:])
    dump=result.stdout.decode('utf-8')
    matches=list(re.finditer(r'(?m)^COPY (?:public\.)?fragment \(([^\r\n]+)\) FROM stdin;\r?\n',dump))
    if len(matches)!=1: sys.exit(f'FAIL: expected exactly one fragment COPY block; found {len(matches)}')
    m=matches[0]
    cols=[v.strip().strip('"') for v in m.group(1).split(',')]
    lines=dump[m.end():].splitlines()
    records={}
    found_end=False
    for line in lines:
        if line==r'\.': found_end=True;break
        fields=line.split('\t')
        if len(fields)!=len(cols): sys.exit(f'FAIL: COPY column count mismatch: {len(fields)} vs {len(cols)}')
        row=dict(zip(cols,map(decode_copy,fields)))
        if row.get('id') in [str(i) for i in EXPECTED]:
            key=int(row['id'])
            if key in records: sys.exit(f'FAIL: duplicate source ID {key}')
            records[key]=row
    if not found_end: sys.exit('FAIL: fragment COPY terminator missing')
    if set(records)!=set(EXPECTED): sys.exit(f'FAIL: source IDs incomplete: {sorted(records)}')
    for id in EXPECTED:
        row=records[id]
        for k in ('id','version','year','month','day','sequence','text','page_id','type'):
            if k not in row: sys.exit('FAIL: missing source column '+k)
        if row['year']!='1828' or row['month']!='1' or row['day']!='1' or row['page_id'] is not None or row['type'] is not None or not row['text']:
            sys.exit(f'FAIL: unexpected original source ownership for fragment {id}')
        print(f"Source {id}: version={row['version']} date={row['year']}-{row['month']}-{row['day']} sequence={row['sequence']} text_chars={len(row['text'])} text_sha256={hashlib.sha256(row['text'].encode()).hexdigest()}")
    OUTPUT.mkdir(parents=True,exist_ok=True)
    output=OUTPUT/'restore-1828-preamble-1-2-3.sql'
    sql=["-- GENERATED RECOVERY PROPOSAL: REVIEW AND OBTAIN EXPLICIT APPROVAL BEFORE EXECUTION", "-- Only applies to the local development database. Never run on production.","\\set ON_ERROR_STOP on",'BEGIN;',"SET LOCAL lock_timeout='5s';","LOCK TABLE public.fragment IN SHARE ROW EXCLUSIVE MODE;", "DO $guard$", "DECLARE n integer;", "BEGIN", " SELECT count(*) INTO n FROM public.fragment WHERE id IN (1,2,3,2348,2349);", " IF n<>2 THEN RAISE EXCEPTION 'Expected only temporary Fragment IDs 2348 and 2349; found % rows',n; END IF;", " IF EXISTS (SELECT 1 FROM public.fragment WHERE id IN (1,2,3)) THEN RAISE EXCEPTION 'Historical IDs already present'; END IF;", " IF (SELECT count(*) FROM public.fragment WHERE diary_id=1 AND year=1828 AND placement='PREAMBLE')<>2 THEN RAISE EXCEPTION 'Unexpected 1828 PREAMBLE count'; END IF;", " IF NOT EXISTS (SELECT 1 FROM public.fragment WHERE id=2348 AND diary_id=1 AND year=1828 AND placement='PREAMBLE' AND type='TEXT' AND page_id IS NULL AND coalesce(text,'')='') THEN RAISE EXCEPTION 'Temporary Fragment 2348 changed'; END IF;", " IF NOT EXISTS (SELECT 1 FROM public.fragment WHERE id=2349 AND diary_id=1 AND year=1828 AND placement='PREAMBLE' AND type='TEXT' AND page_id IS NULL AND text LIKE '%0029%annual%PREAMBLE%') THEN RAISE EXCEPTION 'Temporary Fragment 2349 changed'; END IF;", " IF EXISTS (SELECT 1 FROM public.marquee WHERE fragment_id IN (1,2,3,2348,2349)) THEN RAISE EXCEPTION 'Unexpected Marquee ownership'; END IF;", "END $guard$;", "DELETE FROM public.fragment WHERE id IN (2348,2349);", "INSERT INTO public.fragment (id,version,year,month,day,sequence,text,page_id,diary_id,placement,type,image_id,image_link_url) VALUES"]
    tuples=[]
    for id in EXPECTED:
        r=records[id]
        vals=[str(id),str(int(r['version'])),str(int(r['year'])),str(int(r['month'])),str(int(r['day'])),quote(r['sequence']),quote(r['text']),'NULL','1',quote('PREAMBLE'),quote('TEXT'),'NULL','NULL']
        tuples.append('  ('+', '.join(vals)+')')
    sql.append(',\n'.join(tuples)+';')
    sql.extend(["DO $verify$", "DECLARE n integer;", "BEGIN", " SELECT count(*) INTO n FROM public.fragment WHERE diary_id=1 AND year=1828 AND placement='PREAMBLE';", " IF n<>3 THEN RAISE EXCEPTION 'Unexpected recovered PREAMBLE count: %',n; END IF;", " IF EXISTS (SELECT 1 FROM public.fragment WHERE id IN (2348,2349)) THEN RAISE EXCEPTION 'Temporary fragments remain'; END IF;", "END $verify$;", "SELECT id,diary_id,placement,type,year,month,day,sequence,page_id,length(text) AS text_length FROM public.fragment WHERE id IN (1,2,3) ORDER BY sequence,id;", "COMMIT;"])
    output.write_text('\n'.join(sql)+'\n',encoding='utf-8')
    print('PREPARED (not executed):',output)
    print('SQL SHA256:',hashlib.sha256(output.read_bytes()).hexdigest())
    print('STOP: SQL has NOT been executed. Approval and a fresh current-development backup are required.')

if __name__=='__main__': main()
