
mosquitto_pub \
  -h pluto.rsmaxwell.co.uk \
  -p 1883 \
  -V mqttv5 \
  -u admin \
  -P "${MQTT_ADMIN_PASSWORD}" \
  -t "diaries/rpc/request" \
  -m '{"function":"deleteFile","args":{"subdir":"diary-1830/images","name":"img2221.jpg"}}' \
  -D PUBLISH response-topic 'diaries/rpc/${CLIENT_ID}/response' \
  -D PUBLISH correlation-data '0024-delete-test-1' \
  -D PUBLISH user-property accessToken 'YOUR_DIARIES_ACCESS_TOKEN'
