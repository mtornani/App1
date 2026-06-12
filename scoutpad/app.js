/* ScoutPad — taccuino digitale per scout: tagging live, valutazioni, report.
   Offline-first: tutti i dati vivono in localStorage sul telefono dello scout. */
'use strict';

// ---------- Config ----------
const BUY_URL = 'https://gumroad.com/l/scoutpad-pro'; // sostituisci col tuo prodotto Gumroad/Stripe
const FREE_REPORTS = 3;
// Cambia questo secret PRIMA di vendere licenze e rigenera le chiavi con tools/genkey.js.
// Protezione "soft": tiene onesti gli onesti, non ferma un developer determinato.
const LICENSE_SECRET = 'scoutpad-change-me';

const EVENT_TYPES = [
  { code: 'goal', label: 'Gol', icon: '⚽', sign: 'pos' },
  { code: 'shot_on', label: 'Tiro in porta', icon: '🎯', sign: 'pos' },
  { code: 'shot_off', label: 'Tiro fuori', icon: '💨', sign: 'neg' },
  { code: 'assist', label: 'Assist', icon: '🅰️', sign: 'pos' },
  { code: 'key_pass', label: 'Pass. chiave', icon: '🔑', sign: 'pos' },
  { code: 'dribble_won', label: 'Dribbling ✓', icon: '🪄', sign: 'pos' },
  { code: 'dribble_lost', label: 'Dribbling ✗', icon: '🚧', sign: 'neg' },
  { code: 'duel_won', label: 'Duello vinto', icon: '💪', sign: 'pos' },
  { code: 'duel_lost', label: 'Duello perso', icon: '🥀', sign: 'neg' },
  { code: 'recovery', label: 'Recupero', icon: '🧲', sign: 'pos' },
  { code: 'loss', label: 'Palla persa', icon: '🕳️', sign: 'neg' },
  { code: 'cross', label: 'Cross', icon: '🌙', sign: 'pos' },
  { code: 'foul_won', label: 'Fallo subito', icon: '🩹', sign: 'pos' },
  { code: 'foul', label: 'Fallo fatto', icon: '🟨', sign: 'neg' },
  { code: 'save', label: 'Parata', icon: '🧤', sign: 'pos' },
  { code: 'error', label: 'Errore grave', icon: '❌', sign: 'neg' },
];
const EV = Object.fromEntries(EVENT_TYPES.map((e) => [e.code, e]));

const CATEGORIES = [
  ['tecnica', 'Tecnica'], ['tattica', 'Tattica'], ['fisico', 'Fisico'],
  ['velocita', 'Velocità'], ['mentalita', 'Mentalità'], ['personalita', 'Personalità'],
];
const VERDICTS = { sign: 'FIRMARE', watch: 'MONITORARE', pass: 'SCARTARE' };

// ---------- State ----------
const STORE_KEY = 'scoutpad-v1';
let state = load();
let view = { name: 'home', sessionId: null, playerId: null };
let clockTimer = null;

function load() {
  try {
    const raw = localStorage.getItem(STORE_KEY);
    if (raw) return JSON.parse(raw);
  } catch (e) { /* corrotto: riparti pulito */ }
  return { sessions: [], reports: 0, license: null };
}
function save() { localStorage.setItem(STORE_KEY, JSON.stringify(state)); }
const uid = () => Math.random().toString(36).slice(2, 10);
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const session = () => state.sessions.find((s) => s.id === view.sessionId);

