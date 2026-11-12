#!/usr/bin/env python3
"""0046: build a protected, encrypted inventory *copy* on mango. No Git actions.

Run via stdin from Windows Cygwin; keep this tool in the Diaries feature tools dir.
It never prints inventory values or decrypted data. Requires Ansible and PyYAML on mango.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import yaml
from yaml.nodes import MappingNode, ScalarNode, SequenceNode

# Source file/line/key frozen from 2026-11-11 20:24Z security triage.
# Jenkins credential *identifier* deliberately excluded.
SECRETS = {
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
EXPECTED_FILES = 44
EXPECTED_SECRET_FIELDS = 14


def fail(message):
    raise ValueError(message)


def scalar_positions(text, wanted):
    """Return exact source spans of scalar values, refusing ambiguous structures."""
    docs = list(yaml.compose_all(text))
    if len(docs) != 1 or not isinstance(docs[0], MappingNode):
        fail('Expected one YAML mapping')
    found = {}

    def visit(node):
        if isinstance(node, MappingNode):
            for key, value in node.value:
                if isinstance(key, ScalarNode) and isinstance(value, ScalarNode):
                    line = value.start_mark.line + 1
                    pair = (line, key.value)
                    if pair in wanted:
                        if pair in found:
                            fail('Duplicate candidate')
                        if value.start_mark.line != value.end_mark.line:
                            fail('Multiline candidate requires manual assessment')
                        if value.tag != 'tag:yaml.org,2002:str':
                            fail('Candidate is not a plaintext string')
                        if key.start_mark.line != value.start_mark.line:
                            fail('Candidate not on same line as key')
                        # An inline comment or other trailing token would be moved
                        # onto a ciphertext line by replacement; refuse silently
                        # changing Vault content or commentary.
                        tail = text[value.end_mark.index:text.find('\n', value.end_mark.index) if '\n' in text[value.end_mark.index:] else len(text)]
                        if tail.strip():
                            fail('Candidate has trailing material requiring manual review')
                        found[pair] = (value.start_mark.index, value.end_mark.index,
                                       key.start_mark.column, value.value)
                elif isinstance(value, (MappingNode, SequenceNode)):
                    visit(value)
        elif isinstance(node, SequenceNode):
            for value in node.value:
                visit(value)
    visit(docs[0])
    if set(found) != set(wanted):
        fail('Frozen secret field locations do not match source: refuse migration')
    return found


def vault_replace(text, targets, encrypt):
    spans = scalar_positions(text, set(targets))
    result = text
    for pair, (start, end, key_indent, original_value) in sorted(
            spans.items(), key=lambda item: item[1][0], reverse=True):
        ciphertext = encrypt(original_value)
        if not ciphertext.startswith('$ANSIBLE_VAULT;'):
            fail('Encryption did not produce an Ansible Vault payload')
        indent = ' ' * (key_indent + 2)
        block = '!vault |\n' + ''.join(indent + line + '\n'
                                      for line in ciphertext.rstrip('\n').splitlines())
        # Remove exactly one trailing newline, allowing existing EOL to survive.
        result = result[:start] + block[:-1] + result[end:]
    # Verify every transformed key is tagged !vault; no plaintext values in YAML nodes.
    docs = list(yaml.compose_all(result))
    tagged = []
    def walk(node):
        if isinstance(node, MappingNode):
            for k, v in node.value:
                if isinstance(k, ScalarNode) and isinstance(v, ScalarNode):
                    if k.value in {key for _, key in targets} and v.tag == '!vault':
                        tagged.append(k.value)
                walk(v)
        elif isinstance(node, SequenceNode):
            for v in node.value:
                walk(v)
    for d in docs:
        walk(d)
    if sorted(tagged) != sorted(key for _, key in targets):
        fail('Vault tag postcondition failed')
    return result


def self_test():
    text = 'password: "a # complex\\nstring"\npublic_id: abc\n'
    out = vault_replace(text, [(1, 'password')],
                        lambda s: '$ANSIBLE_VAULT;1.1;AES256\n123abc')
    assert 'password: !vault |\n  $ANSIBLE_VAULT;1.1;AES256\n  123abc\n' in out
    assert 'public_id: abc' in out
    try:
        vault_replace(text, [(2, 'password')], lambda _: '')
    except ValueError:
        pass
    else:
        fail('Fail-closed self-test did not reject drift')
    print('PASS: 0046 staging replacement self-test')


def inventory_bytes(path, playbook_dir, vault_pass):
    proc = subprocess.run([
        'ansible-inventory', '-i', str(path / 'hosts'),
        '--list', '--playbook-dir', str(playbook_dir),
        '--vault-password-file', str(vault_pass),
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode:
        fail('ansible-inventory failed; diagnostic suppressed to avoid leaking data')
    try:
        return json.loads(proc.stdout)
    except (ValueError, UnicodeDecodeError):
        fail('Invalid inventory JSON')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--source', type=Path, default=Path('/etc/ansible'))
    parser.add_argument('--dest', type=Path)
    parser.add_argument('--playbook-dir', type=Path, default=Path('/home/richard/playbooks'))
    parser.add_argument('--vault-password-file', type=Path,
                        default=Path('/home/richard/.vault_pass.txt'))
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    source = args.source.resolve()
    if args.dest is None:
        fail('--dest is required')
    dest = args.dest.absolute()
    if dest.exists() or dest.is_symlink():
        fail('Destination already exists: refusing overwrite')
    if not (source / 'hosts').is_file():
        fail('Inventory hosts source missing')
    if args.playbook_dir.resolve() == source:
        fail('Invalid playbook directory')
    if source in dest.parents or args.playbook_dir.resolve() in dest.parents:
        fail('Destination must not be inside live inventory or public Playbooks checkout')
    if dest.name != 'inventory' or dest.parent.name != 'ansible-controller':
        fail('Destination must be <parent>/ansible-controller/inventory')
    if not args.vault_password_file.is_file():
        fail('Vault password missing')
    if args.vault_password_file.stat().st_mode & 0o077:
        fail('Vault password file must not be group/world accessible')
    expected = [source / 'hosts'] + sorted(
        x for base in ('group_vars', 'host_vars')
        for x in (source / base).rglob('*') if x.is_file()
    )
    if len(expected) != EXPECTED_FILES:
        fail('File count changed since accepted security classification')
    if any(p.is_symlink() for p in expected):
        fail('Symbolic link in inventory source requires manual review')
    for path in expected:
        if any(p.is_symlink() for p in path.parents if p != source and source in p.parents):
            fail('Directory symlink requires manual review')

    # Build every encrypted replacement in process memory before writing any files.
    from ansible.parsing.vault import VaultLib, VaultSecret
    passphrase = args.vault_password_file.read_bytes().rstrip(b'\r\n')
    if not passphrase:
        fail('Empty Vault password')
    secret = VaultSecret(passphrase)
    vault = VaultLib([('default', secret)])
    def encrypt(value):
        return vault.encrypt(value.encode('utf-8'), secret=secret).decode('ascii')

    files = {}
    secret_count = 0
    for path in expected:
        relative = path.relative_to(source).as_posix()
        data = path.read_bytes()
        if relative in SECRETS:
            decoded = data.decode('utf-8')
            result = vault_replace(decoded, SECRETS[relative], encrypt)
            data = result.encode('utf-8')
            secret_count += len(SECRETS[relative])
        files[relative] = data
    if secret_count != EXPECTED_SECRET_FIELDS:
        fail('Wrong number of encrypted secret fields')

    os.umask(0o077)
    dest.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if dest.parent.is_symlink():
        fail('Controller parent cannot be a symbolic link')
    dest.mkdir(mode=0o700)
    for relative, data in files.items():
        path = dest / relative
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(data)
        path.chmod(0o600)

    # In trusted process only: full old/new effective variables without printing them.
    baseline = inventory_bytes(source, args.playbook_dir, args.vault_password_file)
    staged = inventory_bytes(dest, args.playbook_dir, args.vault_password_file)
    # Check exact loaded hostvars and group structure. Path-derived values are NOT ignored.
    if baseline != staged:
        print('REVIEW REQUIRED: effective inventory differs; destination left uncommitted',
              file=sys.stderr)
        print('Do not git add or publish until differences are explained', file=sys.stderr)
        sys.exit(2)
    print(f'PASS: {len(files)} files staged; {secret_count} credential scalars Vault-encrypted')
    print('PASS: full old/new effective inventory structures identical')
    print('No files committed or pushed; /etc/ansible and /home/richard/playbooks unchanged')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, UnicodeError, yaml.YAMLError) as exc:
        # PyYAML exceptions may include source snippets: never print exception text.
        print('FAIL: 0046 protected inventory preparation (' + type(exc).__name__ + ')', file=sys.stderr)
        sys.exit(1)
