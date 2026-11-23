#!/usr/bin/env python3
"""0052-DEF controlled in-place repair of catalogue Images 3 and 18.

Run from Windows Cygwin. By default performs only preflight. Applying changes
requires --apply; uses no extra credentials beyond existing Docker/SSH access.
Private evidence and rollback backups remain inside this feature directory.
No schema changes, Fragment writes, new Image IDs or MQTT client publications.
"""
from __future__ import annotations
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile

DIARY = 'diary-1828-and-1829-and-jan-1830'
IMG3 = 'img2840-image-map-whitley-park.jpg'
IMG18 = 'img2900-image-hermitage.png'
RELATIVE = f'{DIARY}/images'
SHA_APPROVED_MAP_PNG = 'd9f54457b8b4ac67a9a91df5e8c7c32c2767531dd2d6461c3f7faf9c31e4706a'
SHA_APPROVED_HERMITAGE = '9cbe68505a023ad9db4898914c5bf763cce4fb33b6689364586350d58d6411e0'
BEFORE = {
    3: {'version': 0, 'relative_path': RELATIVE+'/'+IMG3, 'mime_type': 'image/jpeg',
        'original_filename': IMG3, 'width': 1060, 'height': 718,
        'checksum': '0ec1199bb262f2c720737a6fcd71549549ea8727784d5b09e3602fcd6d2d69ba'},
    18: {'version': 0, 'relative_path': RELATIVE+'/'+IMG18, 'mime_type': 'image/png',
         'original_filename': IMG18, 'width': 1859, 'height': 1084,
         'checksum': '2097979bd1ca47370a55c0f6053167a96f541a5c04adfe4ff52dc564ccc97d5a'},
}
PROTECTED = ['img2903-image-st-isaac-church.png',
             'img2900-image-the-jordan-staircase-state-hermitage-museum-st-petersburg-russia-B2KPFE.jpg']
FEATURE = Path(__file__).resolve().parent.parent
NAS = Path(os.environ.get('DIARIES_NAS_CONTENT_ROOT',
    '/cygdrive/p/nancy-and-ronald-maxwell/documents/sea-captains-chest/diaries-content'))
META = NAS/'diaries'/DIARY/'metadata'/'images-root'
TARGET_ROOTS = {
    'development': NAS/'files-development-common'/RELATIVE,
    'production': NAS/'files'/RELATIVE,
}

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()

def ensure_hash(path: Path, expected: str, label: str):
    if not path.is_file(): raise RuntimeError(f'{label}: file missing: {path}')
    actual = sha(path)
    if actual != expected: raise RuntimeError(f'{label}: SHA-256 mismatch: got {actual}, expected {expected}')
    print(f'PASS: {label}: {actual}')

def run(args: list[str], *, input_text: str | None = None, log: Path | None = None, cwd: Path | None = None):
    proc = subprocess.run(args, input=input_text, text=True, capture_output=True, cwd=cwd)
    if log: log.write_text(f'$ {args!r}\nexit={proc.returncode}\n{proc.stdout}\n{proc.stderr}', encoding='utf-8')
    if proc.returncode:
        raise RuntimeError(f'Command failed ({proc.returncode}): {args[0]} (details: {log or proc.stderr[-500:]})')
    return proc.stdout

def psql(env: str, sql: str, *, log: Path | None = None) -> str:
    psqlcmd = 'exec psql -X -A -t -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
    if env == 'production':
        args = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=12', 'pluto',
                f"docker exec -i diaries-postgres sh -c '{psqlcmd}'"]
    else:
        # development-infrastructure compose service uses diaries-development-db.
        args = ['docker','exec','-i','diaries-development-db','sh','-c',psqlcmd]
    return run(args, input_text=sql, log=log)

def read_db(env: str, log: Path | None = None) -> dict[int, dict]:
    sql = """BEGIN READ ONLY;
SELECT row_to_json(r) FROM (SELECT id, version, relative_path, mime_type, original_filename,
width, height, checksum, caption, alt_text FROM public.image WHERE id IN (3,18) ORDER BY id) r;
COMMIT;
"""
    out = psql(env, sql, log=log)
    rows = [json.loads(line) for line in out.splitlines() if line.strip().startswith('{')]
    if {x['id'] for x in rows} != {3, 18}: raise RuntimeError(f'{env} catalogue: expected Image IDs 3 and 18')
    return {x['id']: x for x in rows}

