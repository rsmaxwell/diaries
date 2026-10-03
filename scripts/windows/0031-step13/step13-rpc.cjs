'use strict';

const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const ROOT = path.resolve(__dirname, '../../..');
const mqtt = require(path.join(ROOT, 'diaries-client', 'node_modules', 'mqtt'));
const CLIENT_CONFIG = path.join(ROOT, 'diaries-client', 'public', 'assets', 'config.json');
const FIXTURE_BYTES = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGNgYGAAAAAEAAH2FzhVAAAAAElFTkSuQmCC',
  'base64'
);
const FIXTURE_SHA256 = crypto.createHash('sha256').update(FIXTURE_BYTES).digest('hex');
// This fixture is deliberately a complete CRC-valid PNG because uploadFile performs strict image inspection.

function fail(message) {
  throw new Error(`0031 Step 13: ${message}`);
}

function loadClientConfig() {
  if (!fs.existsSync(CLIENT_CONFIG)) fail(`client MQTT config not found: ${CLIENT_CONFIG}`);
  const config = JSON.parse(fs.readFileSync(CLIENT_CONFIG, 'utf8'));
  return {
    brokerUrl: process.env.DIARIES_STEP13_BROKER_URL || config.brokerDirectUrl,
    brokerUsername: process.env.DIARIES_STEP13_BROKER_USERNAME || config.username,
    brokerPassword: process.env.DIARIES_STEP13_BROKER_PASSWORD || config.password,
    observerUsername: process.env.DIARIES_STEP13_OBSERVER_USERNAME || '',
    observerPassword: process.env.DIARIES_STEP13_OBSERVER_PASSWORD || '',
    responderOrigin: process.env.DIARIES_STEP13_RESPONDER_ORIGIN || 'http://127.0.0.1:8081'
  };
}

async function connect(label, identity = 'rpc') {
  const config = loadClientConfig();
  if (!config.brokerUrl || !config.brokerUsername || !config.brokerPassword) {
    fail('broker URL/username/password is missing from the client config or Step 13 overrides');
  }
  let username = config.brokerUsername;
  let password = config.brokerPassword;
  if (identity === 'observer') {
    username = config.observerUsername;
    password = config.observerPassword;
    if (!username || !password) {
      fail('retained-state observer credentials were not supplied by the PowerShell wrapper');
    }
  }
  const client = await mqtt.connectAsync(config.brokerUrl, {
    protocolVersion: 5,
    username,
    password,
    clean: true,
    clientId: `step13-${label}-${crypto.randomUUID()}`,
    connectTimeout: 10000,
    reconnectPeriod: 0
  });
  return { client, config };
}

function parseStatus(packet) {
  const raw = packet.properties?.userProperties?.status;
  if (!raw) fail('RPC response did not include the status user property');
  return JSON.parse(Array.isArray(raw) ? raw[0] : raw);
}

async function rpcSession() {
  const { client, config } = await connect('rpc');
  const responseTopic = `diaries/rpc/${client.options.clientId}/response`;
  await client.subscribeAsync(responseTopic, { qos: 1 });
  const pending = new Map();
  client.on('message', (topic, bytes, packet) => {
    const correlation = packet.properties?.correlationData?.toString();
    if (topic !== responseTopic || !correlation || !pending.has(correlation)) return;
    const entry = pending.get(correlation);
    pending.delete(correlation);
    clearTimeout(entry.timer);
    let payload = null;
    if (bytes.length) payload = JSON.parse(bytes.toString('utf8'));
    entry.resolve({ status: parseStatus(packet), payload });
  });
  let accessToken = null;
  async function rpc(fn, args) {
    const correlation = crypto.randomUUID();
    const reply = new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        pending.delete(correlation);
        reject(new Error(`${fn} RPC timeout`));
      }, 15000);
      pending.set(correlation, { resolve, reject, timer });
    });
    const properties = {
      responseTopic,
      correlationData: Buffer.from(correlation)
    };
    if (accessToken) properties.userProperties = { accessToken };
    await client.publishAsync('diaries/rpc/request', JSON.stringify({ function: fn, args }), {
      qos: 1,
      properties
    });
    return reply;
  }
  async function signin() {
    const username = process.env.DIARIES_STEP13_APP_USERNAME;
    const password = process.env.DIARIES_STEP13_APP_PASSWORD;
    if (!username || !password) fail('application username/password was not supplied by the PowerShell wrapper');
    const reply = await rpc('signin', { username, password, sessionId: crypto.randomUUID() });
    if (reply.status.code !== 200 || !reply.payload?.accessToken) {
      fail(`signin failed with RPC status ${reply.status.code}`);
    }
    accessToken = reply.payload.accessToken;
  }
  return { client, config, rpc, signin };
}

