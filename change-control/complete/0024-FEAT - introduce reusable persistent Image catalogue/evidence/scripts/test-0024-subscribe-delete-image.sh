mosquitto_sub \
  -h pluto.rsmaxwell.co.uk \
  -p 1883 \
  -V mqttv5 \
  -i "${CLIENT_ID}" \
  -u admin \
  -P "${MQTT_ADMIN_PASSWORD}" \
  -t "diaries/rpc/0024-delete-test/response" \
  -v
