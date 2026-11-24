#!/usr/bin/env python3
"""Restage only the reviewed 0028 Gradle task; preserve pre-change evidence.

One-off feature tool. Never runs Gradle or touches a production service.
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
import difflib
import json
from pathlib import Path
import subprocess
import sys


def normalized(text):
    return text.replace('\r\n', '\n').replace('\r', '\n')


def nonblank_lines(text):
    return Counter(line for line in normalized(text).splitlines() if line.strip())


def require_one_task(current, task):
    current_n = normalized(current)
    task_n = normalized(task).strip('\n') + '\n'
    # A task on its own lines. The nearby comment is included in the approved block.
    if current_n.count(task_n) != 1:
        raise ValueError('expected exactly one unchanged 0028 Gradle task block in working tree')
    return current_n, task_n


def make_candidate(head, current, task):
    head_n = normalized(head)
    current_n, task_n = require_one_task(current, task)
    anchor = "tasks.register('migration0024ImageCatalogue', JavaExec) {"
    if head_n.count(anchor) != 1:
        raise ValueError('HEAD does not contain exactly one existing 0024 migration Gradle task')
    if 'migration0028ReviewedFragments' in head_n:
        raise ValueError('0028 task already committed in HEAD; refusing to rewrite')
    without_task = current_n.replace(task_n, '', 1)
    if nonblank_lines(without_task) != nonblank_lines(head_n):
        removed = nonblank_lines(head_n) - nonblank_lines(without_task)
        added = nonblank_lines(without_task) - nonblank_lines(head_n)
        example_missing = list(removed.elements())[:3]
        example_added = list(added.elements())[:3]
        raise ValueError('non-0028 build.gradle edits detected; refusing to overwrite: '
                         'missing {!r}, extra {!r}'.format(example_missing, example_added))
    # Preserve Git HEAD's order; put the reviewed 0028 task immediately ahead of 0024.
    candidate = head_n.replace(anchor, task_n + '\n' + anchor, 1)
    if not staged_diff_only_adds_task(head_n, candidate):
        raise ValueError('candidate makes changes other than adding the approved 0028 task')
    return candidate


def staged_diff_only_adds_task(head, candidate):
    diffs = difflib.SequenceMatcher(a=normalized(head).splitlines(keepends=True),
                                    b=normalized(candidate).splitlines(keepends=True),
                                    autojunk=False).get_opcodes()
    return all(tag in ('equal', 'insert') for tag, *_ in diffs) and sum(
        b2-b1 for tag, a1, a2, b1, b2 in diffs if tag == 'insert') > 0


def git(responder, *args, check=True):
    # Use the responder as the process working directory. Cygwin Python may
    # find native Windows git.exe, which cannot parse /cygdrive/c paths passed
    # through Git's -C argument. The OS converts subprocess cwd correctly.
    p = subprocess.run(['git', *args], cwd=str(responder),
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if check and p.returncode:
        raise RuntimeError('git {} failed: {}'.format(' '.join(args),
                           p.stderr.decode('utf-8', errors='replace')[:800]))
    return p.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='write and stage the minimal diff')
    args = parser.parse_args()

    feature = Path(__file__).resolve().parent.parent
    repo = feature.parents[2]  # feature / in-progress / change-control / diaries root
    responder = repo / 'diaries-responder'
    gradle = responder / 'build.gradle'
    task_file = feature / 'tools' / 'migration0028-gradle-task.inc'
    if not gradle.is_file() or not task_file.is_file():
        raise ValueError('expected checked-out Diaries responder and feature tools')
    head_bytes = git(responder, 'show', 'HEAD:build.gradle')
    head = head_bytes.decode('utf-8')
    working_bytes = gradle.read_bytes()
    working = working_bytes.decode('utf-8')
    candidate = make_candidate(head, working, task_file.read_text(encoding='utf-8'))
    print('PASS: worktree includes the exact approved 0028 task and no other content edits')
    print('PASS: minimal HEAD + task produces insert-only Gradle diff')
    print('Responder source:', git(responder, 'rev-parse', 'HEAD').decode().strip())
    print('Restaged Java/SQL/tests are not modified by this tool')

    if not args.apply:
        print('DRY RUN: no files modified; add --apply to repair and restage build.gradle')
        return

    evidence_root = feature / 'evidence' / 'Step 3' / 'private'
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    evidence = evidence_root / (stamp + '-gradle-diff-repair')
    evidence.mkdir(parents=True, exist_ok=False)
    (evidence / 'build.gradle.before').write_bytes(working_bytes)
    (evidence / 'build.gradle.HEAD').write_bytes(head_bytes)
    (evidence / 'build.gradle.minimal-LF').write_bytes(candidate.encode('utf-8'))

    # Construct from the exact committed bytes, preserving ALL pre-existing line endings.
    eol = b'\r\n' if head_bytes.count(b'\r\n') > head_bytes.count(b'\n') / 2 else b'\n'
    anchor_bytes = b"tasks.register('migration0024ImageCatalogue', JavaExec) {"
    approved = normalized(task_file.read_text(encoding='utf-8')).strip('\n') + '\n'
    task_bytes = approved.replace('\n', eol.decode('ascii')).encode('utf-8')
    target_bytes = head_bytes.replace(anchor_bytes, task_bytes + eol + anchor_bytes, 1)
    if normalized(target_bytes.decode('utf-8')) != candidate:
        raise RuntimeError('generated byte-exact candidate does not match reviewed insertion')
    gradle.write_bytes(target_bytes)
    git(responder, 'add', '--', 'build.gradle')
    staged = git(responder, 'show', ':build.gradle').decode('utf-8')
    if normalized(staged) != candidate:
        raise RuntimeError('staged Gradle blob does not match the minimal candidate; inspect evidence')
    numstat = git(responder, 'diff', '--cached', '--numstat', '--', 'build.gradle')
    stat_cols = numstat.decode('utf-8').split('\t')
    expected_additions = approved.count('\n') + 1  # task lines plus separating empty line
    if len(stat_cols) < 3 or stat_cols[0] != str(expected_additions) or stat_cols[1] != '0':
        raise RuntimeError('unexpected staged Git diff ({}); inspect saved pre-change evidence'.format(
            numstat.decode('utf-8', errors='replace').strip()))
    (evidence / 'REPAIR-RECEIPT.json').write_text(json.dumps({
        'schema': 1,
        'feature': '0028-FEAT',
        'responderHead': git(responder, 'rev-parse', 'HEAD').decode().strip(),
        'purpose': 'restore original Gradle order and stage only the 0028 task',
        'productionChanges': False,
        'evidenceDirectory': str(evidence.relative_to(repo)),
    }, indent=2) + '\n', encoding='utf-8')
    print('PASS: minimal Gradle task staged; previous working file saved in', evidence.relative_to(repo))
    print('=== Exact staged build.gradle summary ===')
    print(git(responder, 'diff', '--cached', '--stat', '--', 'build.gradle').decode('utf-8'))
    print('=== Exact staged build.gradle diff ===')
    print(git(responder, 'diff', '--cached', '--', 'build.gradle').decode('utf-8'))
    print('DO NOT COMMIT until the diff is reviewed.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError) as exc:
        print('FAIL:', exc, file=sys.stderr)
        sys.exit(2)
