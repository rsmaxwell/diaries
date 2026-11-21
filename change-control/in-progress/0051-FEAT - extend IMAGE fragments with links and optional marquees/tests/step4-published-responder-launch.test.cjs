/* Ensure the published-image runner launches responder.sh using CONFIG_FILE. */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { test } = require('node:test');
const root = path.resolve(__dirname, '../../../..');
const feature = path.join(root, 'change-control/in-progress/0051-FEAT - extend IMAGE fragments with links and optional marquees');
const harness = fs.readFileSync(path.join(feature, 'tests/step3-isolated-reader-smoke.cjs'), 'utf8');
const rollout = fs.readFileSync(path.join(feature, 'tests/step4-rollout-rehearsal-checks.cjs'), 'utf8');
const launcher = fs.readFileSync(path.join(root, 'diaries-responder/scripts/files/responder.sh'), 'utf8');

test('responder.sh reads CONFIG_FILE to select its JSON configuration', () => {
  assert.match(launcher, /CONFIG_FILE="\$\{CONFIG_FILE:-/);
  assert.match(launcher, /--config "\$\{CONFIG_FILE\}"/);
});
test('initial published responder mounts synthetic fixtures and selects config via environment', () => {
  assert.match(harness, /'-e','CONFIG_FILE=\/fixture\/responder\.json'/);
  assert.match(harness, /image\]\);/);
  assert.doesNotMatch(harness, /image,'--config','\/fixture\/responder\.json'/);
});
test('legacy and candidate responder swaps select their respective configurations', () => {
  assert.match(rollout, /'-e','CONFIG_FILE=\/config\/responder\.json'/);
  assert.match(rollout, /'-e','CONFIG_FILE=\/fixture\/responder\.json'/);
  assert.equal((rollout.match(/\.\.\.newResponderArgs,images\.candidate\.responder\]/g) || []).length, 2);
  assert.doesNotMatch(rollout, /images\.candidate\.responder,'--config'/);
});
test('gate-disabled, rollback, re-upgrade, activation sequence retained', () => {
  for(const label of ['step4-gate-disabled.json','step4-preactivation-rollback.json','step4-rollout-receipt.json']) {
    assert(rollout.includes(label), `Missing accepted check: ${label}`);
  }
});
