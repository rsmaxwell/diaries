#!/usr/bin/env bash
# 0048: verify NO explicit modes on rsync-backed directories.
# Run from Windows Cygwin: ssh mango 'bash -s' < this-file
# Writes only to a disposable directory on mango; reads mars metadata only.
set -Eeuo pipefail
umask 022
controller='/home/richard/ansible-controller'
playbooks="$controller/playbooks"
tmpdir=''
cleanup() { [[ -z "$tmpdir" || ! -d "$tmpdir" ]] || rm -rf -- "$tmpdir"; }
trap cleanup EXIT
printf '0048 STEP 3 GIT-NATIVE DEFAULT-MODE PREDEPLOYMENT TEST\nUTC: '
date -u '+%Y-%m-%dT%H:%M:%SZ'
printf 'HOST: '; hostname
[[ "$(id -u)" -ne 0 ]] || { echo 'FAIL: do not run as root'; exit 1; }
for app in git python3 ansible-playbook rsync stat mktemp ssh; do
  command -v "$app" >/dev/null || { echo "FAIL: missing $app"; exit 1; }
done
cd -- "$controller"
[[ "$(git branch --show-current)" = main ]] || { echo 'FAIL: controller not on main'; exit 1; }
[[ "$(git rev-parse :playbooks)" = "$(git -C playbooks rev-parse HEAD)" ]] || {
  echo 'FAIL: Playbooks checkout differs from parent Git pin'; exit 1;
}
[[ -z "$(git -C inventory status --porcelain)" ]] || {
  echo 'FAIL: inventory has changes'; exit 1;
}
echo "CONTROLLER=$(git rev-parse HEAD)"
echo "PLAYBOOKS_BASE=$(git -C playbooks rev-parse HEAD)"
echo "INVENTORY=$(git -C inventory rev-parse HEAD)"
echo '=== Working Playbooks changes (do not mistake candidate files for published code) ==='
git -C playbooks status --short

tmpdir="$(mktemp -d "${TMPDIR:-/tmp}/0048-step3.XXXXXXXX")"
clone="$tmpdir/clean-playbooks"
remote="$(git -C playbooks remote get-url origin)"
git clone --quiet --no-checkout "$remote" "$clone"
git -C "$clone" checkout --quiet --detach "$(git -C playbooks rev-parse HEAD)"
[[ -z "$(git -C "$clone" status --porcelain)" ]] || { echo 'FAIL: clone not clean'; exit 1; }

python3 - "$playbooks" "$clone" "$tmpdir" <<'PY'
import copy
import hashlib
import json
import pathlib
import stat
import sys
import yaml

work = pathlib.Path(sys.argv[1]); clone = pathlib.Path(sys.argv[2]); dest = pathlib.Path(sys.argv[3])
role = work / 'roles/backup-collection'
source = clone / 'roles/backup-collection/files'
dirs = ('backup', 'backup/home', 'backup-machine', 'backup-machine/home', 'backup-machine/remote')
expected_filters = {
    'backup/home/excludes-1': '7225808ccc8c9c684ae1098d0ea46557c49419342ddc5d88af004413cb27e1d9',
    'backup-machine/home/excludes-1': '82e17319c7c4ee418ebfb23c94b3327e6c16614fa694a42154efeda9d1107b4b',
    'backup-machine/remote/excludes-1': '9898acd1777ad4ac07242209c2ce351578531596fb9f85d3e2abc6a9dd8e241b',
}
empty = hashlib.sha256(b'').hexdigest()
for subdir in ('backup/home', 'backup-machine/home', 'backup-machine/remote'):
    for filename in ('includes', 'excludes-1', 'excludes-2'):
        expected_filters.setdefault(f'{subdir}/{filename}', empty)

for relative in dirs + tuple(expected_filters):
    src = source / relative
    wk = role / 'files' / relative
    assert src.exists() and wk.exists() and not src.is_symlink() and not wk.is_symlink(), relative
    assert src.is_dir() == (relative in dirs) and wk.is_dir() == src.is_dir(), relative
    mode = stat.S_IMODE(src.stat().st_mode)
    expected_mode = 0o755 if relative in dirs else 0o644
    assert mode == expected_mode, f'{relative}: clean clone {mode:04o} != {expected_mode:04o}'
    if relative in expected_filters:
        assert hashlib.sha256(src.read_bytes()).hexdigest() == expected_filters[relative], relative
        assert hashlib.sha256(wk.read_bytes()).hexdigest() == expected_filters[relative], relative