def read_references(env: str, log: Path | None = None) -> dict:
    # Hash text rather than export diary HTML into the public execution report.
    sql = """BEGIN READ ONLY;
SELECT json_build_object(
  'image3', COALESCE((SELECT json_agg(id ORDER BY id) FROM public.fragment WHERE image_id=3), '[]'::json),
  'image18', COALESCE((SELECT json_agg(id ORDER BY id) FROM public.fragment WHERE image_id=18), '[]'::json),
  'whitley_legacy', COALESCE((SELECT json_agg(id ORDER BY id) FROM public.fragment
                            WHERE lower(text) LIKE '%img2840-image-map-whitley-park%'), '[]'::json),
  'hermitage_legacy', COALESCE((SELECT json_agg(id ORDER BY id) FROM public.fragment
                              WHERE lower(text) LIKE '%img2900-image-hermitage%'), '[]'::json),
  'affected_fragments', COALESCE((SELECT json_agg(row_to_json(f) ORDER BY f.id) FROM (
       SELECT id,version,type,image_id,page_id,year,month,day,sequence,image_link_url,
              md5(coalesce(text,'')) AS html_md5
       FROM public.fragment WHERE id IN (84,598,606,2332,2334,2338)
       ORDER BY id) f), '[]'::json),
  'affected_marquees', COALESCE((SELECT json_agg(row_to_json(m) ORDER BY m.id) FROM (
       SELECT id,version,fragment_id,page_id,x,y,width,height
       FROM public.marquee WHERE fragment_id IN (84,598,606,2332,2334,2338)
       ORDER BY id) m), '[]'::json)
)::text;
COMMIT;
"""
    out=psql(env,sql,log=log)
    rows=[json.loads(line) for line in out.splitlines() if line.strip().startswith('{')]
    if len(rows)!=1: raise RuntimeError(f'{env}: expected one reference-snapshot JSON row')
    expected_ids = [2332,2334] if env=='production' else [2338]
    for key, expected in [('image3',expected_ids),('image18',[]),
                          ('whitley_legacy',[84]),('hermitage_legacy',[598])]:
        if rows[0][key]!=expected:
            raise RuntimeError(f'{env}: consumer drift in {key}: {rows[0][key]} != {expected}')
    return rows[0]

def guard_metadata(rows, expected):
    for ident, fields in expected.items():
        for key, value in fields.items():
            if rows[ident][key] != value:
                raise RuntimeError(f'Catalogue drift for Image {ident}.{key}: {rows[ident][key]!r} vs {value!r}')

def make_jpeg(work: Path) -> Path:
    source = META/'source'/'img2840-whitley-park-map'/'whitley-park-historical-map-large.png'
    ensure_hash(source, SHA_APPROVED_MAP_PNG, 'Approved Whitley PNG')
    target = work/'whitley-approved-776x502-Q99.jpg'
    converter = Path(__file__).with_name('WhitleyToJpeg.java')
    if not converter.is_file(): raise RuntimeError(f'Missing JPEG converter: {converter}')
    # On Cygwin, java.exe is usually the native Windows JDK; convert paths for it.
    # The Python process itself must be Cygwin Python (native Windows Python
    # cannot open /cygdrive/... paths).
    def jpath(p: Path) -> str:
        if str(p).startswith('/cygdrive/'):
            return run(['cygpath', '-w', str(p)]).strip()
        return str(p)
    run(['java', jpath(converter), jpath(source), jpath(target)], log=work/'jpeg-conversion.log')
    if not target.is_file() or not target.read_bytes()[:3] == b'\xff\xd8\xff':
        raise RuntimeError('Generated JPEG header missing or invalid')
    print(f'PASS: converted JPEG: {target.stat().st_size} bytes, SHA-256 {sha(target)}')
    return target

