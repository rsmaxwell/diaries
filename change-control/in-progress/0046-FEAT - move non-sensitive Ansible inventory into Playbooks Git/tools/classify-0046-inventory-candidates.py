#!/usr/bin/env python3
"""0046-FEAT: read-only, no-values classification of possible plaintext secrets.

Run by streaming this script to Python on mango; the inventory never leaves mango.
The output deliberately includes ONLY relative filenames, line numbers, classes,
and counts. Never log YAML values, decrypted Vault data, or exceptions containing
source snippets. This is a heuristic, not a proof of absence of secrets.
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import re
import sys
import tempfile

try:
    import yaml
    from yaml.nodes import MappingNode, ScalarNode, SequenceNode
except ImportError:
    print("FAIL: PyYAML is missing")
    sys.exit(1)

# Match the prior 0046 audit's candidate detection to make the results comparable.
SENSITIVE_KEY = re.compile(
    r"(?:password|passwd|passphrase|private[_-]?key|secret|credential|token|"
    r"api[_-]?key|access[_-]?key|client[_-]?secret|auth[_-]?key|"
    r"become[_-]?pass|smtp[_-]?pass|db[_-]?pass|recovery[_-]?key)", re.I
)
SENSITIVE_LITERAL = re.compile(
    r"-----BEGIN (?:OPENSSH |RSA |EC |DSA |ENCRYPTED )?PRIVATE KEY-----|"
    r"(?:https?|postgres(?:ql)?)://[^/@\s:]+:[^/@\s]+@", re.I
)
WHOLE_VAULT = re.compile(r"^\$ANSIBLE_VAULT;1\.[12];AES256(?:;[^\r\n]*)?\s*(?:\r?\n|$)")
VAULT_VALUE = re.compile(r"^\$ANSIBLE_VAULT;1\.[12];AES256(?:;[^\r\n]*)?\s*(?:\r?\n|$)")
PURE_VARIABLE_REFERENCE = re.compile(
    r"^\{\{\s*[A-Za-z_]\w*(?:\.[A-Za-z_]\w*|\[['\"][A-Za-z_]\w*['\"]\])*\s*\}\}$"
)
SSH_PUBLIC_KEY = re.compile(r"^(?:ssh-ed25519|ssh-rsa|ecdsa-sha2-[A-Za-z0-9-]+) [A-Za-z0-9+/]+={0,2}(?:\s+[^\r\n]*)?$")
BARE_PATH = re.compile(r"^/(?:[^\s:@/]+/)*[^\s:@/]+$")


def classify(value: str) -> str:
    """Classify syntactic shape only. Never return the value itself."""
    if SENSITIVE_LITERAL.search(value):
        return "HIGH_RISK_LITERAL_OR_CREDENTIAL_URL"
    if PURE_VARIABLE_REFERENCE.fullmatch(value):
        return "REFERENCE_ONLY"
    if SSH_PUBLIC_KEY.fullmatch(value):
        return "PUBLIC_KEY_FORMAT"
    if BARE_PATH.fullmatch(value):
        return "PATH_REFERENCE_REVIEW"
    if '{{' in value or '{%' in value or '${' in value:
        return "COMPOSITE_OR_COMPLEX_TEMPLATE_REVIEW"
    return "PLAINTEXT_LITERAL_REVIEW"


def yaml_candidates(content: str):
    """Yield (line, class) while preserving prior audit's matching semantics."""
    out = []
    try:
        docs = list(yaml.compose_all(content))
    except yaml.YAMLError:
        raise ValueError("invalid YAML") from None

    def visit(node, parent_key=''):
        if isinstance(node, MappingNode):
            for key, value in node.value:
                k = key.value if isinstance(key, ScalarNode) else '<complex-key>'
                visit(value, str(k))
        elif isinstance(node, SequenceNode):
            for value in node.value:
                visit(value, parent_key)
        elif isinstance(node, ScalarNode):
            value = node.value.strip()
            tagged = node.tag in ('!vault', 'tag:yaml.org,2002:vault')
            if tagged:
                if not VAULT_VALUE.match(value):
                    raise ValueError("malformed inline vault")
            elif value and value.lower() not in ('null','none','false','true','yes','no'):
                if SENSITIVE_KEY.search(parent_key) or SENSITIVE_LITERAL.search(value):
                    out.append((node.start_mark.line + 1, classify(value)))
    for doc in docs:
        if doc is not None:
            visit(doc)
    return out


def ini_candidates(content: str):
    out = []
    for ln, line in enumerate(content.splitlines(), 1):
        entry = line.strip()
        if not entry or entry.startswith(('#',';','[')):
            continue
        for key, value in re.findall(r'(?<!\S)([^=\s]+)=([^\s]+)', entry):
            if SENSITIVE_KEY.search(key) and value.strip():
                out.append((ln, classify(value)))
        if SENSITIVE_LITERAL.search(entry):
            out.append((ln, 'HIGH_RISK_LITERAL_OR_CREDENTIAL_URL'))
    return out


