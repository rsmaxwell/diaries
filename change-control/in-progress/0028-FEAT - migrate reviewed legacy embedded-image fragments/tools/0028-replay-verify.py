#!/usr/bin/env python3
"""0028 disposable MQTT + Reader rehearsal fixtures. No production credentials or writes."""
import argparse
import base64
import csv
import hashlib
import json
import math
from pathlib import Path
import secrets
import sys


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_rows(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def load_manifest(path):
    images = load_rows(path / '0028-image-decisions.csv')
    extra = load_rows(path / '0028-v2-preservation-decisions.PRIVATE.csv')
    dispositions = load_rows(path / '0028-dispositions.csv')
    require(len(images) == len(extra) == len(dispositions) == 72, 'Review must have 72 rows')
    # The occurrence_action field is not guaranteed to equal the disposition;
    # the authoritative conversion decision is the disposition CSV.
    by_id = {int(r['fragment_id']): r for r in dispositions}
    require(len(by_id) == 72, 'Duplicate Fragment ID')
    require(sum(r['disposition'] == 'CONVERT_TO_IMAGE' for r in dispositions) == 71,
            'Expected 71 conversions')
    require(sum(r['disposition'] == 'DEFER' for r in dispositions) == 1,
            'Expected one DEFER')
    require(next(int(r['fragment_id']) for r in dispositions if r['disposition']=='DEFER') == 1564,
            'Unexpected deferred Fragment')
    eligible = [r for r in images if by_id[int(r['fragment_id'])]['disposition']=='CONVERT_TO_IMAGE']
    require(len(eligible) == 71, 'Expected 71 resolved image decisions')
    keys = {(int(r['fragment_id']), int(r['embedded_image_ordinal'])) for r in eligible}
    require(len(keys)==71, 'Duplicate conversion key')
    require(all(int(r['fragment_id']) in by_id for r in extra), 'Unknown V2 record')
    vmap = {(int(r['fragment_id']), int(r['embedded_image_ordinal'])):r for r in extra}
    require(len(vmap)==72, 'Duplicate V2 sidecar key')
    for r in eligible:
        key=(int(r['fragment_id']), int(r['embedded_image_ordinal']))
        require(key in vmap and int(r['resolved_image_id'])>0, f'Incomplete decision: {key}')
    return eligible, vmap


def generate(manifest, output):
    eligible, vmap = load_manifest(manifest)
    require(output.is_dir() and not any(output.iterdir()), 'Refusing non-empty output directory')
    def write(name, obj):
        (output / name).write_text(json.dumps(obj, indent=2, sort_keys=True)+'\n',encoding='utf-8')
    # Deliberately not using developer/production settings, usernames or secrets.
    # Containers use their own Docker bridge and the already migrated *isolated* DB.
    responder = {
        'mqtt': {'host':'diaries-0028-replay-broker','port':1883,
                 'user': {'username':'rehearsal-responder','password':secrets.token_urlsafe(24)}},
        'db': {'host':'diaries-0028-rehearsal-db','port':5432,
               'database':'diaries_0028_rehearsal',
               'jdbc': {'dbms':'postgresql','driver':'org.postgresql.Driver'},
               'admin':{'username':'postgres','password':''},
               'additionalConnectionProperties': {'hibernate.hbm2ddl.auto':'validate',
                                                   'jakarta.persistence.schema-generation.database.action':'none'}},
        'diaries': {'root':'/data','diaries':'diaries','files':'files-root',
                    'baseUrl':'http://diaries-0028-replay-responder:8081'},
        'refreshPeriod':'5m', 'refreshExpiration':'7d',
        'secret':base64.b64encode(secrets.token_bytes(48)).decode('ascii'),
        'normaliseOnStartup':False,'fragmentLockTtlSeconds':3600
    }
    reader = {
        'http': {'host':'0.0.0.0','port':8082,'basePath':'/',
                 'publicBaseUrl':'http://127.0.0.1:58082'},
        'mqtt': {'host':'diaries-0028-replay-broker','port':1883,
                 'clientId':'diaries-0028-replay-reader', 'topicPrefix':'diaries',
                 'keepAliveSeconds':30,'connectTimeoutSeconds':10,
                 'reconnectDelaySeconds':2,'cleanStart':True},
        'projection': {'initialReplayQuietPeriodMillis':1500,'initialReplayTimeoutSeconds':45},
        'content': {'responderBaseUrl':'http://diaries-0028-replay-responder:8081',
                    'publicResponderBaseUrl':'http://127.0.0.1:58081',
                    'diariesPath':'diaries','filesPath':'files'},
        'site': {'title':'Diaries 0028 ISOLATED REHEARSAL',
                 'description':'Disposable migrated database reader check',
                 'defaultLocale':'en-GB','zoneId':'Europe/London'}
    }
    write('responder.ISOLATED.PRIVATE.json', responder)
    write('reader.ISOLATED.PRIVATE.json', reader)
    (output/'mosquitto.ISOLATED.conf').write_text('listener 1883 0.0.0.0\nallow_anonymous true\npersistence false\nmax_queued_messages 20000\n',encoding='utf-8')
    topics = [f'diaries/fragments/{r["fragment_id"]}' for r in eligible]
    expected=[]
    for r in eligible:
        key=(int(r['fragment_id']),int(r['embedded_image_ordinal']))
        v=vmap[key]
        expected.append({'fragment_id':key[0], 'image_id':int(r['resolved_image_id']),
          'page_id':int(v['approved_page_id']),
          'text':r['image_text'],
          'link':v.get('image_link_url_PRIVATE') or None,
          'marquee_id':int(v['source_marquee_id']) if v['marquee_handling']=='PRESERVE' else None,
          'image_path':r['resolved_relative_path']})
    write('EXPECTED.PRIVATE.json', expected)
    marquees=[{'marquee_id':e['marquee_id'],'fragment_id':e['fragment_id'],
               'page_id':e['page_id']} for e in expected if e['marquee_id'] is not None]
    require(len(marquees)==22 and len({m['marquee_id'] for m in marquees})==22,
            'Expected exactly 22 distinct preserved Marquee associations')
    write('EXPECTED-MARQUEES.PRIVATE.json', marquees)
    print('PASS: configured isolated responder and Reader for 71 conversions; MQTT broker has no host port')


def validate_retained(expected_path, input_path):
    expected=json.loads(expected_path.read_text(encoding='utf-8'))
    received={}
    with input_path.open(encoding='utf-8') as f:
        for line in f:
            line=line.rstrip('\r\n')
            if not line: continue
            require('|||' in line, 'Unrecognised MQTT output format')
            topic,payload=line.split('|||',1)
            fid=int(topic.rsplit('/',1)[-1])
            require(topic==f'diaries/fragments/{fid}', f'Unexpected topic: {topic}')
            require(fid not in received, f'Duplicate retained Fragment {fid}')
            received[fid]=json.loads(payload)
    require(len(received)==len(expected)==71, 'Missing MQTT retained Fragment topics')
    for e in expected:
        fid=e['fragment_id']
        require(fid in received, f'Fragment MQTT missing: {fid}')
        r=received[fid]
        require(r.get('id')==fid and r.get('type')=='IMAGE', f'Wrong MQTT ID or type: {fid}')
        require(r.get('imageId')==e['image_id'], f'Image reference mismatch: {fid}')
        require(r.get('pageId')==e['page_id'], f'Page reference mismatch: {fid}')
        require(r.get('imageLinkUrl')==e['link'], f'Image link mismatch: {fid}')
        require(r.get('marqueeId')==e['marquee_id'], f'Marquee association mismatch: {fid}')
        require(r.get('text')==e['text'], f'Caption mismatch: {fid}')
    print('PASS: 71/71 retained MQTT Fragment topics match reviewed Image/Page/link/Marquee/caption')


def validate_marquees(expected_path, input_path):
    expected=json.loads(expected_path.read_text(encoding='utf-8'))
    require(len(expected)==22,'Expected 22 preserved Marquee records')
    received={}
    for line in input_path.read_text(encoding='utf-8').splitlines():
        if not line:continue
        require('|||' in line, 'Unrecognised Marquee MQTT output format')
        topic,payload=line.split('|||',1)
        mid=int(topic.rsplit('/',1)[-1])
        require(topic==f'diaries/marquees/{mid}' and mid not in received,
                'Unexpected or duplicate Marquee topic')
        received[mid]=json.loads(payload)
    require(len(received)==len(expected), 'Missing retained Marquee topics')
    for x in expected:
        mid=x['marquee_id'];require(mid in received, f'Missing Marquee topic {mid}')
        actual=received[mid]
        require(actual.get('id')==mid and actual.get('fragmentId')==x['fragment_id']
                and actual.get('pageId')==x['page_id'],
                f'Marquee identity/Fragment/Page reassignment: {mid}')
        rect=actual.get('rectangle')
        require(isinstance(rect,dict) and all(isinstance(rect.get(k),(float,int))
                and not isinstance(rect.get(k),bool) and math.isfinite(rect[k])
                for k in ('x','y','width','height')), f'Invalid Marquee rectangle: {mid}')
    print('PASS: all 22 retained Marquee topics preserve identity, Fragment and Page; finite geometry')


def main():
    ap=argparse.ArgumentParser()
    cmd=ap.add_subparsers(dest='cmd',required=True)
    g=cmd.add_parser('generate');g.add_argument('--manifest',type=Path,required=True);g.add_argument('--output',type=Path,required=True)
    v=cmd.add_parser('validate-retained');v.add_argument('--expected',type=Path,required=True);v.add_argument('--input',type=Path,required=True)
    m=cmd.add_parser('validate-marquees');m.add_argument('--expected',type=Path,required=True);m.add_argument('--input',type=Path,required=True)
    args=ap.parse_args()
    if args.cmd=='generate':generate(args.manifest,args.output)
    elif args.cmd=='validate-retained':validate_retained(args.expected,args.input)
    else:validate_marquees(args.expected,args.input)

if __name__=='__main__':
    try:main()
    except (ValueError,KeyError,TypeError,FileNotFoundError) as e:
        print('FAIL:',e,file=sys.stderr);sys.exit(1)
