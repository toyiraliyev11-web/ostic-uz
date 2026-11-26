// Run: node worker.test.mjs  (no dependencies)
import w, { buildMessage } from './worker.js';
import assert from 'node:assert/strict';

const env = { TG_TOKEN: 'TEST_TOKEN', TG_CHAT: '123' };
let sent = [];
let tgOk = true, sheetOk = true;
globalThis.fetch = async (url, init) => {
  sent.push({ url, init });
  return { ok: url.includes('telegram') ? tgOk : sheetOk };
};
const req = (method, body, origin = 'https://ostic.uz') =>
  new Request('https://lead.example.workers.dev/', { method, headers: { Origin: origin, 'Content-Type': 'application/json' }, body });
const good = JSON.stringify({ name: 'Ali', phone: '+998901234567', project: 'Нужны даунлайты на 40 номеров', lang: 'ru', source: 'showroom', evil: 'x' });
let r;

r = await w.fetch(req('POST', good, 'https://evil.example'), env); assert.equal(r.status, 403);
r = await w.fetch(req('OPTIONS', null), env); assert.equal(r.status, 204);
r = await w.fetch(req('GET', null), env); assert.equal(r.status, 405);
r = await w.fetch(req('POST', 'not json'), env); assert.equal(r.status, 400);
r = await w.fetch(req('POST', JSON.stringify({ project: 'short' })), env); assert.equal(r.status, 422);
r = await w.fetch(req('POST', 'x'.repeat(9000)), env); assert.equal(r.status, 413);
r = await w.fetch(req('POST', good), {}); assert.equal(r.status, 500);

// Telegram only
sent = [];
r = await w.fetch(req('POST', good), env); assert.equal(r.status, 204);
assert.equal(sent.length, 1);
const body = JSON.parse(sent[0].init.body);
assert.ok(body.text.includes('Имя: Ali') && body.text.includes('Источник: showroom') && !body.text.includes('evil'));

// Honeypot filled: nothing is sent, the bot still sees success
sent = [];
r = await w.fetch(req('POST', JSON.stringify({ project: 'Нужны даунлайты на 40 номеров', website: 'http://spam' })), env);
assert.equal(r.status, 204); assert.equal(sent.length, 0);

// Telegram + Sheet; the sheet gets the secret and only known fields
const env2 = { ...env, SHEET_URL: 'https://script.google.com/macros/s/X/exec', SHEET_SECRET: 's3cr3t' };
sent = [];
r = await w.fetch(req('POST', good), env2); assert.equal(r.status, 204);
assert.equal(sent.length, 2);
const row = JSON.parse(sent[1].init.body);
assert.equal(row.secret, 's3cr3t'); assert.equal(row.name, 'Ali'); assert.equal(row.evil, undefined);

// Telegram down but the sheet stored it: still a success for the visitor
tgOk = false; sent = [];
r = await w.fetch(req('POST', good), env2); assert.equal(r.status, 204);
// Both down
sheetOk = false;
r = await w.fetch(req('POST', good), env2); assert.equal(r.status, 502);
// Only the sheet configured
tgOk = true; sheetOk = true; sent = [];
r = await w.fetch(req('POST', good), { SHEET_URL: env2.SHEET_URL, SHEET_SECRET: 'x' }); assert.equal(r.status, 204); assert.equal(sent.length, 1);

// The OSTIC platform: the secret goes in a header (not the body), only known fields, https only
const env3 = { ...env, PLATFORM_LEAD_URL: 'https://cloud.ostic.uz/api/v1/public/site-leads', PLATFORM_LEAD_SECRET: 'p'.repeat(40) };
sent = [];
r = await w.fetch(req('POST', good), env3); assert.equal(r.status, 204);
assert.equal(sent.length, 2);
const toPlatform = sent[1];
assert.equal(toPlatform.url, env3.PLATFORM_LEAD_URL);
assert.equal(toPlatform.init.headers['X-Site-Lead-Secret'], env3.PLATFORM_LEAD_SECRET);
const fields = JSON.parse(toPlatform.init.body);
assert.equal(fields.name, 'Ali'); assert.equal(fields.phone, '+998901234567'); assert.equal(fields.evil, undefined); assert.equal(fields.secret, undefined);
// Only the platform configured, and it stored the lead
sent = [];
r = await w.fetch(req('POST', good), { PLATFORM_LEAD_URL: env3.PLATFORM_LEAD_URL, PLATFORM_LEAD_SECRET: 'x'.repeat(40) }); assert.equal(r.status, 204); assert.equal(sent.length, 1);
// A plain http address is never used (the secret would travel in clear)
sent = [];
r = await w.fetch(req('POST', good), { PLATFORM_LEAD_URL: 'http://cloud.ostic.uz/x', PLATFORM_LEAD_SECRET: 'x'.repeat(40) }); assert.equal(r.status, 500); assert.equal(sent.length, 0);

r = await w.fetch(req('POST', good), { ...env, RL: { limit: async () => ({ success: false }) } }); assert.equal(r.status, 429);
assert.equal(buildMessage({ project: 'a\u0000bcdefghij' }).includes('\u0000'), false);
console.log('ALL WORKER TESTS PASSED');
