#!/usr/bin/env python3
"""Source-only Step 12.3 authority-storage contract; no host mutations."""
from pathlib import Path
import yaml
source=Path(__file__).resolve().parents[1] / 'tasks' / 'native.yaml'
tasks=yaml.safe_load(source.read_text(encoding='utf-8'))
related=[t for t in tasks if 'native-btrfs-prune-authority' in t.get('tags',[])]
assert len(related)==3, 'expected stat, assert, file tasks'
stat, guard, provision=related
paths=['/etc/btrfs-receiver-prune','/var/lib/btrfs-receiver-prune','/var/lib/btrfs-receiver-prune/consumed']
assert stat['ansible.builtin.stat']['follow'] is False
assert stat['loop']==paths
assert 'receiver' in stat['when']
assert guard['loop'].startswith('{{ btrfs_receiver_prune_authority_preflight')
assert 'item.stat.exists | default(false)' in guard['when']
for key in ('item.stat.isdir | default(false)', 'not (item.stat.islnk | default(false))', "item.stat.pw_name == 'root'", "item.stat.gr_name == 'root'", "item.stat.mode == '0700'"):
    assert key in guard['ansible.builtin.assert']['that'],key
assert provision['loop']==paths
assert provision['ansible.builtin.file']['state']=='directory'
assert provision['ansible.builtin.file']['mode']=='0700'
assert provision['ansible.builtin.file']['owner']=='root'
assert provision['ansible.builtin.file']['group']=='root'
assert provision['ansible.builtin.file']['follow'] is False
assert 'receiver' in provision['when']
assert all('native-btrfs-prune-authority' in x['tags'] for x in related)
assert not any('sudoers' in str(t).lower() or 'delete-receiver' in str(t) for t in related)
print('PASS: root-only paths, fail-closed existing-directory checks, receiver-only tag')
print('PASS: no approval file, sudoers grant or deletion operation introduced')
