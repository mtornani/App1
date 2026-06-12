import { JSDOM } from 'jsdom';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');

const html = readFileSync(path.join(ROOT, 'index.html'), 'utf8')
  .replace('<script src="app.js"></script>', '')
  .replace(/<script>[\s\S]*?serviceWorker[\s\S]*?<\/script>/, '');
const dom = new JSDOM(html, { url: 'https://localhost/', runScripts: 'outside-only', pretendToBeVisual: true });
const { window } = dom;

window.confirm = () => true;
import('node:crypto').then(()=>{});
const { webcrypto } = await import('node:crypto');
Object.defineProperty(window, 'crypto', { value: webcrypto, configurable: true });
window.eval(readFileSync(path.join(ROOT, 'app.js'), 'utf8'));
const $ = (s) => window.document.querySelector(s);
const click = (s) => { const el = $(s); if (!el) throw new Error('missing element ' + s); el.dispatchEvent(new window.Event('click', { bubbles: true })); };

// Home → setup
if (!$('#newMatch')) throw new Error('home: no newMatch button');
click('#newMatch');
if (!$('#fHome')) throw new Error('setup view not rendered');
// One player row should exist after setupAddRow
if (!$('.player-row')) throw new Error('no player row');
$('#fHome').value = 'Cesena U19'; $('#fAway').value = 'Rimini U19'; $('#fComp').value = 'Primavera 2';
$('.pNum').value = '10'; $('.pName').value = 'Mario Rossi'; $('.pPos').value = 'Trequartista';
click('#startMatch');
if (!$('#clockTime')) throw new Error('live view not rendered');
// Start clock, tag events
click('#clockToggle');
click('[data-ev="goal"]');
click('[data-ev="dribble_won"]');
click('[data-ev="duel_lost"]');
const feedTxt = $('.feed').textContent;
if (!feedTxt.includes('Gol') || !feedTxt.includes('Mario Rossi')) throw new Error('feed missing events: ' + feedTxt);
// Undo
click('#undo');
if ($('.feed').textContent.includes('Duello perso')) throw new Error('undo failed');
// Note
$('#quickNote').value = 'gran movimento';
click('#addNote');
// Eval
click('#goEval');
if (!$('#evalNotes')) throw new Error('eval view not rendered');
click('[data-verdict="sign"]');
const range = $('[data-score="tecnica"]');
range.value = '8'; range.dispatchEvent(new window.Event('input', { bubbles: true }));
$('#evalNotes').value = 'Ottimo piede'; $('#evalNotes').dispatchEvent(new window.Event('input', { bubbles: true }));
// Report (download path: jsdom lacks share; URL.createObjectURL shim)
window.URL.createObjectURL = () => 'blob:fake'; window.URL.revokeObjectURL = () => {};
let downloaded = null;
const origCreate = window.document.createElement.bind(window.document);
window.document.createElement = (tag) => { const el = origCreate(tag); if (tag === 'a') { el.click = () => { downloaded = el.download; }; } return el; };
click('#makeReport');
if (!downloaded) throw new Error('report not generated');
console.log('downloaded:', downloaded);
// State persisted
const st = JSON.parse(window.localStorage.getItem('scoutpad-v1'));
if (st.reports !== 1) throw new Error('reports counter not incremented');
const sess = st.sessions[0];
if (sess.events.length !== 2 || sess.notes.length !== 1) throw new Error('session data wrong: ' + JSON.stringify({e: sess.events.length, n: sess.notes.length}));
const ev = Object.values(sess.evals)[0];
if (ev.verdict !== 'sign' || ev.scores.tecnica !== 8 || ev.notes !== 'Ottimo piede') throw new Error('eval not saved: ' + JSON.stringify(ev));
// Paywall after 3 reports: generate two more via UI, fourth attempt must lock
click('#makeReport');
click('#makeReport');
click('#makeReport');
if (!$('#licKey')) throw new Error('paywall not shown after free limit');
// License activation (key from genkey for this email with default secret)
$('#licEmail').value = 'mirkotornani@gmail.com';
$('#licKey').value = '6B82-D767-BCBE-10FA';
click('#activate');
await new Promise((r) => setTimeout(r, 300));
const st2 = JSON.parse(window.localStorage.getItem('scoutpad-v1'));
if (!st2.license) throw new Error('license not activated');
console.log('license activated for', st2.license.email);
console.log('ALL SMOKE TESTS PASSED');
