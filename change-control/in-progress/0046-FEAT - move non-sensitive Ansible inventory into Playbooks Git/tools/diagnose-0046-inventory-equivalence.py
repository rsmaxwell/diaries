#!/usr/bin/env python3
"""0046: read-only, value-suppressing diagnostic of prepared inventory mismatch.

Runs on mango by stdin from Windows; no Git, files, Ansible config or inventory changes.
It does not display inventory values, encrypted blobs or password content.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess
import sys

# Locations frozen by accepted 0046 secret classification. Used only for paths.
PROTECTED_FIELDS = {
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


def fail(message):
    raise ValueError(message)


def check_path(root, kind):
    if not root.is_dir() or root.is_symlink() or not (root / 'hosts').is_file():
        fail(f'{kind} inventory missing or unsafe')
    for name in ('group_vars', 'host_vars'):
        if not (root / name).is_dir() or (root / name).is_symlink():
            fail(f'{kind} {name} missing or symlinked')


def inventory(root, playbook_dir, vault_pass):
    result = subprocess.run(
        ['ansible-inventory', '-i', str(root/'hosts'), '--list',
         '--playbook-dir', str(playbook_dir),
         '--vault-password-file', str(vault_pass)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        fail('ansible-inventory failed; stderr suppressed (may contain secrets)')
    try:
        obj = json.loads(result.stdout)
    except (ValueError, UnicodeDecodeError):
        fail('ansible-inventory returned non-JSON data')
    if not isinstance(obj, dict):
        fail('ansible-inventory JSON not a mapping')
    return obj


def compare(a, b, parts=(), limit=2000, out=None):
    if out is None:
        out = []
    if len(out) >= limit:
        return out
    if type(a) != type(b):
        out.append((parts, 'TYPE_DIFF'))
    elif isinstance(a, dict):
        for key in sorted(set(a) | set(b), key=str):
            if len(out) >= limit:
                break
            p = parts + (str(key),)
            if key not in a:
                out.append((p, 'NEW_KEY'))
            elif key not in b:
                out.append((p, 'MISSING_KEY'))
            else:
                compare(a[key], b[key], p, limit, out)
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append((parts, 'LIST_LENGTH_DIFF'))
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                if len(out) >= limit:
                    break
                compare(x, y, parts + (str(i),), limit, out)
    elif a != b:
        out.append((parts, 'VALUE_DIFF'))
    return out


def safe_path(parts):
    return '.'.join(p if re.fullmatch(r'[A-Za-z0-9_-]{1,80}', p) else '[nonstandard-key]'
                    for p in parts)


def compare_source_files(src, dst):
    src_files = {}
    dst_files = {}
    for root, collected in ((src, src_files), (dst, dst_files)):
        for rel in ('hosts',):
            collected[rel] = (root / rel).read_bytes()
        for dirname in ('group_vars','host_vars'):
            for path in (root/dirname).rglob('*'):
                if path.is_symlink():
                    fail('Inventory symlink requires review')
                if path.is_file():
                    collected[path.relative_to(root).as_posix()] = path.read_bytes()
    if set(src_files) != set(dst_files):
        print('FILES: source and prepared inventory file sets differ')
        return False
    changed = set()
    for key in src_files:
        if src_files[key] != dst_files[key]:
            changed.add(key)
    expected = set(PROTECTED_FIELDS)
    print(f'FILES: source={len(src_files)} prepared={len(dst_files)} modified={len(changed)} expected_modified={len(expected)}')
    if changed != expected:
        print('FILES: unexpected modified or unmodified path(s), review required')
        for key in sorted(changed ^ expected)[:40]:
            print('  FILE_REVIEW:',safe_path(tuple(key.split('/'))))
        return False
    print('PASS: file changes restricted to the 12 expected Vault-conversion files')
    return True


def compare_encryption_roundtrips(source, dest, vault_pass):
    # Parse as YAML syntax nodes so original plaintext and Vault ciphertext are not printed.
    from ansible.parsing.vault import VaultLib, VaultSecret
    from yaml.nodes import MappingNode, ScalarNode, SequenceNode
    import yaml
    secret = VaultSecret(vault_pass.read_bytes().rstrip(b'\r\n'))
    vault = VaultLib([('default', secret)])

    def extract(path, key):
        docs = list(yaml.compose_all(path.read_text(encoding='utf-8')))
        if len(docs) != 1 or not isinstance(docs[0], MappingNode):
            fail('Expected a single YAML mapping')
        hits=[]
        def visit(node):
            if isinstance(node, MappingNode):
                for k,v in node.value:
                    if isinstance(k, ScalarNode) and k.value == key and isinstance(v, ScalarNode):
                        hits.append(v)
                    visit(v)
            elif isinstance(node, SequenceNode):
                for v in node.value:
                    visit(v)
        visit(docs[0])
        if len(hits)!=1:
            fail('Missing or ambiguous protected key')
        return hits[0]

    passed=0
    failed=[]
    for rel, pairs in PROTECTED_FIELDS.items():
        for _line,key in pairs:
            original=extract(source/rel,key)
            new=extract(dest/rel,key)
            if original.tag != 'tag:yaml.org,2002:str' or new.tag != '!vault':
                failed.append((rel,key,'TAG'))
                continue
            try:
                decrypted=vault.decrypt(new.value.encode('ascii')).decode('utf-8')
            except Exception:
                failed.append((rel,key,'DECRYPT'))
                continue
            if decrypted != original.value:
                failed.append((rel,key,'PLAINTEXT_MISMATCH'))
            else:
                passed += 1
    print(f'VAULT ROUNDTRIP: match={passed}, mismatch={len(failed)}')
    for rel,key,category in failed:
        print('  VAULT_REVIEW:',safe_path(tuple(rel.split('/'))),key,category)
    if passed==14 and not failed:
        print('PASS: all 14 Vault-protected values decrypt to the original values')
    return bool(passed==14 and not failed)


def self_test():
    a = {'_meta': {'hostvars': {'mars': {'x': 'old', 'secret': 123}}},
         'local_backup': {'hosts': ['mars']}}
    b = {'_meta': {'hostvars': {'mars': {'x': 'new', 'secret': 123}}},
         'local_backup': {'hosts': ['mars']}}
    out = compare(a,b)
    assert out == [(('_meta','hostvars','mars','x'), 'VALUE_DIFF')],out
    assert safe_path(('bad space','host_vars','foo')) == '[nonstandard-key].host_vars.foo'
    assert not compare(a,a)
    print('PASS: 0046 diagnostic synthetic tests')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--source', type=Path, default=Path('/etc/ansible'))
    parser.add_argument('--dest', type=Path, default=Path('/home/richard/ansible-controller/inventory'))
    parser.add_argument('--playbook-dir', type=Path, default=Path('/home/richard/playbooks'))
    parser.add_argument('--vault-password-file', type=Path,default=Path('/home/richard/.vault_pass.txt'))
    args=parser.parse_args()
    if args.self_test:
        self_test();return
    source=args.source.resolve()
    dest=args.dest.absolute()
    check_path(source,'Original')
    check_path(dest,'Prepared')
    if source == dest or source in dest.parents or dest in source.parents:
        fail('Overlapping inventory directories')
    if not args.playbook_dir.is_dir() or not args.vault_password_file.is_file():
        fail('Playbooks directory or Vault password file missing')
    if args.vault_password_file.stat().st_mode & 0o077:
        fail('Vault password is group/world accessible')
    print('=== 0046 read-only comparison; no variables or secrets displayed ===')
    file_ok=compare_source_files(source,dest)
    vault_ok=compare_encryption_roundtrips(source,dest,args.vault_password_file)
    original=inventory(source,args.playbook_dir,args.vault_password_file)
    prepared=inventory(dest,args.playbook_dir,args.vault_password_file)
    diffs=compare(original,prepared)
    print('=== Resolved inventory diff (key paths and category only) ===')
    print('difference_count=' + str(len(diffs)) + (' (truncated at 2000)' if len(diffs)==2000 else ''))
    for category,count in sorted(Counter(category for _,category in diffs).items()):
        print('TYPE:',category,'count='+str(count))
    for path,category in diffs[:45]:
        print('DIFF:',safe_path(path),category)
    if len(diffs)>45:
        print(f'... {len(diffs)-45} additional differences omitted')
    if file_ok and vault_ok and not diffs:
        print('PASS: full inventory equivalence verified')
        return
    print('REVIEW REQUIRED: mismatch isolated; no source or destination changes made')
    sys.exit(2)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        # Never emit exception strings: YAML/Python errors can contain inventory data.
        print('FAIL: 0046 comparison diagnostic (' + type(exc).__name__ + ')',file=sys.stderr)
        sys.exit(1)
