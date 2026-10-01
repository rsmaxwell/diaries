#!/usr/bin/env bash
set -euo pipefail

# 0024 production closure test:
# Attempt to delete a catalogued image through the generic deleteFile MQTT RPC.
#
# Expected result:
#   409 "Catalogued file cannot be deleted"
# and the physical image must still exist afterwards.
#
# Run from the Diaries production project directory, e.g.
#   cd /home/richard/projects/diaries
#   ./scripts/test-0024-guarded-delete.sh

MQTT_CONTAINER="${MQTT_CONTAINER:-diaries-mosquitto}"
CLIENT_CONFIG="${CLIENT_CONFIG:-config/client/config.json}"

TARGET_SUBDIR="diary-1830/images"
TARGET_NAME="img2221.jpg"
TARGET_PATH="/data/files/${TARGET_SUBDIR}/${TARGET_NAME}"

REQUEST_TOPIC="diaries/rpc/request"

die() {
    echo "ERROR: $*" >&2
    exit 1
}

command -v jq >/dev/null 2>&1 || die "jq is required on the host"
docker inspect "$MQTT_CONTAINER" >/dev/null 2>&1 || die "MQTT container '$MQTT_CONTAINER' is not available"
docker inspect diaries-responder >/dev/null 2>&1 || die "Responder container 'diaries-responder' is not available"
[[ -r "$CLIENT_CONFIG" ]] || die "Cannot read $CLIENT_CONFIG"

MQTT_USER="$(jq -r '.username // empty' "$CLIENT_CONFIG")"
MQTT_PASSWORD="$(jq -r '.password // empty' "$CLIENT_CONFIG")"

[[ -n "$MQTT_USER" ]] || die "MQTT username not found in $CLIENT_CONFIG"
[[ -n "$MQTT_PASSWORD" ]] || die "MQTT password not found in $CLIENT_CONFIG"

if ! docker exec diaries-responder test -f "$TARGET_PATH"; then
    die "Target image does not exist before test: $TARGET_PATH"
fi

DIARIES_USERNAME="${DIARIES_USERNAME:-richard}"
read -r -p "Diaries username [$DIARIES_USERNAME]: " entered_username
if [[ -n "$entered_username" ]]; then
    DIARIES_USERNAME="$entered_username"
fi

read -r -s -p "Diaries password: " DIARIES_PASSWORD
echo
[[ -n "$DIARIES_PASSWORD" ]] || die "No Diaries password supplied"

new_id() {
    if command -v uuidgen >/dev/null 2>&1; then
        uuidgen | tr '[:upper:]' '[:lower:]'
    else
        printf '%s-%s-%s\n' "$(date +%s)" "$$" "$RANDOM"
    fi
}

mqtt_sub_once() {
    local topic="$1"
    local format="$2"
    local outfile="$3"

    docker exec "$MQTT_CONTAINER" \
        mosquitto_sub \
        -h localhost -p 1883 \
        -V mqttv5 \
        -u "$MQTT_USER" -P "$MQTT_PASSWORD" \
        -t "$topic" \
        -C 1 -W 15 \
        -F "$format" >"$outfile" &
    SUB_PID=$!

    # Give the subscription time to be acknowledged before publishing.
    sleep 0.5
}

mqtt_publish() {
    local reply_topic="$1"
    local correlation="$2"
    local payload="$3"
    local access_token="${4:-}"

    local args=(
        mosquitto_pub
        -h localhost -p 1883
        -V mqttv5
        -u "$MQTT_USER" -P "$MQTT_PASSWORD"
        -t "$REQUEST_TOPIC"
        -q 0
        -m "$payload"
        -D PUBLISH response-topic "$reply_topic"
        -D PUBLISH correlation-data "$correlation"
    )

    if [[ -n "$access_token" ]]; then
        args+=( -D PUBLISH user-property accessToken "$access_token" )
    fi

    docker exec "$MQTT_CONTAINER" "${args[@]}"
}

