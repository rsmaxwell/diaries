'use strict';
const assert=require('node:assert/strict');
const test=require('node:test');
const { verifyRepositoryDigest } = require('./step4-rollout-rehearsal-checks.cjs');
const required='rsmaxwell/diaries-responder@sha256:d0f9224d759e06cabf26eb19722b3b417b170f7c6e3919c481acbe64db507695';
test('same immutable published digest permits different local image IDs',()=>{
  const data={id:'sha256:local-id-is-not-production-id',architecture:'amd64',digests:[required]};
  assert.equal(verifyRepositoryDigest(data,required,'Responder'),true);
});
test('optional docker.io prefix accepted',()=>{
  assert.equal(verifyRepositoryDigest({architecture:'amd64',digests:['docker.io/'+required]},required,'Responder'),true);
});
test('mismatched digest fails closed',()=>{
  assert.throws(()=>verifyRepositoryDigest({architecture:'amd64',digests:['rsmaxwell/diaries-responder@sha256:'+'a'.repeat(64)]},required,'Responder'),/digest mismatch/);
});
test('wrong platform fails closed',()=>{
  assert.throws(()=>verifyRepositoryDigest({architecture:'arm64',digests:[required]},required,'Responder'),/amd64/);
});
test('no published repository digest fails closed',()=>{
  assert.throws(()=>verifyRepositoryDigest({architecture:'amd64',digests:[]},required,'Responder'),/digest mismatch/);
});
