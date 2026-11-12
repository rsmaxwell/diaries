#!/usr/bin/env python3
"""Offline integration smoke test for the one-off 0046 assembler. No GitHub or Ansible access."""
from pathlib import Path
import subprocess
import tempfile
import os
import shutil
import sys

SOURCE = Path(__file__).resolve().parent.parent / 'tools' / 'establish-0046-three-repositories.sh'

def run(cmd, cwd=None, env=None, quiet=False):
    p = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
    if p.returncode and not quiet:
        raise RuntimeError(f'{cmd} exit={p.returncode}\n{p.stdout[-2000:]}\n{p.stderr[-2000:]}')
    return p


def main():
    with tempfile.TemporaryDirectory(prefix='0046-repo-test-') as t:
        x=Path(t)
        root=x/'ansible-controller'; inv=root/'inventory'; pub=x/'playbooks'; old=x/'etc'/'ansible'; home=x/'home'; rem=x/'remotes'; fake=x/'bin'
        for p in (inv, pub, old, home, rem, fake): p.mkdir(parents=True, exist_ok=True)
        for p in (old, inv):
            (p/'hosts').write_text('[all]\nmars\n')
            (p/'group_vars').mkdir(); (p/'host_vars'/'pluto').mkdir(parents=True)
            for i in range(42): (p/'group_vars'/f'v{i:02d}.yaml').write_text(f'a{i}: 1\n')
            (p/'host_vars'/'pluto'/'vault.yaml').write_text('$ANSIBLE_VAULT;1.1;AES256\nabcdef\n')
        (home/'.vault_pass.txt').write_text('test-only\n')
        run(['git','init','--bare','--initial-branch=main',str(rem/'ansible-playbooks.git')])
        cfg=x/'gitconfig'
        cfg.write_text(f'[user]\n\tname = Synthetic Test\n\temail = test@example.invalid\n[protocol "file"]\n\tallow = always\n[url "file://{rem}/"]\n\tinsteadOf = git@github.com:rsmaxwell/\n')
        env=dict(os.environ,HOME=str(home),GIT_CONFIG_GLOBAL=str(cfg),GIT_CONFIG_NOSYSTEM='1',PATH=f'{fake}:'+os.environ['PATH'],TEST_USER=run(['id','-un']).stdout.strip(),GIT_BARE_ROOT=str(rem))
        run(['git','init','-b','main'], cwd=pub, env=env)
        (pub/'README.md').write_text('# Public test playbooks\n')
        run(['git','add','README.md'], cwd=pub, env=env)
        run(['git','commit','-m','base'], cwd=pub, env=env)
        run(['git','remote','add','origin','git@github.com:rsmaxwell/ansible-playbooks.git'], cwd=pub, env=env)
        run(['git','push','-u','origin','main'], cwd=pub, env=env)
        sha=run(['git','rev-parse','HEAD'],cwd=pub,env=env).stdout.strip()
        gh='''#!/usr/bin/env bash
set -e
repo_path() { printf '%s/%s.git' "$GIT_BARE_ROOT" "${1#rsmaxwell/}"; }
if [[ "$1 $2" == 'auth status' ]]; then exit 0; fi
if [[ "$1 $2" == 'repo create' ]]; then
  name="$3"; path="$(repo_path "$name")"; [[ " $* " == *' --private '* ]] || exit 21
  git init --bare --initial-branch=main "$path" >/dev/null; exit 0
fi
if [[ "$1 $2" == 'repo view' ]]; then
  name="$3"; path="$(repo_path "$name")"; [[ -d "$path" ]] || exit 1
  case " $* " in
    *' -q .visibility'*) if [[ "$name" == rsmaxwell/ansible-playbooks ]]; then echo PUBLIC; else echo PRIVATE; fi;;
    *' -q .isEmpty'*) [[ -z "$(git --git-dir="$path" rev-list --all 2>/dev/null)" ]] && echo true || echo false;;
    *' -q .sshUrl'*) echo "git@github.com:$name.git";;
  esac
  exit 0
fi
exit 60
'''
        (fake/'gh').write_text(gh); (fake/'gh').chmod(0o755)
        script = SOURCE.read_text()
        script=script.replace("ROOT='/home/richard/ansible-controller'", f"ROOT='{root}'")
        script=script.replace("OLD='/etc/ansible'", f"OLD='{old}'")
        script=script.replace("PUBLIC='/home/richard/playbooks'",f"PUBLIC='{pub}'")
        script=script.replace("EXPECTED_PLAYBOOKS_SHA='dca638c00cc3b0fe2f2a46ef01c060cb1a1f6296'",f"EXPECTED_PLAYBOOKS_SHA='{sha}'")
        script=script.replace("[[ \"$(id -un)\" == 'richard' ]]", "[[ \"$(id -un)\" == \"$TEST_USER\" ]]")
        script=script.replace("[[ \"$HOME\" == '/home/richard' ]]", f"[[ \"$HOME\" == '{home}' ]]")
        s=x/'stage.sh';s.write_text(script);s.chmod(0o755)
        print('=== Preflight ===')
        pre=run(['bash',str(s),'--preflight'],env=env)
        assert 'PASS: read-only repository assembly preflight' in pre.stdout,pre.stdout
        assert not (root/'.git').exists()
        print('PASS: preflight leaves sources untouched')
        print('=== Apply ===')
        ap=run(['bash',str(s),'--apply'],env=env)
        assert 'PASS: three-repository stage published' in ap.stdout,ap.stdout
        assert (root/'.gitmodules').exists()
        assert (root/'inventory'/'hosts').is_file()
        assert (root/'playbooks'/'README.md').is_file()
        assert 'git@github.com:rsmaxwell/ansible-inventory.git' in (root/'.gitmodules').read_text()
        assert not (root/'inventory'/'.vault_pass.txt').exists()
        assert run(['git','-C',str(root/'playbooks'),'rev-parse','HEAD'],env=env).stdout.strip()==sha
        assert run(['git','-C',str(root),'status','--porcelain'],env=env).stdout.strip()==''
        assert run(['git','-C',str(pub),'status','--porcelain'],env=env).stdout.strip()==''
        assert (old/'hosts').is_file()
        assert run(['git','--git-dir',str(rem/'ansible-controller.git'),'rev-parse','main'],env=env).stdout.strip()==run(['git','-C',str(root),'rev-parse','HEAD'],env=env).stdout.strip()
        print('PASS: staged two private remotes, submodule pins, clean trees, original sources unchanged')
        # Repeat refuses pre-existing local Git rather than altering an accepted state.
        second=run(['bash',str(s),'--apply'],env=env,quiet=True)
        assert second.returncode != 0 and 'Git worktree' in second.stderr,(second.returncode,second.stderr)
        print('PASS: fail-closed repeat execution')

if __name__=='__main__':
    main()
