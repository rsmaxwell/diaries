#!/usr/bin/env python3
"""0028 feature-scoped safe Git staging. Does NOT commit/push or touch production.

Cygwin/Windows Git: use subprocess cwd rather than `git -C <cygdrive-path>`.
The script audits ALL candidate files before staging ANY of them.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

FEATURE = 'change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
PIN = '7aa6296e0c675b3d315e9a46bb0dd70202a8cd55'
ROOT_FILES = {'README.md', 'IMPLEMENTATION-STEPS.md',
              'DESIGN-AND-INTERFACE-CONTRACT.md', '.gitignore'}
TOOL_SUFFIXES = {'.py', '.sh', '.js', '.json', '.conf', '.inc', '.md',
                 '.txt', '.bat', '.yml', '.yaml', '.html', '.css'}
BAD_PARTS = {'evidence', 'scratch', 'private', '__pycache__', 'node_modules',
             '.git', '.gradle', 'build', 'dist', 'generated'}
BAD_EXTS = {'.jar', '.class', '.zip', '.7z', '.tar', '.gz', '.dump', '.sql',
            '.sqlite', '.db', '.log', '.pem', '.key', '.p12', '.pfx', '.crt',
            '.env', '.bak', '.png', '.jpg', '.jpeg', '.gif', '.webp'}
MAX_BYTES = 600_000
SENSITIVE = (
    re.compile(rb'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
    re.compile(rb'(?i)\b(?:ghp_|github_pat_|sk-[a-zA-Z0-9_-]{18,})[a-zA-Z0-9_\-]{12,}'),
    re.compile(rb'(?i)\b(?:postgres|postgresql|mqtt|amqp|https?)://[^\s/@:]+:[^\s/@]+@'),
)

# Explicit synthetic URL validation fixtures. Keep genuine credential-bearing URLs
# blocked, including in tests. Only these literal test values in their named methods
# may be ignored by the staging credential scan.
SYNTHETIC_URL_FIXTURES = {
    'tests/test_step4_0051_compatibility_review.py': (
        b'https://' b'name:password@example.org/',
        b'def test_dangerous_urls_are_rejected(self):',
        b'self.assertFalse(valid_url(url),url)',
    ),
    'tests/test_step4_0051_portal_suggestions.py': (
        b'https://' b'name:pass@example.org/',
        b'def test_dangerous_or_ambiguous_link_never_suggested(self):',
        b"self.assertNotIn('link_handling',source_suggestions(r))",
    ),
}

class Stop(Exception):
    pass

def content_for_credential_scan(relative, content):
    """Mask only an explicitly reviewed negative test case, never arbitrary URLs.

    If its structure, count or scope changes, leave the URL unchanged so the
    ordinary credential check rejects it. The original bytes are still hashed.
    """
    case = SYNTHETIC_URL_FIXTURES.get(relative)
    if case is None:
        return content
    fixture, test_header, expected_assertion = case
    if content.count(fixture) != 1 or content.count(test_header) != 1:
        return content
    start = content.index(test_header)
    end = content.find(b'\n    def ', start + len(test_header))
    if end < 0:
        end = len(content)
    position = content.find(fixture)
    if not (start < position < end):
        return content
    if expected_assertion not in content[position:end]:
        return content
    # Mask only this exact fixture; all other URLs and token patterns remain.
    return content[:position] + b'https://example.org/' + content[position + len(fixture):]

def git(repo, *args, check=True):
    result = subprocess.run(['git', *args], cwd=str(repo), stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, check=False)
    if check and result.returncode:
        raise Stop('git ' + ' '.join(args[:3]) + ' failed: ' +
                   result.stderr.decode('utf-8', 'replace').strip())
    return result

def git_paths(repo, *args):
    return [entry.decode('utf-8', 'surrogateescape')
            for entry in git(repo, *args).stdout.split(b'\x00') if entry]

def candidate_path_allowed(relative):
    """Return a reason for rejection, or None for a reviewable source file."""
    parts = PurePosixPath(relative).parts
    if not parts or any(part in ('', '.', '..') for part in parts):
        return 'unsafe path'
    if any(part.casefold() in BAD_PARTS for part in parts):
        return 'excluded private/generated directory'
    if any(part.endswith('~') for part in parts):
        return 'editor backup'
    path = PurePosixPath(relative)
    if path.suffix.lower() in BAD_EXTS:
        return 'disallowed data/binary suffix'
    if len(parts) == 1:
        return None if relative in ROOT_FILES else 'unreviewed feature root file'
    first = parts[0]
    if first == 'reports':
        return None if path.suffix.lower() == '.md' else 'reports permit Markdown only'
    if first == 'tests':
        return None if path.suffix.lower() in {'.py', '.sh'} else 'tests permit Python/Bash only'
    if first == 'tools':
        if path.name == 'Dockerfile':
            return None
        if path.suffix.lower() in TOOL_SUFFIXES:
            return None
        if path.suffix.lower() == '.csv' and '.example.' in path.name.lower():
            return None
        return 'tool file type requires independent review'
    return 'directory not in reviewed feature scope'

def inspect_file(root, repo_relative):
    if not repo_relative.startswith(FEATURE + '/'):
        raise Stop('out-of-scope candidate: ' + repo_relative)
    relative = repo_relative[len(FEATURE) + 1:]
    rejection = candidate_path_allowed(relative)
    if rejection:
        raise Stop('BLOCKED ' + repo_relative + ': ' + rejection)
    p = root / repo_relative
    if p.is_symlink() or not p.is_file():
        raise Stop('BLOCKED nonregular or symlink file: ' + repo_relative)
    if p.stat().st_size > MAX_BYTES:
        raise Stop('BLOCKED oversize source (review separately): ' + repo_relative)
    content = p.read_bytes()
    if b'\x00' in content:
        raise Stop('BLOCKED binary source: ' + repo_relative)
    scan_content = content_for_credential_scan(relative, content)
    for rule in SENSITIVE:
        if rule.search(scan_content):
            raise Stop('BLOCKED possible embedded credential in: ' + repo_relative)
    return {'path':repo_relative, 'bytes':len(content),
            'sha256':hashlib.sha256(content).hexdigest()}

def source_changes(repo):
    raw = git(repo, 'status', '--porcelain=v1', '-z', '--untracked-files=all',
              '--', FEATURE).stdout
    results = []
    for record in raw.split(b'\x00'):
        if not record:
            continue
        if len(record) < 4 or record[2:3] != b' ':
            raise Stop('unexpected Git status record: ' + repr(record[:80]))
        code = record[:2].decode('ascii', 'replace')
        if code not in ('??', ' M', 'M ', 'MM', ' A', 'A '):
            raise Stop('unsupported 0028 Git state ' + code + ': ' +
                       record[3:].decode('utf-8', 'replace'))
        name = record[3:].decode('utf-8', 'surrogateescape')
        results.append(name)
    return sorted(results)

def save_receipt(repo, records, mode):
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    folder = repo / FEATURE / 'evidence' / 'Step 3' / 'private' / (stamp + '-git-consolidation')
    if folder.exists():
        raise Stop('evidence folder already exists; retry when safe: ' + str(folder))
    folder.mkdir(parents=True)
    receipt = {'schema':1,'feature':'0028-FEAT','mode':mode,
               'source_parent_commit':git(repo,'rev-parse','HEAD').stdout.decode().strip(),
               'source_responder_pin':PIN,
               'excluded':['evidence/**','scratch/**','change-control/todo/0029/**',
                           'change-control/in-progress/0053/**'],
               'source_files':records,
               'production_apply_authorised':False,
               'feature_closed':False}
    (folder/'REVIEW.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    return folder

def run(repo, stage):
    if not (repo/'.git').exists() or not (repo/FEATURE/'README.md').is_file():
        raise Stop('run from the Diaries parent checkout root (Windows Cygwin)')
    original_staged = git_paths(repo, 'diff', '--cached', '--name-only','-z')
    if original_staged:
        raise Stop('existing staged parent changes found; stage/commit/review those separately; no changes made: ' +
                   ', '.join(original_staged[:4]))
    pin = git(repo,'rev-parse','HEAD:diaries-responder').stdout.decode().strip()
    if pin != PIN:
        raise Stop('parent no longer pins expected responder ' + PIN + '; current ' + pin)
    submodule_status = git(repo/'diaries-responder','status','--porcelain').stdout.strip()
    if submodule_status:
        raise Stop('responder submodule dirty; no changes staged')
    names = source_changes(repo)
    if not names:
        raise Stop('no unstaged/untracked 0028 files to consolidate')
    records = [inspect_file(repo, name) for name in names]
    print('PASS: parent pin and responder working-tree checks')
    print('PASS: reviewable 0028-only files: %d, bytes: %d' %
          (len(records), sum(r['bytes'] for r in records)))
    print('Excluded: private evidence, 0029, 0053 and all unrelated paths')
    print('Included paths:')
    for r in records:
        print(' ', r['path'], '(%d bytes)' % r['bytes'])
    if stage:
        # All candidates passed checks, and nothing else was staged initially.
        for i in range(0,len(names),32):
            git(repo,'add','--', *names[i:i+32])
        actual = sorted(git_paths(repo,'diff','--cached','--name-only','-z'))
        if actual != names:
            raise Stop('STAGED SET MISMATCH: inspect git diff --cached immediately; no commit made')
        git(repo,'diff','--cached','--check')
        # Detect if any file was modified between the pre-stage scan and staging.
        for r in records:
            current = inspect_file(repo,r['path'])
            if current['sha256'] != r['sha256']:
                raise Stop('file changed during staging: ' + r['path'] +
                           '; inspect index; no commit made')
        print('PASS: only the audited 0028 file set is staged; no commit/push')
    folder = save_receipt(repo,records,'stage' if stage else 'preview')
    print('Private evidence:', folder.relative_to(repo))
    print('OPEN: review staged change-control content and explicitly commit; formal 0028 approval still open')

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',action='store_true',help='stage audited 0028 source only, never commit')
    args=parser.parse_args()
    try:
        run(Path.cwd(), args.stage)
    except (OSError, Stop) as exc:
        print('FAIL:', exc, file=sys.stderr)
        raise SystemExit(2)
