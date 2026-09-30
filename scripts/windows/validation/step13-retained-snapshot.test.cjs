/* Run: node --test scripts/windows/validation/step13-retained-snapshot.test.cjs */
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const { EventEmitter } = require('node:events');
const { makeRetainedSnapshot } = require('./step13-retained-snapshot.cjs');

class FakeBroker {
  constructor(initial = {}) { this.retained = new Map(Object.entries(initial)); this.clients = []; this.deniedTopic = null; this.stalledTopic = null; this.dropMarkers = false; }
  connect = async () => {
    const broker = this;
    class Client extends EventEmitter {
      constructor() { super(); this.connected = true; this.filters = []; this.pending = []; this.pumping = false; }
      enqueue(topic, payload, retain) {
        this.pending.push([topic, payload, retain]);
        if (!this.pumping) {
          this.pumping = true;
          setImmediate(() => {
            for (const [t,p,r] of this.pending.splice(0)) if (this.connected) this.emit('message', t, Buffer.from(p), {retain:r});
            this.pumping = false;
          });
        }
      }
      async subscribeAsync(topic, {qos}) {
        if (topic === broker.deniedTopic) return [{topic, qos:128}];
        if (topic === broker.stalledTopic) return new Promise(()=>{});
        this.filters.push(topic);
        for (const [name, payload] of broker.retained) if (matches(topic,name)) this.enqueue(name, payload, true);
        return [{topic,qos}];
      }
      async publishAsync(topic, payload, {qos,retain}) {
        assert.equal(qos, 1);
        assert.equal(retain, false);
        if (!broker.dropMarkers) {
          for (const c of broker.clients) if (c !== this && c.filters.some(f => matches(f,topic))) c.enqueue(topic,payload,false);
        }
      }
      async endAsync() { this.connected = false; }
    }
    const client = new Client(); this.clients.push(client); return client;
  };
}
function matches(filter, topic) {
  const a=filter.split('/'), b=topic.split('/');
  if (a.length!==b.length) return false;
  return a.every((v,i)=>v==='+'||v===b[i]);
}
function fixture(broker, timeoutMs=500) {
  const evidence = new Map();
  const snapshot = makeRetainedSnapshot({
    connect: broker.connect,
    sha: bytes => crypto.createHash('sha256').update(bytes).digest('hex'),
    write: (name,value) => evidence.set(name,structuredClone(value)), timeoutMs, ackTimeoutMs:75
  });
  return { snapshot, evidence };
}

test('5376-topic retained replay drains before the independent QoS-1 barrier', async () => {
  const retained={};
  for(let i=1;i<=5376;i++) retained['diaries/fragments/'+i] = JSON.stringify({id:i,type:'IMAGE'});
  retained['diaries/images/23'] = JSON.stringify({id:23,relativePath:'nested/pic.png'});
  const broker=new FakeBroker(retained);
  const {snapshot,evidence}=fixture(broker,1500);
  const result=await snapshot('large');
  assert.equal(Object.keys(result).length,5377);
  assert.deepEqual(result['diaries/images/23'].payload,{id:23,relativePath:'nested/pic.png'});
  const diag=evidence.get('large-mqtt-diagnostics.json');
  assert.equal(diag.status,'PASSED');
  assert.equal(diag.markerReceived,true);
  assert.equal(diag.replayMessages,5377);
  assert.deepEqual(diag.snapshotFilters,['diaries/fragments/+','diaries/images/+']);
  assert.equal(broker.clients.length,2,'barrier publisher must use a different connection');
  assert(broker.clients.every(c=>!c.connected));
});

test('denied SUBACK fails immediately with diagnostic evidence instead of waiting for marker', async () => {
  const broker = new FakeBroker(); broker.deniedTopic = 'diaries/images/+';
  const {snapshot,evidence}=fixture(broker,1500);
  await assert.rejects(snapshot('denied'),/QoS-1 SUBACK was not granted.*diaries\/images/);
  const diag=evidence.get('denied-mqtt-diagnostics.json');
  assert.equal(diag.status,'FAILED'); assert.equal(diag.markerPublished,false);
  assert(broker.clients.every(c=>!c.connected));
});

test('missing barrier fails with received-message counts and retains partial diagnostics', async () => {
  const broker = new FakeBroker({'diaries/images/42':JSON.stringify({id:42})}); broker.dropMarkers=true;
  const {snapshot,evidence}=fixture(broker,100);
  await assert.rejects(snapshot('no-barrier'),/barrier was not received.*1 retained/);
  const diag=evidence.get('no-barrier-mqtt-diagnostics.json');
  assert.equal(diag.status,'FAILED'); assert.equal(diag.markerReceived,false);
  assert.equal(diag.replayMessages,1);
  assert(broker.clients.every(c=>!c.connected));
});

test('missing SUBACK terminates promptly and reports the blocked topic', async () => {
  const broker = new FakeBroker(); broker.stalledTopic = 'diaries/images/+';
  const {snapshot,evidence}=fixture(broker,1500);
  await assert.rejects(snapshot('stalled-suback'),/QoS-1 SUBACK.*diaries\/images.*timed out/);
  const diag=evidence.get('stalled-suback-mqtt-diagnostics.json');
  assert.equal(diag.status,'FAILED'); assert.equal(diag.markerPublished,false);
  assert(broker.clients.every(c=>!c.connected));
});
