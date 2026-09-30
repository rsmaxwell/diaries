/* 0026 Step 13: bounded, diagnostic MQTT v5 retained Fragment/Image snapshots. */
'use strict';
const crypto = require('node:crypto');

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
async function withTimeout(promise, timeoutMs, label) {
  let timer;
  try {
    return await Promise.race([promise, new Promise((_, reject) => {
      timer = setTimeout(() => reject(Error(`${label} timed out after ${timeoutMs}ms`)), timeoutMs);
    })]);
  } finally { clearTimeout(timer); }
}

/**
 * Collect only the retained metadata that Step 13 asserts. A separate publisher
 * sends the QoS-1 barrier after the subscriber has received all three SUBACKs:
 * this avoids coupling the barrier publish to a subscriber receiving thousands
 * of retained publications. The non-overlapping barrier topic is outside the
 * observed topic filters. The resulting stream is complete when it arrives.
 *
 * Dependencies are injected to make ACL, replay and missing-marker paths
 * independently testable without Docker or application credentials.
 */
function makeRetainedSnapshot({ connect, sha, write, timeoutMs = 120_000, ackTimeoutMs = 20_000 }) {
  if (typeof connect !== 'function' || typeof sha !== 'function' || typeof write !== 'function') {
    throw new TypeError('connect, sha and write are required');
  }
  return async function retainedSnapshot(label) {
    const marker = 'diaries-sync/step13/' + crypto.randomUUID();
    const retained = {};
    const diagnosticName = label + '-mqtt-diagnostics.json';
    const diag = {
      label, startedAtUtc: new Date().toISOString(), marker,
      snapshotFilters: ['diaries/fragments/+', 'diaries/images/+'],
      subscriptions: [], markerPublished: false, markerReceived: false,
      replayMessages: 0, liveMessages: 0, fragmentTopics: 0, imageTopics: 0,
      subscriberDisconnect: null, subscriberError: null, publisherError: null,
      expectedBarrierTimeoutMs: timeoutMs, ackTimeoutMs
    };
    let subscriber, publisher, markerReceived = false, closedByUs = false, failure;
    try {
      subscriber = await connect('diaries-responder');
      subscriber.on('message', (topic, bytes, packet) => {
        if (topic === marker) {
          markerReceived = true;
          diag.markerReceived = true;
          diag.markerReceivedAtUtc = new Date().toISOString();
          return;
        }
        if (!packet?.retain) { diag.liveMessages++; return; }
        diag.replayMessages++;
        if (bytes.length === 0) { delete retained[topic]; return; }
        try {
          retained[topic] = { sha256: sha(bytes), payload: JSON.parse(bytes) };
        } catch (error) {
          failure = Error(`Invalid retained JSON on ${topic}: ${error.message}`);
        }
      });
      subscriber.on('error', error => {
        diag.subscriberError = error.message;
        failure = error;
      });
      subscriber.on('close', () => {
        if (!closedByUs && !markerReceived) {
          diag.subscriberDisconnect = 'closed before barrier';
          failure = Error('snapshot subscriber disconnected before the barrier');
        }
      });

      // The publisher must be another client/connection, as in responder's
      // Synchronise.awaitDrained. Both users have the same fixture ACL rights.
      publisher = await connect('diaries-responder');
      publisher.on('error', error => { diag.publisherError = error.message; failure = error; });
      for (const topic of [marker, ...diag.snapshotFilters]) {
        const granted = await withTimeout(subscriber.subscribeAsync(topic, { qos: 1 }), ackTimeoutMs, `QoS-1 SUBACK for ${topic}`);
        diag.subscriptions.push({ topic, granted });
        if (!Array.isArray(granted) || !granted.some(g => g.topic === topic && g.qos === 1)) {
          throw Error(`QoS-1 SUBACK was not granted for ${topic}: ${JSON.stringify(granted)}`);
        }
      }
      // SUBACKs above precede this publication; the broker queues the QoS-1
      // marker after the retained messages from both non-overlapping filters.
      await withTimeout(publisher.publishAsync(marker, 'step13-barrier', { qos: 1, retain: false }), ackTimeoutMs, 'QoS-1 drain-marker PUBACK');
      diag.markerPublished = true;
      diag.markerPublishedAtUtc = new Date().toISOString();
      const deadline = Date.now() + timeoutMs;
      while (!markerReceived) {
        if (failure) throw failure;
        if (Date.now() >= deadline) {
          throw Error(`barrier was not received in ${timeoutMs}ms (received ${diag.replayMessages} retained, ${diag.liveMessages} live messages)`);
        }
        await sleep(50);
      }
      if (failure) throw failure;
      diag.fragmentTopics = Object.keys(retained).filter(t => t.startsWith('diaries/fragments/')).length;
      diag.imageTopics = Object.keys(retained).filter(t => t.startsWith('diaries/images/')).length;
      diag.status = 'PASSED';
      write(label + '.json', retained);
      return retained;
    } catch (error) {
      diag.status = 'FAILED';
      diag.failure = error.message;
      throw new Error(`retained snapshot ${label}: ${error.message}; see ${diagnosticName}`, { cause: error });
    } finally {
      closedByUs = true;
      diag.finishedAtUtc = new Date().toISOString();
      diag.fragmentTopics = Object.keys(retained).filter(t => t.startsWith('diaries/fragments/')).length;
      diag.imageTopics = Object.keys(retained).filter(t => t.startsWith('diaries/images/')).length;
      diag.subscriberConnectedAtFinish = Boolean(subscriber?.connected);
      diag.publisherConnectedAtFinish = Boolean(publisher?.connected);
      // Don't leave a queue-draining snapshot subscriber alive after a failure.
      for (const client of [subscriber, publisher]) {
        if (client) {
          try { await client.endAsync(true); }
          catch (error) { (diag.cleanupErrors ??= []).push(error.message); }
        }
      }
      write(diagnosticName, diag);
    }
  };
}

module.exports = { makeRetainedSnapshot };
