#!/usr/bin/env python3
"""0046-FEAT read-only inventory classification. Never prints variable values.

Run on mango from Windows Cygwin via:
ssh mango 'python3 - --root /etc/ansible --vault-password-file /home/richard/.vault_pass.txt' \
  < 'change-control/in-progress/0046-FEAT - move non-sensitive Ansible inventory into Playbooks Git/tools/audit-0046-inventory-readonly.py'

This is a conservative heuristic, NOT a proof that no plaintext credentials exist.
"""
import argparse
from collections import Counter
from pathlib import Path
import re
import subprocess
import sys

try:
    import yaml
    from yaml.nodes import MappingNode, SequenceNode, ScalarNode
except ImportError:
    print("FAIL: PyYAML is unavailable on this host")
    sys.exit(1)

WHOLE_VAULT = re.compile(r"^\$ANSIBLE_VAULT;1\.[12];AES256(?:;[^\r\n]*)?\s*(?:\r?\n|$)")
INLINE_VAULT = re.compile(r"^\$ANSIBLE_VAULT;1\.[12];AES256(?:;[^\r\n]*)?\s*(?:\r?\n|$)")
SENSITIVE_KEY = re.compile(
    r"(?:password|passwd|passphrase|private[_-]?key|secret|credential|token|"
    r"api[_-]?key|access[_-]?key|client[_-]?secret|auth[_-]?key|"
    r"become[_-]?pass|smtp[_-]?pass|db[_-]?pass|recovery[_-]?key)",
    re.IGNORECASE,
)
SENSITIVE_LITERAL = re.compile(
    r"-----BEGIN (?:OPENSSH |RSA |EC |DSA |ENCRYPTED )?PRIVATE KEY-----|"
    r"(?:https?|postgres(?:ql)?)://[^/@\s:]+:[^/@\s]+@",
    re.IGNORECASE,
)


def all_sources(root):
    paths = [root / 'hosts']
    for dn in ('group_vars', 'host_vars'):
        d = root / dn
        if not d.is_dir():
            raise RuntimeError(f'missing required directory: {d}')
        paths.extend(sorted(d.rglob('*')))
    return paths


def evaluate_yaml(path, content):
    """Return (encrypted scalar count, suspicious plaintext locations, malformed tags)."""
    encrypted = 0
    suspicious = []
    malformed = []
    try:
        documents = list(yaml.compose_all(content))
    except yaml.YAMLError as exc:
        raise RuntimeError(f'cannot parse YAML in {path.name}: {exc.__class__.__name__}') from None

    def traverse(node, parent_key=''):
        nonlocal encrypted
        if isinstance(node, MappingNode):
            for k, v in node.value:
                key = k.value if isinstance(k, ScalarNode) else '<complex-key>'
                traverse(v, str(key))
        elif isinstance(node, SequenceNode):
            for v in node.value:
                traverse(v, parent_key)
        elif isinstance(node, ScalarNode):
            value = node.value.strip()
            tagged = node.tag in ('!vault', 'tag:yaml.org,2002:vault')
            if tagged:
                if INLINE_VAULT.match(value):
                    encrypted += 1
                else:
                    malformed.append(node.start_mark.line + 1)
            elif value and value.lower() not in ('null', 'none', 'false', 'true', 'yes', 'no'):
                if SENSITIVE_KEY.search(parent_key) or SENSITIVE_LITERAL.search(value):
                    suspicious.append((node.start_mark.line + 1, parent_key))
    for doc in documents:
        if doc is not None:
            traverse(doc)
    return encrypted, suspicious, malformed



def inspect_ini_hosts(content):
    # Check variable assignments inside traditional INI inventory lines; do not emit values.
    flagged = []
    for lineno, line in enumerate(content.splitlines(), 1):
        entry = line.strip()
        if not entry or entry.startswith(('#', ';', '[')):
            continue
        for assignment in re.findall(r'(?<!\S)([^=\s]+)=([^\s]+)', entry):
            key, value = assignment
            if SENSITIVE_KEY.search(key) and value.strip():
                flagged.append((lineno, key))
        if SENSITIVE_LITERAL.search(entry):
            flagged.append((lineno, '<credential-bearing-URL-or-key>'))
    return flagged


