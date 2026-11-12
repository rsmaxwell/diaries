#!/usr/bin/env python3
"""0046: verify existing protected inventory without changes or printing secrets.

Canonicalizes the known Ansible inventory JSON vault wrapper *only* at the
14 frozen protected keys; compares all other resolved values strictly.
Checks all 44 file bytes/structures, including 14 ciphertext roundtrips.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

import yaml
from yaml.nodes import MappingNode, ScalarNode, SequenceNode

PROTECTED = {
    'host_vars/acorn-bootstrap.yaml': [(7, 'another_user_password')],
    'host_vars/acorn.yaml': [(109, 'diaries_cloudflare_tunnel_token')],
    'host_vars/backup-bootstrap/backup-bootstrap.yaml': [(7, 'another_user_password')],
    'host_vars/bob-bootstrap.yaml': [(7, 'another_user_password')],
    'host_vars/boris.yaml': [(13, 'hello_password')],
    'host_vars/grape-bootstrap.yaml': [(7, 'another_user_password')],
    'host_vars/grape.yaml': [(8, 'cloudflare_tunnel_token')],
    'host_vars/major.yaml': [(10, 'jenkins_password'), (15, 'deploy_password')],
    'host_vars/mars-bootstrap/mars-bootstrap.yaml': [(7, 'another_user_password')],
    'host_vars/pluto-bootstrap/pluto-bootstrap.yaml': [(7, 'another_user_password')],
    'host_vars/snowy-bootstrap.yaml': [(7, 'another_user_password')],
    'host_vars/tintin.yaml': [(9, 'jenkins_admin_password'), (11, 'jenkins_user_password')],
}
EXPECTED_FILE_COUNT = 44
EXPECTED_VAULT_VALUES = 14
EXPECTED_ACTIVE_VAULT_VALUES = 8
YAML_STRING = 'tag:yaml.org,2002:str'


def fail(msg):
    raise ValueError(msg)


def safe_path(parts):
    return '.'.join(x if re.fullmatch(r'[A-Za-z0-9_-]{1,80}', str(x))
                    else '[nonstandard]' for x in parts)


def inventory_files(root):
    if not root.is_dir() or root.is_symlink() or not (root/'hosts').is_file():
        fail('Inventory root/hosts missing or unsafe')
    files = {'hosts': root/'hosts'}
    for name in ('group_vars', 'host_vars'):
        directory = root/name
        if not directory.is_dir() or directory.is_symlink():
            fail('Inventory variables directory invalid')
        for path in directory.rglob('*'):
            if path.is_symlink():
                fail('Symlink in inventory requires review')
            if path.is_file():
                files[path.relative_to(root).as_posix()] = path
    if len(files) != EXPECTED_FILE_COUNT:
        fail('File count differs from frozen 0046 baseline')
    return files


def compare_yaml(a, b, targets, vault, counts):
    """Structural YAML equivalence, allowing precisely the frozen vault edits."""
    if type(a) is not type(b):
        fail('YAML node types differ unexpectedly')
    if isinstance(a, ScalarNode):
        if targets is not None:
            if a.tag != YAML_STRING or b.tag != '!vault':
                fail('Expected plaintext-to-Vault scalar conversion missing')
            if not b.value.startswith('$ANSIBLE_VAULT;'):
                fail('Vault ciphertext header missing')
            try:
                plaintext = vault.decrypt(b.value.encode('ascii')).decode('utf-8')
            except Exception:
                fail('Unable to decrypt protected scalar')
            if plaintext != a.value:
                fail('Protected scalar plaintext changed')
            counts['protected'] += 1
        elif a.tag != b.tag or a.value != b.value:
            fail('Unrelated YAML scalar changed')
    elif isinstance(a, SequenceNode):
        if a.tag != b.tag or len(a.value) != len(b.value):
            fail('YAML sequence changed')
        for old, new in zip(a.value,b.value):
            compare_yaml(old,new,None,vault,counts)
    elif isinstance(a, MappingNode):
        if a.tag != b.tag or len(a.value) != len(b.value):
            fail('YAML mapping changed')
        for (ak,av),(bk,bv) in zip(a.value,b.value):
            compare_yaml(ak,bk,None,vault,counts)
            if not isinstance(ak,ScalarNode):
                fail('Non-scalar YAML mapping key requires review')
            key = (av.start_mark.line + 1, ak.value)
            if targets is not None and key in targets:
                if key in counts['seen']:
                    fail('Duplicate protected scalar key')
                counts['seen'].add(key)
                compare_yaml(av,bv,key,vault,counts)
            else:
                compare_yaml(av,bv,None,vault,counts)
    else:
        fail('Unsupported YAML structure')


def validate_files(src, dst, vault):
    a = inventory_files(src)
    b = inventory_files(dst)
    if set(a) != set(b):
        fail('Inventory file names differ')
    changed = {rel for rel in a if a[rel].read_bytes() != b[rel].read_bytes()}
    if changed != set(PROTECTED):
        fail('Changed files differ from the 12 frozen Vault-conversion paths')
    protected_count = 0
    for rel, pairs in PROTECTED.items():
        old = list(yaml.compose_all(a[rel].read_text(encoding='utf-8')))
        new = list(yaml.compose_all(b[rel].read_text(encoding='utf-8')))
        if len(old)!=1 or len(new)!=1:
            fail('Ambiguous YAML document count')
        counts={'seen':set(),'protected':0}
        compare_yaml(old[0],new[0],set(pairs),vault,counts)
        if counts['seen'] != set(pairs):
            fail('Expected protected field not found at frozen source location')
        protected_count += counts['protected']
    if protected_count != EXPECTED_VAULT_VALUES:
        fail('Wrong number of protected scalar conversions')
    print('PASS: 44 file paths identical; only 12 expected files changed')
    print('PASS: 14 protected scalars decrypt identically; all other YAML nodes identical')


def inventory_json(root, playbook_dir, vault_pass):
    proc = subprocess.run([
        'ansible-inventory', '-i', str(root/'hosts'), '--list',
        '--playbook-dir', str(playbook_dir),
        '--vault-password-file', str(vault_pass),
    ], stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    if proc.returncode:
        fail('Ansible inventory resolution failed (diagnostics suppressed)')
    try:
        data = json.loads(proc.stdout)
    except (UnicodeDecodeError,ValueError):
        fail('Inventory did not return valid JSON')
    if not isinstance(data,dict):
        fail('Invalid inventory JSON top-level type')
    return data


def frozen_active_paths():
    paths=set()
    for rel,pairs in PROTECTED.items():
        parts=Path(rel).parts
        host = parts[1] if len(parts)>=3 else Path(parts[1]).stem
        for _,key in pairs:
            paths.add(('_meta','hostvars',host,key))
    return paths


def compare_inventory(a,b,vault):
    allowed = frozen_active_paths()
    converted=[]
    diffs=[]

    def compare(x,y,parts=()):
        if parts in allowed and isinstance(y,dict) and set(y)=={'__ansible_vault'}:
            ct=y['__ansible_vault']
            if not isinstance(x,str) or not isinstance(ct,str) or not ct.startswith('$ANSIBLE_VAULT;'):
                diffs.append((parts,'BAD_VAULT_WRAPPER'))
                return
            try:
                actual=vault.decrypt(ct.encode('ascii')).decode('utf-8')
            except Exception:
                diffs.append((parts,'DECRYPT_FAILED'))
                return
            if actual != x:
                diffs.append((parts,'PLAINTEXT_MISMATCH'))
                return
            converted.append(parts)
            return
        if type(x)!=type(y):
            diffs.append((parts,'TYPE_DIFF'))
        elif isinstance(x,dict):
            for k in sorted(set(x)|set(y),key=str):
                p=parts+(str(k),)
                if k not in x:
                    diffs.append((p,'EXTRA_KEY'))
                elif k not in y:
                    diffs.append((p,'MISSING_KEY'))
                else:
                    compare(x[k],y[k],p)
        elif isinstance(x,list):
            if len(x)!=len(y):
                diffs.append((parts,'LENGTH_DIFF'))
            else:
                for i,(i1,i2) in enumerate(zip(x,y)):
                    compare(i1,i2,parts+(str(i),))
        elif x!=y:
            diffs.append((parts,'VALUE_DIFF'))

    compare(a,b)
    for path,typ in diffs[:30]:
        print('REVIEW:',safe_path(path),typ)
    if len(diffs)>30:
        print('REVIEW: more unexpected differences omitted')
    print(f'Inventory normalization: expected_active={EXPECTED_ACTIVE_VAULT_VALUES}, '
          f'verified_vault_wrappers={len(converted)}, unexpected_differences={len(diffs)}')
    if len(set(converted))!=EXPECTED_ACTIVE_VAULT_VALUES or diffs:
        fail('Effective inventory differs after strict Vault normalization')
    print('PASS: active inventory groups and all other hostvars identical')
    print(f'PASS: {len(converted)} active hostvars match after in-memory Vault decryption')


def self_test():
    class FakeVault:
        def decrypt(self,raw):
            if raw.strip()==b'$ANSIBLE_VAULT;fake':
                return b'test-secret'
            raise ValueError('bad cipher')
    allowed=frozen_active_paths()
    assert ('_meta','hostvars','acorn','diaries_cloudflare_tunnel_token') in allowed
    a={'_meta':{'hostvars':{'acorn':{'diaries_cloudflare_tunnel_token':'test-secret',
                                  'ordinary':'value'}}},'x':1}
    b={'_meta':{'hostvars':{'acorn':{'diaries_cloudflare_tunnel_token':
                                  {'__ansible_vault':'$ANSIBLE_VAULT;fake'},
                                  'ordinary':'value'}}},'x':1}
    global EXPECTED_ACTIVE_VAULT_VALUES
    saved=EXPECTED_ACTIVE_VAULT_VALUES
    EXPECTED_ACTIVE_VAULT_VALUES=1
    try:
        compare_inventory(a,b,FakeVault())
        b['x']=2
        try:
            compare_inventory(a,b,FakeVault())
        except ValueError:
            pass
        else:
            fail('Self-test did not reject unrelated variable change')
        b['x']=1
        b['_meta']['hostvars']['acorn']['diaries_cloudflare_tunnel_token']['__ansible_vault']='tampered'
        try:
            compare_inventory(a,b,FakeVault())
        except ValueError:
            pass
        else:
            fail('Self-test did not reject invalid Vault wrapper')
    finally:
        EXPECTED_ACTIVE_VAULT_VALUES=saved
    # Test YAML node-level conversion and unexpected changes.
    original=yaml.compose('password: "test-secret"\nordinary: value\n')
    prepared=yaml.compose('password: !vault |\n  $ANSIBLE_VAULT;fake\nordinary: value\n')
    counts={'seen':set(),'protected':0}
    compare_yaml(original,prepared,{(1,'password')},FakeVault(),counts)
    assert counts['protected']==1 and counts['seen']=={(1,'password')}
    print('PASS: 0046 semantic comparator synthetic tests')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--self-test',action='store_true')
    p.add_argument('--source',type=Path,default=Path('/etc/ansible'))
    p.add_argument('--dest',type=Path,default=Path('/home/richard/ansible-controller/inventory'))
    p.add_argument('--playbook-dir',type=Path,default=Path('/home/richard/playbooks'))
    p.add_argument('--vault-password-file',type=Path,default=Path('/home/richard/.vault_pass.txt'))
    args=p.parse_args()
    if args.self_test:
        self_test();return
    source=args.source.absolute()
    dest=args.dest.absolute()
    if source==dest or source in dest.parents or dest in source.parents:
        fail('Source and destination inventory roots overlap')
    if not args.playbook_dir.is_dir() or not args.vault_password_file.is_file():
        fail('Playbook checkout or Vault password file missing')
    if args.vault_password_file.stat().st_mode & 0o077:
        fail('Vault password file must not be group/world-readable')
    from ansible.parsing.vault import VaultLib,VaultSecret
    secret=VaultSecret(args.vault_password_file.read_bytes().rstrip(b'\r\n'))
    vault=VaultLib([('default',secret)])
    print('=== 0046 read-only protected-inventory semantic verification ===')
    validate_files(source,dest,vault)
    baseline=inventory_json(source,args.playbook_dir,args.vault_password_file)
    prepared=inventory_json(dest,args.playbook_dir,args.vault_password_file)
    compare_inventory(baseline,prepared,vault)
    print('PASS: 0046 prepared inventory equivalent; no files changed, committed or pushed')

if __name__=='__main__':
    try:
        main()
    except Exception as exc:
        # Never expose exception strings (PyYAML, Ansible, and subprocesses may contain secrets).
        print('FAIL: 0046 semantic verification ('+type(exc).__name__+')',file=sys.stderr)
        sys.exit(1)
