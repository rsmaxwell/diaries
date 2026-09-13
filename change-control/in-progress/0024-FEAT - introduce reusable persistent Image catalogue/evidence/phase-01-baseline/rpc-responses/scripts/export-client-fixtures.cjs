'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { verifyCapture } = require('./verify-compatibility.cjs');
const [capture, destination] = process.argv.slice(2);
if (!capture || !destination) throw new Error('Usage: node export-client-fixtures.cjs <capture-directory> <new-destination.ts>');
const cases = verifyCapture(capture);
fs.mkdirSync(path.dirname(destination), { recursive: true });
fs.writeFileSync(destination,
  '// Generated from the 0024 Phase 1 MQTT capture by export-client-fixtures.cjs.\n' +
  '// Test fixtures only; source capture and SHA-256 manifest are in parent change-control.\n' +
  'export const fileRpcBaseline = ' + JSON.stringify(cases, null, 2) + ';\n', { flag: 'wx' });