def audit(root, vault_password_file, check_decrypt=True):
    counts = Counter()
    suspicious = []
    malformed = []
    errors = []
    files=[]
    for path in all_sources(root):
        if path.is_symlink():
            errors.append(f'symlink present; requires explicit scope review: {path.relative_to(root)}')
        elif path.is_file():
            files.append(path)
        elif path.is_dir():
            pass
        else:
            errors.append(f'unsupported file type: {path.relative_to(root)}')
    for file in sorted(files):
        rel = file.relative_to(root).as_posix()
        counts['files'] += 1
        try:
            content = file.read_text(encoding='utf-8')
        except (UnicodeError, OSError):
            errors.append(f'unreadable/non-text source: {rel}')
            continue
        if WHOLE_VAULT.match(content):
            counts['whole_file_vaults'] += 1
            if check_decrypt:
                cp = subprocess.run(
                    ['ansible-vault','view',str(file),'--vault-password-file',str(vault_password_file)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
                if cp.returncode:
                    errors.append(f'whole-file vault failed decryption: {rel}')
        elif rel == 'hosts':
            suspicious.extend((rel, line, key) for line, key in inspect_ini_hosts(content))
        elif file.suffix.lower() in ('.yml','.yaml'):
            try:
                n, flagged, invalid = evaluate_yaml(file, content)
            except RuntimeError as exc:
                errors.append(f'{rel}: {exc}')
                continue
            counts['inline_vault_values'] += n
            counts['files_with_inline_vault'] += bool(n)
            suspicious.extend((rel, line, key) for line,key in flagged)
            malformed.extend((rel, line) for line in invalid)
        elif rel != 'hosts':
            errors.append(f'non-YAML variable file requires manual review: {rel}')
    print('=== 0046 source classification (no variable values) ===')
    for key in ('files','whole_file_vaults','files_with_inline_vault','inline_vault_values'):
        print(f'{key}={counts[key]}')
    print(f'heuristic_plaintext_secret_candidates={len(suspicious)}')
    print(f'malformed_inline_vault_tags={len(malformed)}')
    print(f'errors={len(errors)}')
    # Key names only are printed, never field values. Redact opaque key names
    # to avoid accidentally echoing sensitive metadata into the evidence.
    for rel, line, _ in suspicious:
        print(f'REVIEW: potential unencrypted secret: {rel}:{line}')
    for rel, line in malformed:
        print(f'FAIL: malformed inline Vault tag: {rel}:{line}')
    for problem in errors:
        print('FAIL: '+problem)
    if malformed or errors:
        print('FAIL: inventory audit has validation failures')
        return 1
    if suspicious:
        print('REVIEW REQUIRED: candidate fields must be classified on mango before private Git staging')
        return 2
    print('PASS: no secret candidates found by heuristic; human review is still mandatory before Git staging')
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, default=Path('/etc/ansible'))
    ap.add_argument('--vault-password-file', type=Path, default=Path.home()/'.vault_pass.txt')
    ap.add_argument('--skip-decrypt', action='store_true', help='tests only')
    opts=ap.parse_args()
    if not opts.root.is_dir() or not (opts.root/'hosts').is_file():
        print('FAIL: inventory root/hosts missing')
        return 1
    if not opts.skip_decrypt and not opts.vault_password_file.is_file():
        print('FAIL: vault password file unavailable')
        return 1
    try:
        return audit(opts.root, opts.vault_password_file, not opts.skip_decrypt)
    except (OSError,RuntimeError) as exc:
        print(f'FAIL: {exc}')
        return 1

if __name__ == '__main__':
    sys.exit(main())
