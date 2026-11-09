#!/usr/bin/env bash
# 0040-FEAT Step 12: Windows-Cygwin orchestrator for the single guarded cutover.
# Invoke as a standalone Bash process, never `source` it into an interactive shell.
set -euo pipefail

MODE="${1:-}"
if [[ $# -ne 1 || ( "$MODE" != 'preflight' && "$MODE" != 'execute' ) ]]; then
    printf 'Usage: bash %s preflight|execute\n' "$0" >&2
    exit 2
fi

TOOL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FEATURE_DIR="$(cd "$TOOL_DIR/.." && pwd)"
DIARIES_DIR="$(cd "$FEATURE_DIR/../../.." && pwd)"
AUDITOR="$TOOL_DIR/step12-legacy-journal-transition.py"
LOGDIR="$FEATURE_DIR/evidence/Step 12/raw-logs"
mkdir -p "$LOGDIR"
LOG="$LOGDIR/step12-controlled-cutover-${MODE}-$(date -u +%Y%m%d-%H%M%S)-$$.txt"
exec > >(tee "$LOG") 2>&1

EXPECTED_BINARY='9be64295a6b6807df0fcd33d924b7a6549959f2a03dcab2953dcf0ac77fa6297'
EXPECTED_JOURNAL='e11483fe05c482894c2db6fc15ffa63164f6b9c3da831508e0a2990123b9f3f2'
EXPECTED_CANDIDATE='20261030-170009Z'
EXPECTED_PARENT='20261101-140039Z'
EXPECTED_PARENT_UUID='69ef9a57-50ff-9a4e-92ed-8f10560ab1f2'
SOURCE_STATE='/media/usb/@snapshots/.simple-agreed-parent.json'
RECEIVER_STATE='/@data/mars-received/.replication-state/.simple-agreed-parent.json'

PHASE='initial checks'
SOURCE_STOPPED='no'
finished() {
    local code=$?
    if (( code != 0 )); then
        printf '\nFAIL: %s (exit %s). Evidence: %s\n' "$PHASE" "$code" "$LOG" >&2
        if [[ "$SOURCE_STOPPED" == yes ]]; then
            printf '%s\n' 'ATTENTION: mars timer/service were stopped; do NOT restart the legacy job automatically.' >&2
            printf '%s\n' 'Preserve existing journal, snapshots, receipts and state files pending review.' >&2
        fi
    fi
}
trap finished EXIT

die() { printf 'REFUSED: %s\n' "$*" >&2; exit 1; }
step() { PHASE="$1"; printf '\n=== %s ===\n' "$PHASE"; }
require_text() { [[ "$1" == *"$2"* ]] || die "Missing expected evidence: $2"; }

step 'Windows Diaries checkout and packaging'
[[ -f "$AUDITOR" ]] || die "Missing audit utility: $AUDITOR (apply the revised transition ZIP first)"
command -v ssh >/dev/null || die 'ssh is unavailable in this Cygwin terminal'
command -v sha256sum >/dev/null || die 'sha256sum is unavailable'
cd "$DIARIES_DIR"
git rev-parse --show-toplevel
git branch --show-current
git rev-parse --short HEAD
git status --short
git submodule status
printf 'Audit utility: '; sha256sum "$AUDITOR"
printf 'Action: %s\n' "$MODE"

step 'Re-audit initial read-only source parent on mars'
source_audit="$(ssh mars 'sudo -n python3 - audit source' < "$AUDITOR")" || die 'Source audit failed'
printf '%s\n' "$source_audit"
require_text "$source_audit" 'PASS: read-only source audit; no state changed'
require_text "$source_audit" "Proposed common parent $EXPECTED_PARENT: UUID=$EXPECTED_PARENT_UUID Received UUID=- Flags=readonly"
require_text "$source_audit" 'ABSENT (expected before bootstrap)'

step 'Audit legacy candidate Btrfs identity and pin historical receipt bytes on backup'
receiver_audit="$(ssh backup 'sudo -n python3 - audit receiver' < "$AUDITOR")" || die 'Receiver audit failed'
printf '%s\n' "$receiver_audit"
require_text "$receiver_audit" 'PASS: read-only receiver audit; no state changed'
require_text "$receiver_audit" "Proposed common parent $EXPECTED_PARENT:"
require_text "$receiver_audit" "Received UUID=$EXPECTED_PARENT_UUID Flags=readonly"
require_text "$receiver_audit" "sha256=$EXPECTED_JOURNAL"
require_text "$receiver_audit" "'timestamp': '$EXPECTED_CANDIDATE'"
require_text "$receiver_audit" 'Candidate Btrfs identity: VERIFIED (readonly; independent of receipt claims)'
require_text "$receiver_audit" 'Nonce-bound private staged object: ABSENT'
require_text "$receiver_audit" 'Nonce-bound ownership sidecar: ABSENT'
require_text "$receiver_audit" 'Legacy marker .receiver-prune-pending.json: ABSENT'
require_text "$receiver_audit" 'Legacy marker .agreed-parent-provisional.json: ABSENT'
require_text "$receiver_audit" 'Staging bound: False'
require_text "$receiver_audit" 'Publication witnessed: False'
require_text "$receiver_audit" 'Simplified parent /@data/mars-received/.replication-state/.simple-agreed-parent.json: ABSENT'
receipt_sha="$(printf '%s\n' "$receiver_audit" | awk '$1=="Candidate" && $2=="receipt" && $3=="sha256:" {print $4}')"
[[ "$receipt_sha" =~ ^[0-9a-f]{64}$ ]] || die 'Audit did not provide a single valid receipt SHA-256'
printf 'Pinned completed-candidate receipt SHA-256: %s\n' "$receipt_sha"

step 'Confirm installed executable and old service configuration'
source_binary_hash="$(ssh mars 'sudo -n sha256sum /usr/local/bin/btrfs-simplified-replication' | awk '{print $1}')" || die 'mars installed SHA check failed'
receiver_binary_hash="$(ssh backup 'sudo -n sha256sum /usr/local/bin/btrfs-simplified-replication' | awk '{print $1}')" || die 'backup installed SHA check failed'
[[ "$source_binary_hash" == "$EXPECTED_BINARY" && "$receiver_binary_hash" == "$EXPECTED_BINARY" ]] || die 'Installed binary SHA-256 not the accepted version'
printf 'PASS: accepted binary hash on both hosts: %s\n' "$EXPECTED_BINARY"
service_exec="$(ssh mars 'systemctl show -p ExecStart --value btrfs-native-push.service')" || die 'Cannot inspect current service'
printf 'Current service ExecStart: %s\n' "$service_exec"
[[ "$service_exec" == *'/usr/local/bin/btrfs-native-push --latest'* && "$service_exec" != *'btrfs-simplified-replication'* ]] || die 'Source service is not the expected legacy configuration'
timer_enabled="$(ssh mars 'systemctl is-enabled btrfs-native-push.timer')" || die 'Cannot inspect timer enablement'
timer_active="$(ssh mars 'systemctl is-active btrfs-native-push.timer')" || die 'Cannot inspect timer activity'
service_active="$(ssh mars 'systemctl show -p ActiveState --value btrfs-native-push.service')" || die 'Cannot inspect service activity'
[[ "$timer_enabled" == enabled && "$timer_active" == active ]] || die 'Source timer not enabled and active as expected'
[[ "$service_active" == failed || "$service_active" == inactive ]] || die "Legacy service currently running or changing state: $service_active"
printf 'PASS: timer enabled/active; legacy service %s (not running)\n' "$service_active"

step 'Verify noninteractive transport and receiver prune configuration'
ssh mars 'sudo -n -u richard ssh -o BatchMode=yes -o ConnectTimeout=15 -p 39263 richard@10.254.22.1 "sudo -n true"' || die 'mars -> backup SSH/sudo transport refused'
ssh backup 'sudo -n python3 -c '\''import json; p="/etc/btrfs-snapshot-manager.json"; d=json.load(open(p)); print("receiver_prune_enabled:", d.get("receiver_prune_enabled")); assert d.get("receiver_prune_enabled") is False'\''' || die 'Receiver pruning not demonstrably disabled'

step 'Inspect first newer source candidate and existing receipt'
next_candidate="$(ssh mars "sudo -n find /media/usb/@snapshots/@data -mindepth 1 -maxdepth 1 -type d -printf '%f\n'" | grep -E '^[0-9]{8}-[0-9]{6}Z$' | LC_ALL=C sort | awk -v parent="$EXPECTED_PARENT" '$0 > parent && !found { print; found=1 }')" || die 'Cannot list the source snapshots'
[[ -n "$next_candidate" ]] || die 'No newer snapshot is available for the required controlled transfer'
printf 'First newer snapshot: %s\n' "$next_candidate"
receipt_exists="$(ssh backup "if sudo -n test -e /@data/mars-received/.replication-state/${next_candidate}.json || sudo -n test -L /@data/mars-received/.replication-state/${next_candidate}.json; then echo PRESENT; else echo ABSENT; fi")" || die 'Cannot inspect next-candidate legacy receipt'
[[ "$receipt_exists" == ABSENT ]] || die "Next candidate $next_candidate has a legacy receipt or an unexpected receipt status: $receipt_exists"
receiver_candidate_exists="$(ssh backup "if sudo -n test -e /@data/mars-received/@data/${next_candidate} || sudo -n test -L /@data/mars-received/@data/${next_candidate}; then echo PRESENT; else echo ABSENT; fi")" || die 'Cannot inspect next-candidate receiver object'
[[ "$receiver_candidate_exists" == ABSENT ]] || die "Next candidate $next_candidate already exists on backup; classify before claiming a fresh send/receive test"

printf '\nPASS: guarded cutover preflight completed. Historical receipt bytes and Btrfs parent were checked independently.\n'
if [[ "$MODE" == preflight ]]; then
    printf 'No state has been changed. Evidence: %s\n' "$LOG"
    exit 0
fi

step 'STOP legacy replication timer and service on mars'
SOURCE_STOPPED='yes'  # a partial stop also needs explicit operator attention
ssh mars 'sudo -n systemctl stop btrfs-native-push.timer && sudo -n systemctl stop btrfs-native-push.service' || die 'Could not stop existing source timer/service'
ssh mars '! systemctl is-active --quiet btrfs-native-push.timer && ! systemctl is-active --quiet btrfs-native-push.service' || die 'Source timer/service remained active'
printf 'PASS: legacy job stopped before journal retirement\n'

step 'Guarded archive of ONLY the obsolete legacy journal on backup'
ssh backup "sudo -n python3 - archive --expected-sha256 $EXPECTED_JOURNAL --expected-candidate $EXPECTED_CANDIDATE --allow-completed-candidate --expected-receipt-sha256 $receipt_sha" < "$AUDITOR" || die 'Guarded journal archive failed; inspect journal and locks before proceeding'
[[ "$(ssh backup 'sudo -n test ! -e /@data/mars-received/.replication-state/.agreed-parent-transfer-pending.json && echo absent')" == absent ]] || die 'Journal still active after archive'
printf 'PASS: obsolete legacy journal archived; existing snapshots and receipts preserved unchanged\n'

step 'Bootstrap new agreed parent on both hosts via source sender'
ssh mars "sudo -n /usr/local/bin/btrfs-simplified-replication sender bootstrap --snapshot $EXPECTED_PARENT" || die 'Bootstrap failed; preserve any receiver-only state and inspect'
source_state="$(ssh mars "sudo -n cat $SOURCE_STATE")" || die 'Cannot read source new state'
receiver_state="$(ssh backup "sudo -n cat $RECEIVER_STATE")" || die 'Cannot read receiver new state'
printf 'Source initial state: %s\nReceiver initial state: %s\n' "$source_state" "$receiver_state"
[[ "$source_state" == "$receiver_state" ]] || die 'Initial parent state mismatch'
require_text "$source_state" "\"timestamp\": \"$EXPECTED_PARENT\""
require_text "$source_state" "\"uuid\": \"$EXPECTED_PARENT_UUID\""
require_text "$source_state" '"prior": null'
printf 'PASS: source and receiver initial parent are equal\n'

step 'Run ONE controlled simplified replication cycle'
# A failure leaves the old timer stopped. Never run the legacy sender blindly.
ssh mars 'sudo -n /usr/local/bin/btrfs-simplified-replication sender cycle' || die 'Manual cycle failed; do not enable unattended schedule'
source_state="$(ssh mars "sudo -n cat $SOURCE_STATE")" || die 'Cannot read source after cycle'
receiver_state="$(ssh backup "sudo -n cat $RECEIVER_STATE")" || die 'Cannot read receiver after cycle'
printf 'Source state after cycle: %s\nReceiver state after cycle: %s\n' "$source_state" "$receiver_state"
[[ "$source_state" == "$receiver_state" ]] || die 'Source and receiver disagree after manual cycle'
require_text "$source_state" "\"prior\": {\"timestamp\": \"$EXPECTED_PARENT\""
[[ "$source_state" != *'"prior": null'* ]] || die 'No snapshot transferred; prior was not advanced'
printf '\nPASS: first simplified cycle completed with equal source/receiver agreed-parent records.\n'
printf '%s\n' 'The old timer remains STOPPED. Do not enable it until the Playbooks cutover preview is reviewed.'
printf 'Evidence: %s\n' "$LOG"
