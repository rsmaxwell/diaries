#!/usr/bin/env python3
"""0039-DEF offline planner adversarial regression; evidence is strictly read-only.

Run from any working directory: python3 test-plan-qgroup-investigation.py
Uses only Python standard library. All tampering occurs within TemporaryDirectory.
"""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

STEP = Path(__file__).resolve().parent
PLANNER = STEP / 'plan-qgroup-investigation.py'
UUIDS = {'backup': 'b915f967-7cb4-4c14-b11b-f52209637a22',
         'mars': '72d1d8ea-900e-4fca-837f-1b1febec036c'}
COUNTS = {'backup': (29571, 15475, 13962, 3), 'mars': (191, 21, 24, 6)}


def sources(host):
    return (STEP / 'inventory' / host / 'qgroup-manifest.json',
            STEP / 'inventory' / host / 'filesystem-identity.txt',
            STEP / 'assessment' / (host + '-qgroup-safety.json'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def invoke(host, paths):
    return subprocess.run([sys.executable, str(PLANNER), '--manifest', str(paths[0]),
                           '--identity', str(paths[1]), '--assessment', str(paths[2]),
                           '--expected-host', host, '--expected-uuid', UUIDS[host],
                           '--sample-limit', '10'], capture_output=True, text=True,
                          check=False, timeout=90)


def assert_rejected(label, host, inputs, output_dir, mutator):
    paths = [output_dir / ('input-%d' % n + ('.txt' if n == 1 else '.json'))
             for n in range(3)]
    for source, target in zip(inputs, paths):
        target.write_bytes(source.read_bytes())
    mutator(paths)
    run = invoke(host, paths)
    if run.returncode == 0:
        raise AssertionError(label + ': unsafe ACCEPTANCE of tampered evidence')
    if run.returncode != 2 or 'PLAN UNAVAILABLE:' not in run.stderr:
        raise AssertionError(label + ': unexpected rejection mode: ' + repr((run.returncode, run.stderr[:300])))
    if run.stdout.strip():
        raise AssertionError(label + ': rejected input emitted a plan')
    print('PASS:', label, '=>', run.stderr.strip()[:180])


def change_json(index, action):
    def mutation(paths):
        obj = json.loads(paths[index].read_text(encoding='utf-8'))
        action(obj)
        paths[index].write_text(json.dumps(obj, indent=2) + '\n', encoding='utf-8')
    return mutation


def remove_field(index, field):
    return change_json(index, lambda obj: obj.pop(field))


def main():
    all_inputs = [path for host in UUIDS for path in sources(host)]
    for path in [PLANNER, STEP / 'validate-qgroup-manifest.py', *all_inputs]:
        if not path.is_file():
            raise AssertionError('required evidence/code missing: ' + str(path))
    original_hashes = {path: digest(path) for path in all_inputs}
    try:
        for host in ('backup', 'mars'):
            inputs = sources(host)
            good = invoke(host, inputs)
            if good.returncode != 0:
                raise AssertionError(host + ' valid baseline rejected: ' + good.stderr[:500])
            plan = json.loads(good.stdout)
            total, candidates, limited, protected = COUNTS[host]
            if (plan['qgroup_count'] != total or
                plan['unmatched_unlimited_investigation_count'] != candidates or
                plan['counts']['limited-excluded'] != limited or
                plan['counts']['active-protected-snapshot'] != protected or
                len(plan['review_sample']) != 10 or
                plan['deletion_authorized'] is not False or
                plan['deletion_commands'] != [] or
                plan['executable_actions'] != []):
                raise AssertionError(host + ': unsafe or inconsistent valid plan')
            print('PASS:', host, 'valid full-size baseline / no deletion authorization')
        backup = sources('backup')
        with tempfile.TemporaryDirectory(prefix='0039-qgroup-adversarial-') as temp:
            directory = Path(temp)
            tests = [
                ('manifest-fingerprint / altered category', 0,
                 change_json(0, lambda x: x['manifest']['qgroups'][0].update(category='unmatched-candidate'))),
                ('assessment classification counts', 0,
                 change_json(2, lambda x: x['counts'].update({'limited-excluded': 1}))),
                ('removed protected snapshot IDs', 0,
                 change_json(2, lambda x: x.update(protected_active_subvolume_ids=[]))),
                ('removed one protected snapshot ID', 0,
                 change_json(2, lambda x: x['protected_active_subvolume_ids'].pop())),
                ('deletion authorized flag', 0,
                 change_json(2, lambda x: x.update(deletion_authorized=True))),
                ('injected deletion command', 0,
                 change_json(2, lambda x: x.update(deletion_commands=['btrfs qgroup destroy 0/123 /']))),
                ('assessment fingerprint mismatch', 0,
                 change_json(2, lambda x: x.update(source_fingerprint_sha256='0'*64))),
                ('assessment sample tampering', 0,
                 change_json(2, lambda x: x.update(investigation_sample=[]))),
                ('missing assessment counts', 0, remove_field(2, 'counts')),
                ('missing manifest', 0, change_json(0, lambda x: x.pop('manifest'))),
                ('invalid JSON', 0, lambda paths: paths[2].write_text('{invalid json', encoding='utf-8')),
                ('identity tampering', 0, lambda paths: paths[1].write_text('tampered identity\n', encoding='utf-8')),
            ]
            for idx, (label, _, mutation) in enumerate(tests):
                case = directory / ('case-%02d' % idx)
                case.mkdir()
                assert_rejected(label, 'backup', backup, case, mutation)
        print('PASS: 12 adversarial cases rejected')
    finally:
        changed = [str(path) for path, before in original_hashes.items() if digest(path) != before]
        if changed:
            raise AssertionError('SOURCE EVIDENCE MODIFIED: ' + ', '.join(changed))
        print('PASS: original input evidence SHA256 unchanged')
    print('=== ALL OFFLINE ADVERSARIAL REGRESSIONS PASSED ===')


if __name__ == '__main__':
    try:
        main()
    except (AssertionError, OSError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
        print('REGRESSION FAILED:', error, file=sys.stderr)
        sys.exit(1)