TMPDIR_TEST="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_TEST"' EXIT

echo
echo "1. Signing in to obtain a short-lived access token..."

SESSION_ID="$(new_id)"
SIGNIN_CORR="$(new_id)"
SIGNIN_REPLY="diaries/rpc/0024-delete-test-signin-$$/response"
SIGNIN_PAYLOAD="$(
    jq -cn \
        --arg username "$DIARIES_USERNAME" \
        --arg password "$DIARIES_PASSWORD" \
        --arg sessionId "$SESSION_ID" \
        '{function:"signin",args:{username:$username,password:$password,sessionId:$sessionId}}'
)"

SIGNIN_OUT="$TMPDIR_TEST/signin.out"
mqtt_sub_once "$SIGNIN_REPLY" '%p' "$SIGNIN_OUT"
mqtt_publish "$SIGNIN_REPLY" "$SIGNIN_CORR" "$SIGNIN_PAYLOAD"
wait "$SUB_PID" || die "Timed out waiting for signin response"

ACCESS_TOKEN="$(jq -r '.accessToken // empty' "$SIGNIN_OUT" 2>/dev/null || true)"
[[ -n "$ACCESS_TOKEN" ]] || {
    echo "Signin response:"
    cat "$SIGNIN_OUT"
    die "Signin did not return an access token"
}

echo "   Signin succeeded."

# Do not retain the password in a shell variable longer than necessary.
unset DIARIES_PASSWORD

echo
echo "2. Attempting generic deleteFile RPC for the catalogued image:"
echo "     $TARGET_SUBDIR/$TARGET_NAME"
echo
echo "   EXPECTED: responder rejects this with HTTP-style status 409."
echo "   The file must remain present."

DELETE_CORR="$(new_id)"
DELETE_REPLY="diaries/rpc/0024-delete-test-$$/response"
DELETE_PAYLOAD="$(
    jq -cn \
        --arg subdir "$TARGET_SUBDIR" \
        --arg name "$TARGET_NAME" \
        '{function:"deleteFile",args:{subdir:$subdir,name:$name}}'
)"

DELETE_OUT="$TMPDIR_TEST/delete.out"
mqtt_sub_once "$DELETE_REPLY" '%P\t%p' "$DELETE_OUT"
mqtt_publish "$DELETE_REPLY" "$DELETE_CORR" "$DELETE_PAYLOAD" "$ACCESS_TOKEN"
wait "$SUB_PID" || die "Timed out waiting for deleteFile response"

echo
echo "3. Raw responder reply:"
cat "$DELETE_OUT"
echo

STATUS_TEXT="$(sed -n 's/.*status:\({.*}\).*/\1/p' "$DELETE_OUT" | head -1 || true)"
STATUS_CODE=""
STATUS_MESSAGE=""

if [[ -n "$STATUS_TEXT" ]]; then
    STATUS_CODE="$(printf '%s' "$STATUS_TEXT" | jq -r '.code // empty' 2>/dev/null || true)"
    STATUS_MESSAGE="$(printf '%s' "$STATUS_TEXT" | jq -r '.message // empty' 2>/dev/null || true)"
fi

echo "4. Verifying physical image still exists..."
if docker exec diaries-responder test -f "$TARGET_PATH"; then
    echo "   PASS: file still exists:"
    echo "         $TARGET_PATH"
else
    echo "   FAIL: file has disappeared:"
    echo "         $TARGET_PATH"
    exit 2
fi

echo
if [[ "$STATUS_CODE" == "409" ]]; then
    echo "PASS: generic delete was correctly rejected with status 409."
    if [[ -n "$STATUS_MESSAGE" ]]; then
        echo "      Message: $STATUS_MESSAGE"
    fi
    echo
    echo "0024 guarded-delete production test PASSED."
    exit 0
fi

echo "WARNING: Could not confirm the expected 409 status from the formatted reply."
echo "         The physical file is still present, so no destructive delete occurred."
echo "         Review the raw reply above before recording the test as passed."
exit 3
