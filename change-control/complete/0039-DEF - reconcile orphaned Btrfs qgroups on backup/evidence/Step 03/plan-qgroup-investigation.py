#!/usr/bin/env python3
"""0039-DEF: OFFLINE read-only investigation plan; no deletion authorization.

Processes previously captured audit/identity/assessment files only.
Does not invoke shell, btrfs, remote commands or modify source evidence.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def validator_module():
    name = Path(__file__).with_name('validate-qgroup-manifest.py')
    if not name.is_file():
        raise RuntimeError('missing existing validator: validate-qgroup-manifest.py')
    spec = importlib.util.spec_from_file_location('qgroup_validator', name)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def plan(manifest, identity, assessment, host, uuid, sample_limit):
    validator = validator_module()
    try:
        proof = validator.validate(manifest, identity, host, uuid)
    except validator.ValidationError as exc:
        raise ValueError(f'inventory validation failed: {exc}') from exc
    def check(value, message):
        if not value:
            raise ValueError(message)
    check(type(assessment) is dict and assessment.get('schema') == 1 and
          assessment.get('result') == 'PASS' and
          assessment.get('assessment') == 'offline-observational-only' and
          assessment.get('deletion_authorized') is False and
          assessment.get('deletion_commands') == [], 'unsafe or invalid assessment')
    check(assessment.get('host') == host and assessment.get('filesystem') == proof['filesystem'] and
          assessment.get('uuid') == proof['uuid'] and
          assessment.get('source_fingerprint_sha256') == proof['fingerprint_sha256'] and
          assessment.get('qgroups') == proof['qgroups'], 'assessment/manifest identity mismatch')
    rows = manifest['manifest']['qgroups']
    active = {r['id'] for r in manifest['manifest']['active_subvolumes']}
    protected = assessment.get('protected_active_subvolume_ids')
    check(type(protected) is list and len(protected) > 0 and
          all(type(i) is int and i > 5 and i in active for i in protected) and
          len(set(protected)) == len(protected), 'invalid protected-ID attestation')
    qids = {r['id'] for r in rows}
    check(all('0/' + str(i) in qids for i in protected), 'protected active qgroup missing')
    dispositions = {'active': 'active-protected-snapshot', 'higher-level':'higher-level-excluded',
                    'pending-deletion':'pending-deletion-excluded', 'related-protected':'related-excluded',
                    'limited-protected':'limited-excluded', 'ambiguous':'ambiguous-excluded',
                    'unmatched-candidate':'unmatched-investigation-only'}
    counts = {}
    observed = []
    for row in rows:
        category = row['category']
        check(category in dispositions, 'unknown qgroup category')
        if category == 'active':
            disposition = ('active-protected-snapshot' if int(row['id'].split('/')[1]) in protected
                           else 'active-excluded')
        else:
            disposition = dispositions[category]
        counts[disposition] = counts.get(disposition, 0) + 1
        if disposition == 'unmatched-investigation-only':
            observed.append(row['id'])
    check(counts == assessment.get('counts'), 'assessment category counts mismatch')
    ordered = sorted(observed, key=lambda x: tuple(map(int, x.split('/'))))
    check(assessment.get('investigation_sample') == ordered[:20], 'assessment sample mismatch')
    check(1 <= sample_limit <= 100, 'sample limit must be 1..100')
    return {'schema': 1, 'purpose': 'offline-investigation-plan', 'host': host,
            'filesystem': proof['filesystem'], 'filesystem_uuid': proof['uuid'],
            'source_fingerprint_sha256': proof['fingerprint_sha256'],
            'assessment_sha256': hashlib.sha256(json.dumps(assessment, sort_keys=True,
                                   separators=(',', ':')).encode()).hexdigest(),
            'qgroup_count': len(rows), 'protected_active_subvolume_ids': sorted(protected),
            'counts': dict(sorted(counts.items())),
            'unmatched_unlimited_investigation_count': len(ordered),
            'review_sample': ordered[:sample_limit],
            'review_sample_truncated': len(ordered) > sample_limit,
            'deletion_authorized': False, 'deletion_commands': [], 'executable_actions': [],
            'next_gate': 'Independent live identity, receipts, holds and fingerprint revalidation; separate explicit approval required',
            'warning': 'Historical non-atomic evidence; NOT safe to execute on a filesystem'}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--identity', required=True)
    ap.add_argument('--assessment', required=True)
    ap.add_argument('--expected-host', choices=('backup', 'mars'), required=True)
    ap.add_argument('--expected-uuid', required=True)
    ap.add_argument('--sample-limit', type=int, default=20)
    args = ap.parse_args()
    try:
        inputs = [Path(x) for x in (args.manifest, args.identity, args.assessment)]
        if any(p.stat().st_size > 32 * 1024 * 1024 for p in inputs):
            raise ValueError('input too large')
        manifest = json.loads(inputs[0].read_text(encoding='utf-8'))
        identity = inputs[1].read_text(encoding='utf-8')
        assessment = json.loads(inputs[2].read_text(encoding='utf-8'))
        result = plan(manifest, identity, assessment, args.expected_host, args.expected_uuid, args.sample_limit)
    except (OSError, RuntimeError, ValueError, TypeError, KeyError, UnicodeError) as exc:
        print(f'PLAN UNAVAILABLE: {exc}', file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
