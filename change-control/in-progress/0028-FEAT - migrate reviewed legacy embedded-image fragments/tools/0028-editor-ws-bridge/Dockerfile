# Dedicated, disposable, backend-only WebSocket-to-MQTT TCP bridge for 0028.
# No MQTT port or WebSocket listener is published on the Windows host.
FROM node:20-alpine
WORKDIR /opt/diaries-0028-bridge
RUN npm install --omit=dev --ignore-scripts --no-audit --no-fund --no-save ws@8.18.3 \
    && chown -R node:node /opt/diaries-0028-bridge
COPY --chown=node:node bridge.js ./bridge.js
USER node
EXPOSE 9001
CMD ["node", "bridge.js"]