print('PASS: fresh checkout (umask 022) has 5 dirs 0755 and 9 filters 0644, with frozen hashes')

workspace_modes = [(rel, stat.S_IMODE((role / 'files' / rel).stat().st_mode))
                   for rel in dirs + tuple(expected_filters)]
wrong = [(rel, f'{mode:04o}') for rel, mode in workspace_modes
         if mode != (0o755 if rel in dirs else 0o644)]
print(f'WORKING_COPY_MODE_DIFFERENCES={len(wrong)}')
for rel, mode in wrong:
    print(f'REVIEW BEFORE DEPLOYMENT: working-copy mode {mode} differs from clean-clone mode: {rel}')

# Extract the actual role tasks from the proposed Playbooks checkout: no mocks.
def make_tasks(filename, src, dest_suffix, path_prefixes):
    tasks = yaml.safe_load((role / 'tasks' / filename).read_text())
    creates = [t for t in tasks if t.get('name', '').endswith('Create directories')]
    copies = [t for t in tasks if 'ansible.posix.synchronize' in t]
    assert len(creates) == len(copies) == 1, filename
    create = copy.deepcopy(creates[0]); sync_task = copy.deepcopy(copies[0])
    field = create['ansible.builtin.file']
    assert field['state'] == 'directory', filename
    items = create['loop']
    if src == 'backup/':
        assert field['path'] == '{{ backup_directory.path }}', filename
        assert field.get('mode') == '{{ backup_directory.mode | default(omit) }}', filename
        modes = {item['path']: item.get('mode') for item in items}
        expected = {
            '{{ normal_user_home }}/scripts/backup': None,
            '{{ normal_user_home }}/scripts/backup/home': None,
            '{{ normal_user_home }}/scripts/backup/cron': '0750',
            '{{ normal_user_home }}/log/backup': '0750',
        }
        assert modes == expected, f'user create-directory policy: {modes}'
    else:
        assert field['path'] == '{{ backup_directory }}', filename
        assert 'mode' not in field, 'machine directory task must not override source modes'
        assert len(items) == 5, filename
    sync = sync_task['ansible.posix.synchronize']
    assert sync['archive'] is True and sync['src'] == src, filename
    assert '--omit-dir-times' in sync['rsync_opts'], filename
    assert not any('--chmod' in opt or '--no-perms' in opt for opt in sync['rsync_opts']), filename
    for item in items:
        path = item['path'] if isinstance(item, dict) else item
        for prefix, replacement in path_prefixes:
            if path.startswith(prefix):
                mapped = path.replace(prefix, replacement, 1)
                if isinstance(item, dict):
                    item['path'] = mapped
                else:
                    items[items.index(item)] = mapped
                break
        else:
            raise AssertionError(f'unrecognised creation path: {path}')
    sync_task['ansible.posix.synchronize']['src'] = (
        '{{ clone_root }}/roles/backup-collection/files/' + src)
    sync_task['ansible.posix.synchronize']['dest'] = '{{ target_root }}/' + dest_suffix + '/'
    sync_task.pop('register', None)
    return [create, sync_task]

items = make_tasks('install_user_scripts.yaml', 'backup/', 'user', [
    ('{{ normal_user_home }}/scripts/backup', '{{ target_root }}/user'),
    ('{{ normal_user_home }}/log/backup', '{{ target_root }}/user-log'),
])
items += make_tasks('install_machine_scripts.yaml', 'backup-machine/', 'machine', [
    ('/root/scripts/backup', '{{ target_root }}/machine'),
    ('/root/log/backup', '{{ target_root }}/machine-log'),
])
play = [{'name':'0048 proposed default-mode create and rsync tasks',
         'hosts':'localhost','connection':'local','gather_facts':False,
         'become':False,'tasks':items}]