def check_png(path: Path, expected: str, width: int, height: int):
    ensure_hash(path, expected, path.name)
    with path.open('rb') as f: header = f.read(24)
    if header[:16] != b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR': raise RuntimeError(f'Invalid PNG header: {path}')
    dims = (int.from_bytes(header[16:20],'big'), int.from_bytes(header[20:24], 'big'))
    if dims != (width,height): raise RuntimeError(f'Unexpected PNG size: {path}: {dims}')

def stop_production(log: Path):
    # Stop only the Diaries responder for the short file/DB correction window.
    run(['ssh','-o','BatchMode=yes','pluto','docker stop diaries-responder'],log=log)

def start_production(log: Path):
    run(['ssh','-o','BatchMode=yes','pluto','docker start diaries-responder'],log=log)

def local_responder_running() -> bool:
    try:
        sock=socket.create_connection(('127.0.0.1',8081), timeout=1)
        sock.close();return True
    except OSError: return False

def backup_file(path: Path, target: Path, manifest: list):
    target.parent.mkdir(parents=True,exist_ok=True)
    if path.is_file():
        shutil.copy2(path,target)
        if sha(path)!=sha(target):raise RuntimeError(f'Backup mismatch: {path}')
        manifest.append({'path':str(path),'backup':str(target),'old_sha256':sha(path),'existed':True})
    elif path.exists():
        raise RuntimeError(f'Unexpected non-file target: {path}')
    else:
        manifest.append({'path':str(path),'backup':'','old_sha256':None,'existed':False})

def atomic_copy(source: Path, target: Path):
    target.parent.mkdir(parents=True,exist_ok=True)
    tempname = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix='.0052-stage-', delete=False) as f:
            tempname=Path(f.name)
            with source.open('rb') as inp: shutil.copyfileobj(inp,f)
            f.flush();os.fsync(f.fileno())
        if sha(tempname)!=sha(source):raise RuntimeError(f'Staged checksum differs from approved file: {target}')
        os.replace(tempname,target)
    finally:
        if tempname is not None and tempname.exists(): tempname.unlink()
    ensure_hash(target,sha(source),f'Written {target.name}')

def write_sql(new_jpeg_sha: str, *, reverse: bool = False) -> str:
    if len(new_jpeg_sha)!=64 or any(c not in '0123456789abcdef' for c in new_jpeg_sha): raise ValueError('JPEG SHA invalid')
    if reverse:
        old3, new3, old18, new18, w3,h3,w18,h18, version3,version18=(new_jpeg_sha, BEFORE[3]['checksum'],SHA_APPROVED_HERMITAGE,BEFORE[18]['checksum'],1060,718,1859,1084,1,1)
        comment = 'Rollback Image 3 and Image 18 to their original metadata'
    else:
        old3, new3, old18, new18, w3,h3,w18,h18, version3,version18=(BEFORE[3]['checksum'],new_jpeg_sha,BEFORE[18]['checksum'],SHA_APPROVED_HERMITAGE,776,502,720,480,0,0)
        comment = 'Apply Image 3 and Image 18 corrected metadata'
    # Check all original path/mime/version/hash/dimensions atomically before either update.
    newversion=0 if reverse else 1
    expected3= (776,502) if reverse else (1060,718)
    expected18= (720,480) if reverse else (1859,1084)
    return f"""-- {comment}\nBEGIN;
SELECT id FROM public.image WHERE id IN (3,18) FOR UPDATE;
DO $verify$
BEGIN
 IF NOT EXISTS (SELECT 1 FROM public.image WHERE id=3 AND version={version3}
   AND relative_path='{RELATIVE}/{IMG3}' AND mime_type='image/jpeg'
   AND original_filename='{IMG3}' AND width={expected3[0]} AND height={expected3[1]}
   AND checksum='{old3}') THEN
   RAISE EXCEPTION '0052 Image 3 changed before update'; END IF;
 IF NOT EXISTS (SELECT 1 FROM public.image WHERE id=18 AND version={version18}
   AND relative_path='{RELATIVE}/{IMG18}' AND mime_type='image/png'
   AND original_filename='{IMG18}' AND width={expected18[0]} AND height={expected18[1]}
   AND checksum='{old18}') THEN
   RAISE EXCEPTION '0052 Image 18 changed before update'; END IF;
END
$verify$;
UPDATE public.image SET version={newversion}, width={w3},height={h3},checksum='{new3}' WHERE id=3;
UPDATE public.image SET version={newversion}, width={w18},height={h18},checksum='{new18}' WHERE id=18;
COMMIT;
"""

