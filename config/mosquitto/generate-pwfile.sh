#!/bin/sh

set -e

SOURCE_FILE="/work/pwfile.txt"
TEMP_FILE="/tmp/pwfile.txt"

cp "${SOURCE_FILE}" "${TEMP_FILE}"
chmod 0600 "${TEMP_FILE}"

mosquitto_passwd -U "${TEMP_FILE}"

cp "${TEMP_FILE}" "${SOURCE_FILE}"
chown 1883:1883 "${SOURCE_FILE}"
chmod 0600 "${SOURCE_FILE}"