async function retainedSnapshot(topic, waitMs = 1300) {
  // Retained Image catalogue state is deliberately not readable by the Angular
  // diaries-client MQTT identity. Use the responder MQTT identity supplied only
  // through the wrapper environment; never write those credentials to evidence.
  const { client } = await connect('observer', 'observer');
  const messages = [];
  client.on('message', (receivedTopic, bytes, packet) => {
    if (receivedTopic !== topic) return;
    messages.push({
      topic: receivedTopic,
      retained: Boolean(packet.retain),
      qos: packet.qos,
      payloadBytes: bytes.length,
      payload: bytes.length ? bytes.toString('utf8') : ''
    });
  });
  const grants = await client.subscribeAsync(topic, { qos: 1 });
  if (Array.isArray(grants) && grants.some(grant => Number(grant.qos) >= 128)) {
    fail(`retained-state observer is not authorised to subscribe to ${topic}`);
  }
  await new Promise(resolve => setTimeout(resolve, waitMs));
  await client.endAsync();
  return messages;
}

async function httpSnapshot(relativeUrl, expectedBytes) {
  const { responderOrigin } = loadClientConfig();
  const url = new URL(relativeUrl, responderOrigin).href;
  let response;
  try {
    response = await fetch(url);
  } catch (error) {
    return { url, networkError: String(error?.cause?.message || error?.message || error) };
  }
  const bytes = Buffer.from(await response.arrayBuffer());
  return {
    url,
    status: response.status,
    contentType: response.headers.get('content-type'),
    bytes: bytes.length,
    sha256: response.ok ? crypto.createHash('sha256').update(bytes).digest('hex') : null,
    expectedSha256: expectedBytes ? crypto.createHash('sha256').update(expectedBytes).digest('hex') : null
  };
}

async function upload(name, subdir) {
  const session = await rpcSession();
  try {
    await session.signin();
    const args = {
      name,
      subdir,
      contentType: 'image/png',
      size: FIXTURE_BYTES.length,
      bytes: FIXTURE_BYTES.toString('base64'),
      sha256: FIXTURE_SHA256
    };
    const reply = await session.rpc('uploadFile', args);
    if (reply.status.code !== 200 || !reply.payload?.imageId || !reply.payload?.image) {
      fail(`uploadFile failed with RPC status ${reply.status.code} (${reply.status.message || 'no status message'})`);
    }
    if (reply.payload.url !== `/files/${subdir}/${name}`) {
      fail(`uploadFile returned unstable public URL '${reply.payload.url}'`);
    }
    const overwrite = await session.rpc('uploadFile', { ...args, overwrite: true });
    if (overwrite.status.code !== 409) {
      fail(`catalogued overwrite safety check expected 409 but received ${overwrite.status.code}`);
    }
    const imageId = reply.payload.imageId;
    const topic = `diaries/images/${imageId}`;
    const retained = await retainedSnapshot(topic);
    const nonEmpty = retained.filter(message => message.payloadBytes > 0);
    if (nonEmpty.length !== 1) fail(`expected one retained Image message on ${topic}; found ${nonEmpty.length}`);
    const retainedPayload = JSON.parse(nonEmpty[0].payload);
    if (Number(retainedPayload.id) !== Number(imageId)) fail('retained Image payload id does not match upload response');
    const http = await httpSnapshot(reply.payload.url, FIXTURE_BYTES);
    if (http.status !== 200 || http.sha256 !== FIXTURE_SHA256) {
      fail(`static ${reply.payload.url} byte verification failed`);
    }
    return {
      operation: 'upload',
      fixture: { name, subdir, relativePath: `${subdir}/${name}`, size: FIXTURE_BYTES.length, sha256: FIXTURE_SHA256 },
      uploadReply: reply,
      overwriteAttempt: overwrite,
      retained,
      http,
      imageId,
      imageTopic: topic
    };
  } finally {
    await session.client.endAsync().catch(() => {});
  }
}

async function observe(state) {
  const topic = `diaries/images/${state.imageId}`;
  const retained = await retainedSnapshot(topic);
  const nonEmpty = retained.filter(message => message.payloadBytes > 0);
  if (nonEmpty.length !== 1) fail(`expected retained Image state on ${topic}; found ${nonEmpty.length}`);
  const payload = JSON.parse(nonEmpty[0].payload);
  if (Number(payload.id) !== Number(state.imageId) || payload.relativePath !== state.relativePath) {
    fail('retained Image snapshot does not identify the Step 13 fixture');
  }
  const http = await httpSnapshot(state.publicUrl, FIXTURE_BYTES);
  if (http.status !== 200 || http.sha256 !== state.sha256) fail('second-mode HTTP byte check failed');
  return { operation: 'observe', imageTopic: topic, retained, http };
}