def restore_files(manifest: list[dict]):
    for entry in reversed(manifest):
        dest=Path(entry['path'])
        if entry['existed']:
            src=Path(entry['backup'])
            ensure_hash(src,entry['old_sha256'],f'Rollback backup for {dest.name}')
            atomic_copy(src,dest)
        elif dest.exists():
            # Only creation under this tracked run is removed. No recursive deletion.
            if not dest.is_file():raise RuntimeError(f'Rollback encountered non-regular file: {dest}')
            dest.unlink()

def write_json(path:Path, data):
    path.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n',encoding='utf-8')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true',help='EXPLICIT WRITE: update development and production Files and catalogue')
    parser.add_argument('--mode',choices=['both','production','development'],default='both')
    args=parser.parse_args()
    envs=['development','production'] if args.mode=='both' else [args.mode]
    timestamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    work=FEATURE/'evidence'/'Step 2'/'private'/timestamp
    work.mkdir(parents=True,exist_ok=False)
    print(f'0052 Step 2 {"APPLY" if args.apply else "PREFLIGHT ONLY"}; mode={args.mode}; evidence={work}')
    try:
        if os.name == 'nt':
            raise RuntimeError('Use Cygwin Python with /cygdrive paths, not native Windows Python')
        repo=FEATURE.parents[2]
        for label, cmd in [('branch',['git','branch','--show-current']),
                           ('revision',['git','rev-parse','HEAD']),
                           ('status',['git','status','--short']),
                           ('submodules',['git','submodule','status'])]:
            run(cmd, cwd=repo, log=work/f'git-{label}.log')
        print('PASS: repository branch, revision, status and submodules recorded')
        approved_hermitage=META/'source'/IMG18
        processed_hermitage=META/'images'/IMG18
        check_png(approved_hermitage,SHA_APPROVED_HERMITAGE,720,480)
        check_png(processed_hermitage,SHA_APPROVED_HERMITAGE,720,480)
        new_jpeg=make_jpeg(work)
        jpeg_sha=sha(new_jpeg)
        (work/'new-jpeg.sha256').write_text(f'{jpeg_sha}  {new_jpeg.name}\n',encoding='ascii')
        before={}
        protect={}
        references_before={}
        for env in envs:
            before[env]=read_db(env,work/f'{env}-before-db.log')
            references_before[env]=read_references(env,work/f'{env}-before-references.log')
            guard_metadata(before[env],BEFORE)
            for ident,oldfilename in [(3,IMG3),(18,IMG18)]:
                ensure_hash(TARGET_ROOTS[env]/oldfilename, BEFORE[ident]['checksum'], f'{env} currently served Image {ident}')
            protect[env]={x:sha(TARGET_ROOTS[env]/x) for x in PROTECTED}
            print(f'PASS: {env}: expected catalogue identities and served old-file checksums')
        write_json(work/'before-catalogue.json',before)
        write_json(work/'before-references.json',references_before)
        write_json(work/'protected-before.json',protect)
        if not args.apply:
            print('PASS: preflight complete — NO FILES, DATABASES, RESPONDERS OR MQTT CHANGED')
            print(f'New JPEG hash: {jpeg_sha}. Inspect its visual quality before --apply.')
            return 0
        if 'development' in envs and local_responder_running():
            raise RuntimeError('Local development responder appears active on port 8081. Stop it from your IDE before --apply; do not allow concurrent writes or stale MQTT state.')
        backup=[]
        targets=[(META/'source'/IMG3,new_jpeg),(META/'images'/IMG3,new_jpeg)]
        for env in envs:
            targets.extend([(TARGET_ROOTS[env]/IMG3,new_jpeg),(TARGET_ROOTS[env]/IMG18,approved_hermitage)])
        for i,(dest,src) in enumerate(targets):
            backup_file(dest,work/'original-files'/f'{i:02d}-{dest.name}',backup)
        write_json(work/'rollback-file-manifest.json',backup)
        write_json(work/'rollback-sql.json', {env:write_sql(jpeg_sha,reverse=True) for env in envs})
        write_json(work/'apply-manifest.json', {'mode':args.mode,'approved_whitley_png_sha256':SHA_APPROVED_MAP_PNG,
           'converted_whitley_jpeg_sha256':jpeg_sha,'approved_hermitage_png_sha256':SHA_APPROVED_HERMITAGE,
           'targets':[(str(a),str(b)) for a,b in targets]})
        print('PASS: original Files and catalogue rows backed up to private feature evidence')
        prod_stopped=False
        try:
            if 'production' in envs:
                stop_production(work/'production-stop-responder.log')
                prod_stopped=True
                print('Stopped production responder during controlled writes')
            for dest,src in targets:atomic_copy(src,dest)
            for env in envs:
                psql(env,write_sql(jpeg_sha),log=work/f'{env}-apply-db.log')
                expect={k:dict(v) for k,v in BEFORE.items()}
                expect[3].update(version=1,width=776,height=502,checksum=jpeg_sha)
                expect[18].update(version=1,width=720,height=480,checksum=SHA_APPROVED_HERMITAGE)
                guard_metadata(read_db(env,work/f'{env}-after-db.log'),expect)
                after_refs=read_references(env,work/f'{env}-after-references.log')
                if after_refs != references_before[env]:
                    raise RuntimeError(f'{env}: Fragment/Marquee references or metadata changed unexpectedly')
                for ident,filename,expected_hash in ((3,IMG3,jpeg_sha),(18,IMG18,SHA_APPROVED_HERMITAGE)):
                    ensure_hash(TARGET_ROOTS[env]/filename,expected_hash,f'{env} applied Image {ident}')
                for name,expected_hash in protect[env].items():
                    ensure_hash(TARGET_ROOTS[env]/name,expected_hash,f'{env} protected {name}')
            print('PASS: both catalogue rows and both served images reconciled for selected environment(s)')
        except Exception:
            print('ERROR: apply incomplete. Attempting automatic rollback of committed DB rows and Files.',file=sys.stderr)
            rollback_error=False
            for env in reversed(envs):
                try:
                    # A psql transport error can occur after server-side COMMIT.
                    # Always read the current row state before deciding whether to undo.
                    state=read_db(env,work/f'{env}-rollback-inspection-db.log')
                    expected_new={k:dict(v) for k,v in BEFORE.items()}
                    expected_new[3].update(version=1,width=776,height=502,checksum=jpeg_sha)
                    expected_new[18].update(version=1,width=720,height=480,checksum=SHA_APPROVED_HERMITAGE)
                    try:
                        guard_metadata(state,BEFORE)
                    except RuntimeError:
                        guard_metadata(state,expected_new)
                        psql(env,write_sql(jpeg_sha,reverse=True),log=work/f'{env}-auto-rollback-db.log')
                except Exception as e:
                    rollback_error=True;print(f'ROLLBACK DATABASE FAILED for {env}: {e}',file=sys.stderr)
            try:restore_files(backup)
            except Exception as e:rollback_error=True;print(f'ROLLBACK FILE FAILED: {e}',file=sys.stderr)
            if rollback_error:print('MANUAL RECOVERY REQUIRED using private backup and rollback-sql.json!',file=sys.stderr)
            else:print('ROLLBACK: original images and all committed Image metadata restored.',file=sys.stderr)
            raise
        finally:
            if prod_stopped:
                try:start_production(work/'production-start-responder.log')
                except Exception as e:print(f'URGENT: production responder did not restart: {e}',file=sys.stderr);raise
        print('PASS: Step 2 file/database correction applied; production responder restarted if applicable')
        print('REQUIRED: independently verify HTTP hashes, retained MQTT Image 3/18 metadata, and editor/reader visual acceptance.')
        print('REQUIRED: restart local development responder if development was modified, then check retained MQTT state.')
        print(f'ROLLBACK backups and SQL: {work}')
        return 0
    except Exception as exc:
        print(f'FAIL: {exc}',file=sys.stderr)
        print(f'Private diagnostic evidence: {work}',file=sys.stderr)
        return 1

if __name__=='__main__':sys.exit(main())
