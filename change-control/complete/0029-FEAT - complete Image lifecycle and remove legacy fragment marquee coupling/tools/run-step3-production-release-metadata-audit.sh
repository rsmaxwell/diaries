#!/usr/bin/env bash
# 0029 Step 3 — read-only production release and backup metadata audit.
# Windows Cygwin: run from the Diaries parent repository root.
set -o pipefail
feature='change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling'
evidence="$feature/evidence/step-3-production-release-readiness"
mkdir -p "$evidence" || exit 1
stamp=$(date -u +%Y%m%d-%H%M%S)
log="$evidence/release-metadata-$stamp.log"
exec > >(tee "$log") 2>&1
printf '0029 STEP 3 — PRODUCTION RELEASE READ-ONLY METADATA AUDIT UTC=%s\n' "$(date -u +%FT%TZ)"
printf 'Evidence: %s\n' "$log"
fail=0
section() { printf '\n=== %s ===\n' "$1"; }
check() { label=$1; shift; if "$@"; then printf 'PASS: %s\n' "$label"; else printf 'FAIL: %s\n' "$label"; fail=1; fi; }
section 'Windows source provenance — parent and three independent submodules'
check 'local Git revision/status' bash -c 'git status --short --branch; git rev-parse HEAD; git submodule status; for d in diaries-client diaries-responder diaries-web; do echo "--- $d ---"; git -C "$d" status --short --branch; git -C "$d" rev-parse HEAD; done'
section 'Ansible controller and Playbooks Git provenance — mango'
check 'mango Git metadata' ssh mango 'cd /home/richard/ansible-controller && git status --short --branch && git rev-parse HEAD && git submodule status && cd playbooks && git status --short --branch && git rev-parse HEAD'
section 'Effective pluto image tags from decrypted Ansible inventory — allowlisted fields ONLY'
# Never print raw inventory: it may include Vault secrets. Python only emits safe image identifiers.
check 'Ansible effective image resolution' ssh mango 'cd /home/richard/ansible-controller && ansible-inventory -i inventory/hosts --host pluto --vault-password-file ~/.vault_pass.txt | python3 -c '\''import json,sys; x=json.load(sys.stdin); keys=("diaries_client_image_name","diaries_client_image_tag","diaries_responder_image_name","diaries_responder_image_tag","diaries_web_image_name","diaries_web_image_tag","diaries_frontend_mode","diaries_files_dir","diaries_complete_backup_published_root"); print("NOTE: role defaults are not merged into ansible-inventory --host; absent values must be checked in role defaults and playbook output."); [(print(k+"="+str(x[k]) if k in x else k+"=<not present in host inventory>")) for k in keys]'\'''
section 'Source role default image tags — mango (safe non-secret lines)'
check 'role image defaults' ssh mango 'cd /home/richard/ansible-controller/playbooks && grep -E "^diaries_(client|responder|web)_image_(name|tag):" roles/diaries/defaults/main.yaml'
section 'Live container image tags and IDs — pluto'
check 'running container image identities' ssh pluto 'for n in diaries-client diaries-responder diaries-web diaries-postgres diaries-mosquitto; do docker inspect --format "{{.Name}} image={{.Config.Image}} id={{.Image}} state={{.State.Status}}" "$n" || exit 1; done'
section 'Production complete-backup publication — pluto (metadata only)'
check 'backup publication directory metadata' ssh pluto 'p="$HOME/projects/diaries/data/diaries-backup"; if [ -d "$p" ]; then ls -ld "$p"; find "$p" -maxdepth 2 -type f \( -name "*.manifest" -o -name "manifest*.json" -o -name "*.sha256" -o -name "*.dump" \) -printf "%TY-%Tm-%TdT%TH:%TM:%TS %s %p\n" | head -n 35; else echo "NOT FOUND: $p (check actual production project root)"; exit 1; fi'
section 'Production backup service/timer state — pluto (no execution)'
check 'backup service metadata' ssh pluto 'systemctl show diaries-complete-backup-publish.service -p ActiveState -p Result -p ExecMainStatus -p ExecMainExitTimestamp; systemctl list-timers --all --no-pager diaries-complete-backup-publish.timer'
section 'Live production annual MQTT ACL — pluto (no credentials)'
check 'deployed annual topic ACL metadata' ssh pluto 'docker exec diaries-mosquitto sh -c '\''if [ -r /mosquitto/config/aclfile ]; then grep -n -E "^(user diaries-|topic (read|readwrite) diaries/years/#)" /mosquitto/config/aclfile; else echo "ACL path not found; inspect mounted config location"; exit 1; fi'\'''
section 'Result'
if (( fail )); then echo 'RESULT: INCOMPLETE — review FAIL checks; no deployments or production writes attempted'; exit 1; fi
echo 'RESULT: METADATA COLLECTION PASS — backup RESTORABILITY and Files recovery remain UNVERIFIED; no deployments or production writes attempted'