async function remove(state) {
  const observer = await connect('delete-observer', 'observer');
  const topic = `diaries/images/${state.imageId}`;
  const live = [];
  observer.client.on('message', (receivedTopic, bytes, packet) => {
    if (receivedTopic === topic) live.push({ topic, retained: Boolean(packet.retain), qos: packet.qos, payloadBytes: bytes.length });
  });
  const grants = await observer.client.subscribeAsync(topic, { qos: 1 });
  if (Array.isArray(grants) && grants.some(grant => Number(grant.qos) >= 128)) {
    fail(`retained-state observer is not authorised to subscribe to ${topic}`);
  }
  await new Promise(resolve => setTimeout(resolve, 450));
  live.length = 0;

  const session = await rpcSession();
  try {
    await session.signin();
    const reply = await session.rpc('deleteImage', { name: state.name, subdir: state.subdir });
    if (reply.status.code !== 200 || reply.payload?.deleted !== true || Number(reply.payload?.id) !== Number(state.imageId)) {
      fail(`deleteImage failed or returned unexpected identity (RPC status ${reply.status.code})`);
    }
    await new Promise(resolve => setTimeout(resolve, 700));
    if (!live.some(message => message.payloadBytes === 0)) fail('live retained-topic tombstone was not observed after deleteImage');
    await observer.client.endAsync();
    const afterRetained = await retainedSnapshot(topic);
    if (afterRetained.length !== 0) fail('deleted Image topic still has retained state');
    const http = await httpSnapshot(state.publicUrl, null);
    if (!http.networkError && http.status === 200) fail('deleted Image is still served with HTTP 200');
    return { operation: 'delete', deleteReply: reply, liveTombstoneMessages: live, retainedAfterDelete: afterRetained, httpAfterDelete: http };
  } finally {
    await session.client.endAsync().catch(() => {});
    await observer.client.endAsync().catch(() => {});
  }
}


async function retainedCheck(imageId) {
  const topic = `diaries/images/${imageId}`;
  const retained = await retainedSnapshot(topic);
  const nonEmpty = retained.filter(message => message.payloadBytes > 0);
  return { operation: 'retained-check', imageId: Number(imageId), imageTopic: topic, retained, nonEmptyCount: nonEmpty.length };
}

async function cleanup(name, subdir, expectedId) {
  const session = await rpcSession();
  const topic = `diaries/images/${expectedId}`;
  try {
    await session.signin();
    const beforeRetained = await retainedSnapshot(topic);
    const reply = await session.rpc('deleteImage', { name, subdir });
    if (reply.status.code !== 200 || reply.payload?.deleted !== true || Number(reply.payload?.id) !== Number(expectedId)) {
      fail(`recovery deleteImage failed or returned unexpected identity (RPC status ${reply.status.code})`);
    }
    const afterRetained = await retainedSnapshot(topic);
    if (afterRetained.length !== 0) fail(`recovery cleanup left retained Image state on ${topic}`);
    const publicUrl = `/files/${subdir}/${name}`;
    const http = await httpSnapshot(publicUrl, null);
    if (!http.networkError && http.status === 200) fail(`recovery cleanup left ${publicUrl} available with HTTP 200`);
    return { operation: 'cleanup', expectedId: Number(expectedId), imageTopic: topic, beforeRetained, deleteReply: reply, retainedAfterDelete: afterRetained, httpAfterDelete: http };
  } finally {
    await session.client.endAsync().catch(() => {});
  }
}

async function main() {
  const [command, arg1, arg2, arg3] = process.argv.slice(2);
  let result;
  if (command === 'upload') {
    if (!arg1 || !arg2) fail('usage: step13-rpc.cjs upload <name> <subdir>');
    result = await upload(arg1, arg2);
  } else if (command === 'observe') {
    if (!arg1) fail('usage: step13-rpc.cjs observe <state.json>');
    result = await observe(JSON.parse(fs.readFileSync(arg1, 'utf8')));
  } else if (command === 'delete') {
    if (!arg1) fail('usage: step13-rpc.cjs delete <state.json>');
    result = await remove(JSON.parse(fs.readFileSync(arg1, 'utf8')));
  } else if (command === 'cleanup') {
    if (!arg1 || !arg2 || !arg3) fail('usage: step13-rpc.cjs cleanup <name> <subdir> <imageId>');
    result = await cleanup(arg1, arg2, arg3);
  } else if (command === 'retained-check') {
    if (!arg1) fail('usage: step13-rpc.cjs retained-check <imageId>');
    result = await retainedCheck(arg1);
  } else {
    fail('command must be upload, observe, delete, cleanup or retained-check');
  }
  process.stdout.write(JSON.stringify(result, null, 2) + '\n');
}

main().catch(error => {
  process.stderr.write(`${error.stack || error}\n`);
  process.exitCode = 1;
});