(dest / 'harness.yml').write_text(yaml.safe_dump(play, sort_keys=False))
print('PASS: proposed role tasks set NO modes on synchronized directories; no rsync overrides')
PY

run_case() {
  local label="$1"
  local target="$tmpdir/target-$label"
  mkdir -p -- "$target"
  if [[ "$label" = existing-0750 ]]; then
    # Simulates the accepted 0047 installed state. None of these are live paths.
    for rel in user user/home machine machine/home machine/remote; do
      mkdir -p -- "$target/$rel"
      chmod 0750 -- "$target/$rel"
    done
    mkdir -p -- "$target/user/cron" "$target/user-log"
    chmod 0750 -- "$target/user/cron" "$target/user-log"
  fi
  python3 - "$clone" "$target" "$tmpdir/vars-$label.json" <<'PY'
import json, sys
json.dump({'clone_root':sys.argv[1], 'target_root':sys.argv[2]},open(sys.argv[3],'w'))
PY
  echo "=== $label: Ansible run 1 (disposable target) ==="
  ansible-playbook -i localhost, -c local "$tmpdir/harness.yml" \
    -e "@$tmpdir/vars-$label.json" | tee "$tmpdir/$label-run1.log"
  echo "=== $label: Ansible run 2 (must be unchanged) ==="
  ansible-playbook -i localhost, -c local "$tmpdir/harness.yml" \
    -e "@$tmpdir/vars-$label.json" | tee "$tmpdir/$label-run2.log"
  local changed
  changed="$(sed -nE '/^localhost[[:space:]]*:/s/.*changed=([0-9]+).*/\1/p' "$tmpdir/$label-run2.log" | tail -n 1)"
  [[ "$changed" =~ ^[0-9]+$ ]] || { echo "FAIL: $label run 2 recap unparseable"; return 1; }
  echo "${label^^}_RUN2_CHANGED=$changed"
  [[ "$changed" = 0 ]] || { echo "FAIL: $label run 2 not idempotent"; return 1; }
  python3 - "$target" "$label" <<'PYMODES'
import pathlib, stat, sys
base = pathlib.Path(sys.argv[1]); label = sys.argv[2]
expected = {rel:0o755 for rel in ('user','user/home','machine','machine/home','machine/remote')}
expected.update({'user/cron':0o750, 'user-log':0o750})
for rel, mode in expected.items():
    p = base / rel
    assert stat.S_IMODE(p.stat().st_mode) == mode, (rel, oct(stat.S_IMODE(p.stat().st_mode)))
for subdir in ('user/home','machine/home','machine/remote'):
    for filename in ('includes','excludes-1','excludes-2'):
        p=base/subdir/filename
        assert stat.S_IMODE(p.stat().st_mode) == 0o644, str(p)
print(f'PASS: {label} effective modes: synced dirs 0755, filters 0644, user cron/log 0750')
PYMODES
}
run_case fresh
run_case existing-0750

printf '\n=== Read-only mars ancestry and intended reader checks ===\n'
ssh mars 'sudo -n bash -s' <<'MARS'
set -e
[[ "$(stat -c '%a' /home/richard)" = 750 ]] || { echo 'FAIL: home ancestry changed'; exit 1; }
[[ "$(stat -c '%a' /root)" = 700 ]] || { echo 'FAIL: root ancestry changed'; exit 1; }
sudo -n -u richard test -r /home/richard/scripts/backup/home/excludes-1 || {
    echo 'FAIL: richard cannot read user filter'; exit 1;
}
test -r /root/scripts/backup/home/excludes-1 || {
    echo 'FAIL: root cannot read machine filter'; exit 1;
}
if sudo -n -u nobody test -r /home/richard/scripts/backup/home/excludes-1; then
    echo 'FAIL: nobody unexpectedly reads user filter'; exit 1;
fi
if sudo -n -u nobody test -r /root/scripts/backup/home/excludes-1; then
    echo 'FAIL: nobody unexpectedly reads root filter'; exit 1;
fi
printf 'GROUP_RICHARD='; getent group richard || true
echo 'PASS: existing ancestry denies unauthorized reads; legitimate readers allowed'
MARS

echo 'PASS: disposable clean-clone default-mode convergence and mars access checks; no production deployment'
