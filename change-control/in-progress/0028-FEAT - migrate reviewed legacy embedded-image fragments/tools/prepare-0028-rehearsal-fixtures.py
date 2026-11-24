#!/usr/bin/env python3
"""Prepare PRIVATE, isolated-only 0028 rehearsal fixtures (Python 3.7+)."""
import argparse
import collections
import datetime
import hashlib
import json
from pathlib import Path
import sys


def write(path, content):
    if path.exists():
        raise ValueError('Refusing to overwrite existing evidence: {}'.format(path))
    path.write_text(content, encoding='utf-8')


def jsonwrite(path, value):
    write(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n')


def config(args):
    if not (1024 < args.port <= 65535):
        raise ValueError('Rehearsal port must be an unprivileged localhost port')
    if args.files_root.name != 'files-root' or not args.files_root.is_dir():
        raise ValueError('Rehearsal Files-root must be the staged files-root directory')
    root = args.windows_root
    if not root or ':' not in root:
        raise ValueError('Explicit absolute Windows Files-root parent is required')
    conf = {
        'db': {'host': '127.0.0.1', 'port': args.port,
               'database': 'diaries_0028_rehearsal',
               'jdbc': {'dbms': 'postgresql', 'driver': 'org.postgresql.Driver'},
               'admin': {'username': 'postgres', 'password': ''}},
        'diaries': {'root': str(root), 'files': 'files-root'}
    }
    jsonwrite(args.output, conf)
    print('PASS: generated isolated localhost rehearsal configuration; no production credentials')


def load_plan(path):
    plan = json.loads(path.read_text(encoding='utf-8'))
    if (plan.get('schemaVersion') != 1 or plan.get('mode') != 'dry-run' or
            len(plan.get('conversions', [])) != 71 or plan.get('deferredFragments') != [1564]):
        raise ValueError('Unexpected or non-reviewed 0028 dry-run plan')
    if plan.get('producedBy') != '0028-71-in-place-v1':
        raise ValueError('Unexpected migration tool revision')
    return plan


def make_approval(args):
    plan = load_plan(args.plan)
    if not args.operator.strip():
        raise ValueError('Rehearsal operator identity is required')
    approval = {
        'schema': '0028-apply-approval-v1',
        'scope': 'RESTORED_REHEARSAL',
        'writer_state': 'OFFLINE_WRITERS_STOPPED',
        'approved_by': 'isolated rehearsal operator: ' + args.operator,
        'approved_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'plan_sha256': hashlib.sha256(args.plan.read_bytes()).hexdigest(),
        'input_identity': plan['inputIdentity'],
        'database_identity': plan['databaseIdentity'],
        'files_root': plan['filesRoot']
    }
    jsonwrite(args.output, approval)
    print('PASS: rehearsal-only approval bound to plan/database/files identities; NOT PRODUCTION')


def generate(args):
    plan = load_plan(args.plan)
    groups = collections.OrderedDict()
    for p in plan['conversions']:
        groups.setdefault(p['date'], []).append(int(p['fragmentId']))
    if len(groups) < 2:
        raise ValueError('Expected multiple conversion dates for restart test')
    dates = list(groups.items())
    chosen = next(((date, ids) for date, ids in dates[1:] if len(ids) >= 2), None)
    if chosen is None:
        raise ValueError('Cannot find a multi-row date after the first committed date')
    failing_date, ids = chosen
    injection_id = ids[-1]
    earlier = sum(len(rows) for date, rows in dates if date < failing_date)
    if earlier <= 0:
        raise ValueError('Failure injection would not prove restart handling')
    all_ids = [int(p['fragmentId']) for p in plan['conversions']]
    ids_string = ','.join(str(i) for i in all_ids)
    # Exact stable row fingerprints for the entire otherwise-unmodified dataset.
    sql = '''\\set ON_ERROR_STOP on
SELECT 'fragment_count|' || count(*) FROM public.fragment;
SELECT 'page_count|' || count(*) FROM public.page;
SELECT 'image_count|' || count(*) FROM public.image;
SELECT 'marquee_count|' || count(*) FROM public.marquee;
SELECT 'unrelated_fragments_sha256_like|' || md5(coalesce(string_agg(md5(row_to_json(f)::text),'' ORDER BY f.id),''))
  FROM public.fragment f WHERE NOT (f.id = ANY(ARRAY[%s]::bigint[]));
SELECT 'page_rows_sha256_like|' || md5(coalesce(string_agg(md5(row_to_json(p)::text),'' ORDER BY p.id),'')) FROM public.page p;
SELECT 'image_rows_sha256_like|' || md5(coalesce(string_agg(md5(row_to_json(i)::text),'' ORDER BY i.id),'')) FROM public.image i;
SELECT 'marquee_rows_sha256_like|' || md5(coalesce(string_agg(md5(row_to_json(m)::text),'' ORDER BY m.id),'')) FROM public.marquee m;
''' % ids_string
    write(args.dir / 'unrelated-fingerprints.sql', sql)
    injection_sql = '''\\set ON_ERROR_STOP on
CREATE OR REPLACE FUNCTION public.migration0028_rehearsal_fail_insert() RETURNS trigger
LANGUAGE plpgsql AS $rehearsal$
BEGIN
 IF NEW.fragment_id = %d THEN
   RAISE EXCEPTION '0028_REHEARSAL_INJECTED_FAILURE';
 END IF;
 RETURN NEW;
END;
$rehearsal$;
CREATE TRIGGER migration0028_rehearsal_fail BEFORE INSERT ON public.migration0028_source
FOR EACH ROW EXECUTE FUNCTION public.migration0028_rehearsal_fail_insert();
''' % injection_id
    write(args.dir / 'inject-failure.sql', injection_sql)
    write(args.dir / 'remove-failure.sql', '''\\set ON_ERROR_STOP on
DROP TRIGGER IF EXISTS migration0028_rehearsal_fail ON public.migration0028_source;
DROP FUNCTION IF EXISTS public.migration0028_rehearsal_fail_insert();
''')
    info = {'schema': '0028-isolated-injection-v1', 'failureDate': failing_date,
            'failureFragment': injection_id, 'earlierCommittedExpected': earlier,
            'failedDateFragments': ids, 'totalConversions': 71}
    jsonwrite(args.dir / 'INJECTION-PARAMETERS.json', info)
    print('PASS: rollback/restart fixture prepared for date {} (fragment {})'.format(failing_date, injection_id))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command')
    one = sub.add_parser('config'); one.add_argument('--files-root', type=Path, required=True)
    one.add_argument('--port', type=int, required=True); one.add_argument('--output', type=Path, required=True)
    one.add_argument('--windows-root', required=True)
    two = sub.add_parser('approval'); two.add_argument('--plan', type=Path, required=True)
    two.add_argument('--output', type=Path, required=True); two.add_argument('--operator', required=True)
    three = sub.add_parser('fixtures'); three.add_argument('--plan', type=Path, required=True)
    three.add_argument('--dir', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'config': config(args)
    elif args.command == 'approval': make_approval(args)
    elif args.command == 'fixtures': generate(args)
    else: parser.error('Expected config, approval or fixtures')


if __name__ == '__main__':
    try: main()
    except Exception as exc:
        print('FAIL: rehearsal fixture: {}'.format(exc), file=sys.stderr)
        sys.exit(1)