function toast(msg) {
  const t = $('#toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(t._h);
  t._h = setTimeout(() => t.classList.remove('show'), 2200);
}

// ---------- Clock ----------
function clockSeconds(s) {
  const c = s.clock;
  return c.base + (c.startedAt ? (Date.now() - c.startedAt) / 1000 : 0);
}
function currentMinute(s) {
  return s.clock.halfStartMin + Math.floor(clockSeconds(s) / 60);
}
function clockLabel(s) {
  const sec = Math.floor(clockSeconds(s));
  const m = String(s.clock.halfStartMin + Math.floor(sec / 60)).padStart(2, '0');
  return `${m}:${String(sec % 60).padStart(2, '0')}`;
}

// ---------- Licensing ----------
async function keyForEmail(email) {
  const enc = new TextEncoder();
  const k = await crypto.subtle.importKey('raw', enc.encode(LICENSE_SECRET), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const sig = await crypto.subtle.sign('HMAC', k, enc.encode(email.trim().toLowerCase()));
  const hex = [...new Uint8Array(sig)].map((b) => b.toString(16).padStart(2, '0')).join('').slice(0, 16).toUpperCase();
  return hex.match(/.{4}/g).join('-');
}
async function activateLicense(email, key) {
  if (!crypto.subtle) { toast('Serve HTTPS per attivare la licenza'); return false; }
  const expected = await keyForEmail(email);
  if (expected === key.trim().toUpperCase()) {
    state.license = { email: email.trim().toLowerCase(), key: expected };
    save();
    return true;
  }
  return false;
}
const isPro = () => !!state.license;
const reportsLeft = () => Math.max(0, FREE_REPORTS - state.reports);

// ---------- Render ----------
function render() {
  clearInterval(clockTimer);
  $('#hdrRight').innerHTML = isPro()
    ? '<span class="badge">PRO</span>'
    : `${reportsLeft()}/${FREE_REPORTS} report gratis`;
  const r = { home: renderHome, setup: renderSetup, live: renderLive, eval: renderEval, paywall: renderPaywall }[view.name];
  $('#app').innerHTML = r();
  bind();
  if (view.name === 'live') {
    clockTimer = setInterval(() => {
      const s = session();
      const el = $('#clockTime');
      if (s && el) el.textContent = clockLabel(s);
    }, 1000);
  }
}

function renderHome() {
  const items = state.sessions.slice().reverse().map((s) => `
    <div class="card session-item">
      <div style="min-width:0">
        <h3>${esc(s.home)} – ${esc(s.away)}</h3>
        <div class="dim small">${esc(s.date)} · ${esc(s.competition || '')} · ${s.players.length} osservati · ${s.events.length} eventi</div>
      </div>
      <div style="flex:0 0 auto">
        <button class="btn-ghost" data-open="${s.id}">Apri</button>
        <button class="btn-danger" data-del="${s.id}">✕</button>
      </div>
    </div>`).join('');
  return `
    <button class="btn-primary" id="newMatch">+ Nuova partita</button>
    <div style="height:14px"></div>
    ${items || '<div class="card dim">Nessuna partita. Creane una e inizia a taggare dal vivo: funziona anche senza rete, a bordo campo.</div>'}
    <div class="card">
      <h2>Backup</h2>
      <div class="row">
        <button class="btn" id="exportData" style="text-align:center">Esporta dati</button>
        <button class="btn" id="importData" style="text-align:center">Importa</button>
      </div>
      ${isPro() ? `<div class="small dim">Licenza PRO attiva: ${esc(state.license.email)}</div>`
        : `<button class="btn-ghost" id="goPro">Hai una licenza? Attiva ScoutPad PRO →</button>`}
    </div>
    <div class="muted-link">ScoutPad · i dati restano sul tuo telefono · parte di OpenScout</div>
    <input type="file" id="importFile" accept="application/json" hidden>`;
}

function renderSetup() {
  return `
    <div class="card">
      <h2>Nuova partita</h2>
      <div class="row">
        <div><label>Casa</label><input id="fHome" placeholder="Es. Cesena U19"></div>
        <div><label>Ospite</label><input id="fAway" placeholder="Es. Rimini U19"></div>
      </div>
      <div class="row">
        <div><label>Data</label><input id="fDate" type="date" value="${new Date().toISOString().slice(0, 10)}"></div>
        <div><label>Competizione</label><input id="fComp" placeholder="Es. Primavera 2"></div>
      </div>
    </div>
    <div class="card">
      <h2>Giocatori da osservare</h2>
      <div id="playerRows"></div>
      <button class="btn" id="addPlayer" style="text-align:center">+ Aggiungi giocatore</button>
      <div class="small dim">Numero di maglia, nome, squadra e ruolo. Puoi osservarne più d'uno nella stessa partita.</div>
    </div>
    <button class="btn-primary" id="startMatch">Inizia osservazione</button>
    <button class="btn-ghost" id="backHome">← Annulla</button>`;
}

function playerRowHTML() {
  return `
    <div class="row player-row" style="margin-bottom:8px">
      <input class="pNum" placeholder="N°" inputmode="numeric" style="flex:0 0 64px">
      <input class="pName" placeholder="Nome" style="flex:2">
      <select class="pTeam" style="flex:1"><option>Casa</option><option>Ospite</option></select>
      <input class="pPos" placeholder="Ruolo" style="flex:1">
    </div>`;
}

function renderLive() {
  const s = session();
  const sel = s.players.find((p) => p.id === view.playerId) || s.players[0];
  if (sel) view.playerId = sel.id;
  const chips = s.players.map((p) =>
    `<button class="chip ${p.id === view.playerId ? 'active' : ''}" data-player="${p.id}">${p.number ? '#' + esc(p.number) + ' ' : ''}${esc(p.name)}</button>`).join('');
  const grid = EVENT_TYPES.map((e) =>
    `<button class="evbtn ${e.sign}" data-ev="${e.code}"><b>${e.icon}</b>${e.label}</button>`).join('');
  const feed = s.events.slice(-30).reverse().map((e) => {
    const p = s.players.find((x) => x.id === e.playerId);
    return `<div><span>${e.min}' ${EV[e.type].icon} ${EV[e.type].label} — <b>${esc(p ? p.name : '?')}</b></span></div>`;
  }).join('');
  const c = s.clock;
  return `
    <div class="card clock">
      <div class="time" id="clockTime">${clockLabel(s)}</div>
      <div style="display:flex;gap:8px">
        <button class="btn" id="clockToggle" style="width:auto;margin:0">${c.startedAt ? '⏸ Pausa' : '▶ Avvia'}</button>
        <button class="btn" id="clockHalf" style="width:auto;margin:0">${c.halfStartMin === 0 ? '2° T' : '⏹'}</button>
      </div>
    </div>
    <div class="chips">${chips || '<span class="dim">Nessun giocatore osservato</span>'}</div>
    <div class="evgrid">${grid}</div>
    <div style="height:10px"></div>
    <div class="row">
      <input id="quickNote" placeholder="Nota rapida (es. 'gran movimento senza palla')">
      <button class="btn" id="addNote" style="flex:0 0 64px;text-align:center;margin:0">＋</button>
    </div>
    <div class="card">
      <div class="topbar"><h2 style="margin:0">Eventi (${s.events.length})</h2>
        <button class="btn-ghost" id="undo">↩ Annulla ultimo</button></div>
      <div class="feed">${feed || '<span class="dim small">Tocca un giocatore e poi un evento.</span>'}</div>
    </div>
    <button class="btn-primary" id="goEval">Valutazioni e report →</button>
    <button class="btn-ghost" id="backHome">← Partite</button>`;
}

function renderEval() {
  const s = session();
  const p = s.players.find((x) => x.id === view.playerId) || s.players[0];
  if (!p) return '<div class="card dim">Nessun giocatore osservato in questa partita.</div><button class="btn-ghost" id="backLive">← Indietro</button>';
  view.playerId = p.id;
  const ev = (s.evals[p.id] = s.evals[p.id] || { scores: {}, verdict: null, notes: '' });
  const chips = s.players.map((x) =>
    `<button class="chip ${x.id === p.id ? 'active' : ''}" data-player="${x.id}">${esc(x.name)}</button>`).join('');
  const counts = countEvents(s, p.id);
  const summary = EVENT_TYPES.filter((e) => counts[e.code])
    .map((e) => `<span class="pill">${e.icon} ${e.label}: <b>${counts[e.code]}</b></span>`).join(' ') || '<span class="dim small">Nessun evento taggato.</span>';
  const sliders = CATEGORIES.map(([k, label]) => `
    <div class="slider-row"><span>${label}</span>
      <input type="range" min="1" max="10" step="1" value="${ev.scores[k] || 6}" data-score="${k}">
      <b id="sv-${k}">${ev.scores[k] || 6}</b></div>`).join('');
  return `
    <div class="chips">${chips}</div>
    <div class="card">
      <h3>${p.number ? '#' + esc(p.number) + ' ' : ''}${esc(p.name)} <span class="pill">${esc(p.pos || '')}</span></h3>
      <div style="margin:8px 0 14px">${summary}</div>
      ${sliders}
      <label style="margin-top:10px">Verdetto</label>
      <div class="verdict">
        <button class="v-sign ${ev.verdict === 'sign' ? 'on' : ''}" data-verdict="sign">FIRMARE</button>
        <button class="v-watch ${ev.verdict === 'watch' ? 'on' : ''}" data-verdict="watch">MONITORARE</button>
        <button class="v-pass ${ev.verdict === 'pass' ? 'on' : ''}" data-verdict="pass">SCARTARE</button>
      </div>
      <label style="margin-top:12px">Note dello scout</label>
      <textarea id="evalNotes" placeholder="Punti di forza, debolezze, contesto, proiezione...">${esc(ev.notes)}</textarea>
    </div>
    <button class="btn-primary" id="makeReport">📄 Genera report partita</button>
    <button class="btn-ghost" id="backLive">← Torna al live</button>`;
}

function renderPaywall() {
  return `
    <div class="card lock">
      <div class="big">🔓</div>
      <h3>Hai usato i ${FREE_REPORTS} report gratuiti</h3>
      <p class="dim">ScoutPad PRO sblocca report illimitati per sempre. Una licenza, tutti i tuoi dispositivi.</p>
      <button class="btn-primary" id="buy">Acquista ScoutPad PRO</button>
    </div>
    <div class="card">
      <h2>Ho già una licenza</h2>
      <label>Email d'acquisto</label><input id="licEmail" type="email" placeholder="email@esempio.it">
      <label>Chiave licenza</label><input id="licKey" placeholder="XXXX-XXXX-XXXX-XXXX" autocapitalize="characters">
      <button class="btn-primary" id="activate">Attiva</button>
    </div>
    <button class="btn-ghost" id="backHome">← Indietro</button>`;
}

// ---------- Events / actions ----------
function countEvents(s, playerId) {
  const out = {};
  for (const e of s.events) if (e.playerId === playerId) out[e.type] = (out[e.type] || 0) + 1;
  return out;
}

function bind() {
  const on = (sel, fn) => { const el = $(sel); if (el) el.addEventListener('click', fn); };

  on('#newMatch', () => { view = { name: 'setup' }; render(); setupAddRow(); });
  on('#backHome', () => { view = { name: 'home' }; render(); });
  on('#goPro', () => { view = { name: 'paywall' }; render(); });
  on('#buy', () => window.open(BUY_URL, '_blank'));

  document.querySelectorAll('[data-open]').forEach((b) => b.addEventListener('click', () => {
    view = { name: 'live', sessionId: b.dataset.open };
    render();
  }));
  document.querySelectorAll('[data-del]').forEach((b) => b.addEventListener('click', () => {
    if (!confirm('Eliminare questa partita e tutti i suoi dati?')) return;
    state.sessions = state.sessions.filter((s) => s.id !== b.dataset.del);
    save(); render();
  }));

  on('#exportData', () => {
    downloadFile(`scoutpad-backup-${Date.now()}.json`, JSON.stringify(state), 'application/json');
  });
  on('#importData', () => $('#importFile').click());
  const imp = $('#importFile');
  if (imp) imp.addEventListener('change', async () => {
    try {
      const incoming = JSON.parse(await imp.files[0].text());
      if (!Array.isArray(incoming.sessions)) throw new Error('formato non valido');
      state = incoming; save(); render(); toast('Backup importato');
    } catch (e) { toast('File non valido'); }
  });

  // Setup
  on('#addPlayer', setupAddRow);
  on('#startMatch', () => {
    const players = [...document.querySelectorAll('.player-row')].map((r) => ({
      id: uid(),
      number: r.querySelector('.pNum').value.trim(),
      name: r.querySelector('.pName').value.trim(),
      team: r.querySelector('.pTeam').value,
      pos: r.querySelector('.pPos').value.trim(),
    })).filter((p) => p.name);
    const s = {
      id: uid(),
      home: $('#fHome').value.trim() || 'Casa',
      away: $('#fAway').value.trim() || 'Ospite',
      date: $('#fDate').value,
      competition: $('#fComp').value.trim(),
      players,
      events: [],
      notes: [],
      evals: {},
      clock: { base: 0, startedAt: null, halfStartMin: 0 },
    };
    state.sessions.push(s); save();
    view = { name: 'live', sessionId: s.id, playerId: players[0]?.id };
    render();
  });

  // Live
  document.querySelectorAll('[data-player]').forEach((b) => b.addEventListener('click', () => {
    view.playerId = b.dataset.player; render();
  }));
  document.querySelectorAll('[data-ev]').forEach((b) => b.addEventListener('click', () => {
    const s = session();
    if (!view.playerId) { toast('Seleziona prima un giocatore'); return; }
    s.events.push({ t: Date.now(), min: currentMinute(s), playerId: view.playerId, type: b.dataset.ev });
    save();
    const p = s.players.find((x) => x.id === view.playerId);
    toast(`${EV[b.dataset.ev].icon} ${EV[b.dataset.ev].label} — ${p.name}`);
    if (navigator.vibrate) navigator.vibrate(15);
    render();
  }));
  on('#undo', () => { const s = session(); s.events.pop(); save(); render(); });
  on('#clockToggle', () => {
    const s = session(); const c = s.clock;
    if (c.startedAt) { c.base += (Date.now() - c.startedAt) / 1000; c.startedAt = null; }
    else c.startedAt = Date.now();
    save(); render();
  });
  on('#clockHalf', () => {
    const s = session(); const c = s.clock;
    if (c.halfStartMin === 0) { c.halfStartMin = 45; c.base = 0; c.startedAt = null; toast('Secondo tempo'); }
    else { if (c.startedAt) { c.base += (Date.now() - c.startedAt) / 1000; c.startedAt = null; } toast('Partita conclusa'); }
    save(); render();
  });
  on('#addNote', () => {
    const s = session(); const txt = $('#quickNote').value.trim();
    if (!txt) return;
    s.notes.push({ min: currentMinute(s), playerId: view.playerId, text: txt });
    save(); $('#quickNote').value = ''; toast('Nota salvata');
  });
  on('#goEval', () => { view.name = 'eval'; render(); });
  on('#backLive', () => { view.name = 'live'; render(); });

  // Eval
  document.querySelectorAll('[data-score]').forEach((r) => r.addEventListener('input', () => {
    const s = session();
    s.evals[view.playerId].scores[r.dataset.score] = Number(r.value);
    $('#sv-' + r.dataset.score).textContent = r.value;
    save();
  }));
  document.querySelectorAll('[data-verdict]').forEach((b) => b.addEventListener('click', () => {
    const s = session();
    s.evals[view.playerId].verdict = b.dataset.verdict;
    save(); render();
  }));
  const notes = $('#evalNotes');
  if (notes) notes.addEventListener('input', () => {
    session().evals[view.playerId].notes = notes.value; save();
  });
  on('#makeReport', generateReport);

  // Paywall
  on('#activate', async () => {
    const ok = await activateLicense($('#licEmail').value, $('#licKey').value);
    if (ok) { toast('ScoutPad PRO attivato 🎉'); view = { name: 'home' }; render(); }
    else toast('Chiave non valida per questa email');
  });
}

function setupAddRow() {
  const div = document.createElement('div');
  div.innerHTML = playerRowHTML();
  $('#playerRows').appendChild(div.firstElementChild);
}

// ---------- Report ----------
function radarSVG(labels, values, size = 320) {
  const cx = size / 2, cy = size / 2, R = size / 2 - 52, n = labels.length;
  const pt = (i, r) => {
    const a = (Math.PI * 2 * i) / n - Math.PI / 2;
    return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
  };
  let out = '';
  for (const f of [0.25, 0.5, 0.75, 1]) {
    out += `<polygon points="${labels.map((_, i) => pt(i, R * f).join(',')).join(' ')}" fill="none" stroke="#30363d"/>`;
  }
  out += labels.map((_, i) => { const [x, y] = pt(i, R); return `<line x1="${cx}" y1="${cy}" x2="${x}" y2="${y}" stroke="#30363d"/>`; }).join('');
  out += `<polygon points="${labels.map((_, i) => pt(i, (R * values[i]) / 10).join(',')).join(' ')}" fill="rgba(63,185,80,.3)" stroke="#3fb950" stroke-width="2"/>`;
  out += labels.map((l, i) => {
    const [x, y] = pt(i, R + 26);
    return `<text x="${x}" y="${y}" fill="#8b949e" font-size="12" text-anchor="middle">${l} <tspan fill="#e6edf3" font-weight="bold">${values[i]}</tspan></text>`;
  }).join('');
  return `<svg viewBox="0 0 ${size} ${size}" width="100%" style="max-width:${size}px;display:block;margin:0 auto" xmlns="http://www.w3.org/2000/svg">${out}</svg>`;
}

function reportHTML(s) {
  const vColor = { sign: '#3fb950', watch: '#d29922', pass: '#f85149' };
  const playerBlocks = s.players.map((p) => {
    const ev = s.evals[p.id] || { scores: {}, verdict: null, notes: '' };
    const counts = countEvents(s, p.id);
    const stats = EVENT_TYPES.filter((e) => counts[e.code])
      .map((e) => `<div class="stat"><b>${counts[e.code]}</b><span>${e.icon} ${e.label}</span></div>`).join('');
    const radar = radarSVG(CATEGORIES.map(([, l]) => l), CATEGORIES.map(([k]) => ev.scores[k] || 6));
    const avg = (CATEGORIES.reduce((a, [k]) => a + (ev.scores[k] || 6), 0) / CATEGORIES.length).toFixed(1);
    const timeline = s.events.filter((e) => e.playerId === p.id)
      .map((e) => `<tr><td>${e.min}'</td><td>${EV[e.type].icon} ${EV[e.type].label}</td></tr>`).join('');
    const pNotes = s.notes.filter((n) => n.playerId === p.id)
      .map((n) => `<li><b>${n.min}'</b> ${esc(n.text)}</li>`).join('');
    return `
    <div class="card">
      <h2 style="font-size:20px;color:#e6edf3;text-transform:none;letter-spacing:0">
        ${p.number ? '#' + esc(p.number) + ' ' : ''}${esc(p.name)}
        ${ev.verdict ? `<span class="verdict" style="background:${vColor[ev.verdict]}">${VERDICTS[ev.verdict]}</span>` : ''}
      </h2>
      <div class="dim">${esc(p.pos || '')} · ${p.team === 'Casa' ? esc(s.home) : esc(s.away)} · media valutazione <b style="color:#e6edf3">${avg}/10</b></div>
      <div style="margin:16px 0">${radar}</div>
      ${stats ? `<div class="grid">${stats}</div>` : ''}
      ${ev.notes ? `<h3>Note dello scout</h3><p>${esc(ev.notes).replace(/\n/g, '<br>')}</p>` : ''}
      ${pNotes ? `<h3>Appunti live</h3><ul>${pNotes}</ul>` : ''}
      ${timeline ? `<h3>Timeline eventi</h3><table>${timeline}</table>` : ''}
    </div>`;
  }).join('');

  return `<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Report scouting — ${esc(s.home)} vs ${esc(s.away)}</title><style>
body{font-family:-apple-system,'Segoe UI',Roboto,sans-serif;background:#0d1117;color:#e6edf3;margin:0;padding:28px 14px}
.wrap{max-width:760px;margin:0 auto}
.card{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:22px;margin-bottom:14px}
h1{margin:0 0 4px;font-size:24px} h2{font-size:14px;color:#8b949e;text-transform:uppercase;letter-spacing:.06em;margin:0 0 10px}
h3{font-size:13px;color:#8b949e;text-transform:uppercase;margin:18px 0 6px}
.dim{color:#8b949e;font-size:14px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:10px;margin-top:14px}
.stat{background:#0d1117;border:1px solid #30363d;border-radius:10px;padding:8px 10px}
.stat b{display:block;font-size:18px}.stat span{color:#8b949e;font-size:11px}
.verdict{color:#04260f;font-weight:800;border-radius:8px;padding:3px 12px;font-size:13px;vertical-align:middle}
table{border-collapse:collapse;width:100%;font-size:14px} td{padding:5px 8px;border-bottom:1px solid #30363d}
ul{padding-left:18px;font-size:14px} p{font-size:14px;line-height:1.5}
.footer{color:#8b949e;font-size:12px;text-align:center;margin-top:22px}
@media print{body{background:#fff;color:#111}.card{border-color:#ddd;background:#fff}}
</style></head><body><div class="wrap">
<div class="card"><h1>${esc(s.home)} – ${esc(s.away)}</h1>
<div class="dim">${esc(s.date)}${s.competition ? ' · ' + esc(s.competition) : ''} · ${s.events.length} eventi taggati dal vivo</div></div>
${playerBlocks}
<div class="footer">Report generato con ScoutPad · scoutpad.app</div>
</div></body></html>`;
}

function downloadFile(name, content, type) {
  const blob = new Blob([content], { type });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 5000);
}

async function generateReport() {
  if (!isPro() && state.reports >= FREE_REPORTS) { view.name = 'paywall'; render(); return; }
  const s = session();
  const html = reportHTML(s);
  const name = `report-${s.home}-${s.away}-${s.date}.html`.replace(/\s+/g, '-').toLowerCase();
  const file = new File([html], name, { type: 'text/html' });
  state.reports += 1; save();
  if (navigator.canShare && navigator.canShare({ files: [file] })) {
    try {
      await navigator.share({ files: [file], title: 'Report scouting' });
      toast('Report condiviso'); render();
      return;
    } catch (e) { /* annullato: fallback al download */ }
  }
  downloadFile(name, html, 'text/html');
  toast('Report scaricato');
  render();
}

render();
