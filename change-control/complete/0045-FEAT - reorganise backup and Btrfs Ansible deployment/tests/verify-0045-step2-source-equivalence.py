#!/usr/bin/env python3
"""0045: verify phased role tasks are semantically identical to frozen Step 1 source."""
import argparse
import hashlib
import json
from pathlib import Path
import yaml

EXPECTED = {'roles/snapshots/tasks/main.yaml': {'task_count': 24, 'canonical_sha256': '230fde42cf8ca1b4e78250911e8077782e6e996beac8842295642cf829abb11e', 'phases': ['validate.yaml', 'prerequisites.yaml', 'snapshot-roots.yaml', 'installed-files.yaml', 'state-and-config.yaml', 'systemd-units.yaml', 'preflight.yaml', 'activation.yaml']}, 'roles/btrfs-replication/tasks/native.yaml': {'task_count': 36, 'canonical_sha256': 'b8bddbc6b6af7652a4a9c214cbcf4e9b20d86d2c02e4cb51fc0b927b0ecf1bc1', 'phases': ['endpoint-setup.yaml', 'receiver-holds.yaml', 'receiver-config.yaml', 'retire-legacy-pull.yaml', 'source-scheduling.yaml', 'receiver-policy.yaml', 'simplified-runtime.yaml', 'receiver-retention.yaml', 'qgroup-deployment.yaml']}}
PHASE_NAMES = {name for meta in EXPECTED.values() for name in meta['phases']}

def load(path):
    return yaml.safe_load(path.read_text(encoding='utf-8'))

def flatten(task_file, seen=()):
    if task_file in seen:
        raise AssertionError('cyclic import: ' + str(task_file))
    result = []
    for task in load(task_file):
        if ('ansible.builtin.import_tasks' in task and
                task['ansible.builtin.import_tasks'] in PHASE_NAMES):
            # Expand only 0045-generated phases, not the original nested qgroup import.
            if set(task) != {'name', 'ansible.builtin.import_tasks'}:
                raise AssertionError('import adds task-level semantics: ' + task['name'])
            result.extend(flatten(task_file.parent / task['ansible.builtin.import_tasks'], seen+(task_file,)))
        else:
            result.append(task)
    return result

def sha(data):
    raw=json.dumps(data,sort_keys=True,ensure_ascii=False,separators=(',',':'))
    return hashlib.sha256(raw.encode()).hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--playbooks',type=Path,required=True)
    args=parser.parse_args()
    pb=args.playbooks.resolve()
    for rel,meta in EXPECTED.items():
        tasks=flatten(pb/rel)
        got=sha(tasks)
        assert len(tasks)==meta['task_count'], f'{rel}: wrong task count'
        assert got==meta['canonical_sha256'], f'{rel}: task semantics changed: {got}'
        assert sorted(f.name for f in (pb/rel).parent.glob('*.yaml') if f.name in meta['phases'])==sorted(meta['phases']), f'{rel}: missing phases'
        print(f'PASS {rel}: {len(tasks)} tasks, identical conditions/tags/order/args')
    native=load(pb/'btrfs-replication.yaml')
    assert native[0]['tasks'][0]['ansible.builtin.include_role']['tasks_from']=='native.yaml'
    assert load(pb/'backup-collection.yaml')[0]['roles'][0]['role']=='local-backup'
    assert 'backup-collection.yaml' in (pb/'scripts/backup-collection.sh').read_text()
    assert load(pb/'roles/btrfs-replication/tasks/main.yaml')[0]['ansible.builtin.include_role']['name']=='snapshots'
    print('PASS operator entrypoints and native-vs-generic role dispatch')
if __name__=='__main__':
    main()