def scan(root: Path):
    entries = [root / 'hosts']
    for sub in ('group_vars', 'host_vars'):
        if not (root / sub).is_dir():
            raise ValueError('missing inventory variable directory')
        entries.extend(sorted((root/sub).rglob('*')))
    results = []
    counts = Counter()
    for p in sorted(entries):
        rel = p.relative_to(root).as_posix()
        if p.is_symlink():
            raise ValueError('inventory contains symlink: ' + rel)
        if p.is_dir():
            continue
        if not p.is_file():
            raise ValueError('unsupported inventory path: ' + rel)
        try:
            content = p.read_text(encoding='utf-8')
        except (OSError, UnicodeError):
            raise ValueError('unreadable inventory file: ' + rel) from None
        counts['files'] += 1
        if WHOLE_VAULT.match(content):
            counts['whole_file_vaults'] += 1
            continue
        if rel == 'hosts':
            candidates = ini_candidates(content)
        elif p.suffix.lower() in ('.yaml','.yml'):
            try:
                candidates = yaml_candidates(content)
            except ValueError:
                raise ValueError('invalid YAML/Vault tag: ' + rel) from None
        else:
            raise ValueError('unrecognised inventory file type: ' + rel)
        for line, category in candidates:
            counts[category] += 1
            results.append((rel, line, category))
    return counts, results


def self_test():
    """Run synthetic fixtures only, no live inventory data."""
    assert classify('{{ vault_secret }}') == 'REFERENCE_ONLY'
    assert classify('{{ object.name }}') == 'REFERENCE_ONLY'
    assert classify("{{ password | default('literal') }}") == 'COMPOSITE_OR_COMPLEX_TEMPLATE_REVIEW'
    assert classify('/root/.ssh/id_example') == 'PATH_REFERENCE_REVIEW'
    assert classify('not_a_real_test_secret') == 'PLAINTEXT_LITERAL_REVIEW'
    assert classify('https://fake-user:fake-secret@example.invalid/') == 'HIGH_RISK_LITERAL_OR_CREDENTIAL_URL'
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root/'hosts').write_text('[example]\nexample\n', encoding='utf-8')
        (root/'group_vars').mkdir()
        (root/'host_vars').mkdir()
        (root/'host_vars'/'example.yaml').write_text(
            "password: '{{ vault_password }}'\n"
            "api_token: plain_fake_test_value\n"
            "private_key_file: /root/.ssh/id_example\n"
            "inline_secret: !vault |\n"
            "  $ANSIBLE_VAULT;1.1;AES256\n"
            "  abcdef\n", encoding='utf-8')
        c, rows = scan(root)
        assert c['files'] == 2
        assert c['REFERENCE_ONLY'] == 1
        assert c['PLAINTEXT_LITERAL_REVIEW'] == 1
        assert c['PATH_REFERENCE_REVIEW'] == 1
        assert len(rows) == 3
        assert rows[0] == ('host_vars/example.yaml',1,'REFERENCE_ONLY')
    print('PASS: 0046 synthetic classifier tests (values never emitted)')
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, default=Path('/etc/ansible'))
    ap.add_argument('--self-test', action='store_true')
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    try:
        counts, rows = scan(a.root)
    except (OSError, ValueError) as exc:
        # Error contains only inventory relative path, never parser content/values.
        print('FAIL: ' + str(exc))
        return 1
    print('=== 0046 candidate classification; NO values shown ===')
    print('files=' + str(counts['files']))
    print('whole_file_vaults=' + str(counts['whole_file_vaults']))
    print('candidates=' + str(len(rows)))
    for category in ('REFERENCE_ONLY','PUBLIC_KEY_FORMAT','PATH_REFERENCE_REVIEW',
                     'COMPOSITE_OR_COMPLEX_TEMPLATE_REVIEW',
                     'PLAINTEXT_LITERAL_REVIEW','HIGH_RISK_LITERAL_OR_CREDENTIAL_URL'):
        print(f'{category}={counts[category]}')
    for rel, line, category in rows:
        print(f'CLASSIFY: {rel}:{line} {category}')
    print('NOTICE: no key names, values, ciphertext, plaintext, or Vault password printed')
    # Even all references do not establish that other fields are secret-free.
    if counts['HIGH_RISK_LITERAL_OR_CREDENTIAL_URL'] or counts['PLAINTEXT_LITERAL_REVIEW'] or counts['COMPOSITE_OR_COMPLEX_TEMPLATE_REVIEW'] or counts['PATH_REFERENCE_REVIEW']:
        print('REVIEW REQUIRED: inspect remaining candidates locally on mango, do not paste values in chat')
        return 2
    print('PASS: structural triage only; manual secret review still required before private Git commit')
    return 0


if __name__ == '__main__':
    sys.exit(main())
