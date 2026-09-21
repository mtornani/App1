/* Console dell'agenzia — offline-first, zero dipendenze.
 *
 * Cosa fa, in ordine di importanza:
 *  1. mostra lo stato delle missioni leggendo state/index.json (con cache locale,
 *     quindi l'ultimo stato noto resta leggibile anche in aereo);
 *  2. crea missioni scrivendo il file JSON nel repo via GitHub API e risvegliando
 *     il workflow; senza token o senza rete la missione resta in coda locale;
 *  3. non esegue nulla lato client: l'esecuzione e' sempre della CI, cosi' il
 *     telefono puo' spegnersi senza fermare il lavoro.
 */
'use strict';

const LS = {
  settings: 'agency.settings',
  cache: 'agency.cache',
  queue: 'agency.queue'
};

const DEFAULTS = { owner: '', repo: '', branch: 'main', token: '' };
const WORKFLOW_FILE = 'agency.yml';
const MISSIONS_PATH = 'agency/state/missions';
const INDEX_URL = '../state/index.json';

const TOPOLOGY_HINTS = {
  team: 'Il PM scompone la missione, gli specialisti eseguono in sequenza.',
  swarm: 'Nessun centro: ogni agente decide se chiudere o passare la palla.',
  solo: 'Un agente, un turno. Veloce ed economico, nessun controllo incrociato.'
};

let state = { counts: {}, missions: [], generated_at: null };
let filter = 'all';
let topology = 'team';

/* ------------------------------------------------------------- storage */

function readLS(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch (err) {
    return fallback;
  }
}

function writeLS(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (err) {
    toast('Memoria del browser piena o bloccata', 'err');
  }
}

function settings() {
  return Object.assign({}, DEFAULTS, readLS(LS.settings, {}));
}

function configured() {
  const s = settings();
  return Boolean(s.owner && s.repo && s.token);
}

/* ---------------------------------------------------------------- utils */

function $(id) { return document.getElementById(id); }

function escapeHtml(text) {
  return String(text == null ? '' : text)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function toast(message, kind) {
  const el = $('toast');
  el.textContent = message;
  el.className = 'toast show ' + (kind || '');
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => { el.className = 'toast'; }, 3600);
}

/* Slug identico a store.slugify(): gli id devono combaciare tra PWA e CLI. */
function slugify(text, maxLen) {
  const ascii = text.normalize('NFKD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const slug = ascii.replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
  return (slug.slice(0, maxLen || 24).replace(/-+$/, '')) || 'mission';
}

/* Stesso formato di store.utc_now(): ISO-8601 UTC al millisecondo. */
function utcNow() {
  return new Date().toISOString();
}

function missionId(objective) {
  const stamp = utcNow().replace(/[-:TZ]/g, '');
  return 'm-' + stamp.slice(0, 8) + '-' + stamp.slice(8, 14) + '-' + slugify(objective, 24);
}

/* Base64 UTF-8 safe: btoa() da solo rompe su accenti e emoji. */
function b64encode(str) {
  const bytes = new TextEncoder().encode(str);
  let binary = '';
  bytes.forEach(byte => { binary += String.fromCharCode(byte); });
  return btoa(binary);
}

/* Decodifica base64 -> UTF-8 (l'API GitHub restituisce il contenuto cosi'). */
function b64decode(b64) {
  const binary = atob(String(b64).replace(/\s/g, ''));
  const bytes = Uint8Array.from(binary, char => char.charCodeAt(0));
  return new TextDecoder('utf-8').decode(bytes);
}

function relativeTime(iso) {
  if (!iso) return '';
  const delta = (Date.now() - Date.parse(iso)) / 1000;
  if (!isFinite(delta)) return '';
  if (delta < 60) return 'ora';
  if (delta < 3600) return Math.floor(delta / 60) + ' min fa';
  if (delta < 86400) return Math.floor(delta / 3600) + ' h fa';
  return Math.floor(delta / 86400) + ' g fa';
}

/* ------------------------------------------------------------ GitHub API */

async function github(path, options) {
  const s = settings();
  const response = await fetch('https://api.github.com' + path, Object.assign({
    headers: {
      'Accept': 'application/vnd.github+json',
      'Authorization': 'Bearer ' + s.token,
      'X-GitHub-Api-Version': '2022-11-28'
    }
  }, options || {}));
  if (!response.ok) {
    const detail = await response.text();
    throw new Error('GitHub ' + response.status + ': ' + detail.slice(0, 180));
  }
  return response.status === 204 ? null : response.json();
}

/* Carica lo stato: prima il file statico (veloce, niente token), poi l'API
 * (utile su repo privati o quando Pages non e' attivo), infine la cache. */
async function loadState(announce) {
  const s = settings();
  try {
    const response = await fetch(INDEX_URL + '?t=' + Date.now(), { cache: 'no-store' });
    if (!response.ok) throw new Error('index non raggiungibile');
    state = await response.json();
    writeLS(LS.cache, state);
    setDot('ok', 'Stato aggiornato');
    if (announce) toast('Stato aggiornato', 'ok');
    return;
  } catch (err) { /* si prova l'API */ }

  if (configured()) {
    try {
      const data = await github('/repos/' + s.owner + '/' + s.repo +
        '/contents/agency/state/index.json?ref=' + encodeURIComponent(s.branch || 'main'));
      state = JSON.parse(b64decode(data.content));
      writeLS(LS.cache, state);
      setDot('ok', 'Stato aggiornato via API');
      if (announce) toast('Stato aggiornato', 'ok');
      return;
    } catch (err) { /* si usa la cache */ }
  }

  const cached = readLS(LS.cache, null);
  if (cached) {
    state = cached;
    setDot('warn', 'Offline: ultimo stato noto');
    if (announce) toast('Offline: mostro l\'ultimo stato noto', 'err');
  } else {
    state = { counts: {}, missions: [] };
    setDot('err', 'Nessuno stato disponibile');
  }
}

/* Invia una missione: scrive il file e sveglia il workflow.
 * Il dispatch e' best-effort: se il token non ha i permessi su Actions la
 * missione parte comunque al giro successivo del cron. */
async function pushMission(mission) {
  const s = settings();
  const path = MISSIONS_PATH + '/' + mission.id + '.json';
  await github('/repos/' + s.owner + '/' + s.repo + '/contents/' + path, {
    method: 'PUT',
    body: JSON.stringify({
      message: 'agency: nuova missione ' + mission.id,
      content: b64encode(JSON.stringify(mission, null, 2) + '\n'),
      branch: s.branch || 'main'
    })
  });

  let dispatched = true;
  try {
    await github('/repos/' + s.owner + '/' + s.repo + '/actions/workflows/' +
      WORKFLOW_FILE + '/dispatches', {
      method: 'POST',
      body: JSON.stringify({ ref: s.branch || 'main' })
    });
  } catch (err) {
    dispatched = false;
  }
  return dispatched;
}

/* -------------------------------------------------------------- missioni */

function buildMission() {
  const objective = $('objective').value.trim();
  if (!objective) { toast('Serve un obiettivo', 'err'); return null; }
  const agents = topology === 'team' ? [] : [$('agent').value];
  return {
    id: missionId(objective),
    objective: objective,
    topology: topology,
    agents: agents,
    context: $('context').value.trim(),
    status: 'pending',
    source: 'pwa',
    created_at: utcNow(),
    started_at: null,
    finished_at: null,
    deliverable: null,
    error: null
  };
}

async function sendMission() {
  const mission = buildMission();
  if (!mission) return;

  const button = $('btn-send');
  button.disabled = true;
  button.textContent = 'Invio...';

  try {
    if (!configured()) throw new Error('setup incompleto');
    const dispatched = await pushMission(mission);
    toast(dispatched ? 'Missione in coda, agenzia svegliata' : 'Missione in coda (parte al prossimo giro)', 'ok');
    $('objective').value = '';
    $('context').value = '';
    await loadState(false);
  } catch (err) {
    // Coda locale: nulla va perso se manca rete, token o permessi.
    const queue = readLS(LS.queue, []);
    queue.unshift(mission);
    writeLS(LS.queue, queue.slice(0, 50));
    toast('Salvata in coda locale: ' + err.message, 'err');
  } finally {
    button.disabled = false;
    button.textContent = 'Invia all\'agenzia';
    render();
  }
}

async function flushQueue() {
  const queue = readLS(LS.queue, []);
  if (!queue.length || !configured()) return;
  const remaining = [];
  let sent = 0;
  for (const mission of queue) {
    try {
      await pushMission(mission);
      sent += 1;
    } catch (err) {
      remaining.push(mission);
    }
  }
  writeLS(LS.queue, remaining);
  if (sent) {
    toast(sent + ' missione/i in coda locale inviate', 'ok');
    await loadState(false);
  }
}

/* ------------------------------------------------------------- rendering */

function setDot(kind, title) {
  const dot = $('status-dot');
  dot.className = 'dot ' + kind;
  dot.title = title;
}

function missionCard(mission, isLocal) {
  const status = isLocal ? 'local' : (mission.status || 'pending');
  const when = relativeTime(mission.finished_at || mission.created_at);
  return '<div class="mission ' + status + '" data-id="' + escapeHtml(mission.id) +
    '" data-local="' + (isLocal ? '1' : '0') + '">' +
    '<div class="mission-objective">' + escapeHtml(mission.objective) + '</div>' +
    '<div class="mission-meta">' +
      '<span class="tag">' + escapeHtml(mission.topology || 'team') + '</span>' +
      '<span>' + (isLocal ? 'in coda locale' : escapeHtml(status)) + '</span>' +
      (when ? '<span>' + escapeHtml(when) + '</span>' : '') +
      (mission.error ? '<span class="text-danger">errore</span>' : '') +
    '</div></div>';
}

function render() {
  const counts = state.counts || {};
  $('c-pending').textContent = counts.pending || 0;
  $('c-running').textContent = counts.running || 0;
  $('c-done').textContent = counts.done || 0;
  $('c-failed').textContent = counts.failed || 0;

  const queue = readLS(LS.queue, []);
  const missions = (state.missions || []).filter(m => filter === 'all' || m.status === filter);

  let html = '';
  if (filter === 'all' || filter === 'pending') {
    html += queue.map(m => missionCard(m, true)).join('');
  }
  html += missions.map(m => missionCard(m, false)).join('');
  $('missions').innerHTML = html || '<p class="empty">Nessuna missione da mostrare.</p>';

  $('footer-note').textContent = state.generated_at
    ? 'Stato del ' + new Date(state.generated_at).toLocaleString('it-IT')
    : 'Nessuno stato sincronizzato.';

  // Il pallino racconta la freschezza dei dati (lo imposta loadState): qui non
  // va sovrascritto, altrimenti lo stato "offline" resterebbe invisibile.
  $('send-hint').textContent = configured()
    ? 'La missione viene scritta nel repo ed eseguita dalla CI.'
    : 'Setup incompleto: le missioni restano in coda locale su questo dispositivo.';
}

function openMission(id, isLocal) {
  const mission = isLocal
    ? readLS(LS.queue, []).find(m => m.id === id)
    : (state.missions || []).find(m => m.id === id);
  if (!mission) return;

  $('detail-title').textContent = mission.objective;
  $('detail-meta').innerHTML =
    '<span class="tag">' + escapeHtml(mission.topology || 'team') + '</span>' +
    '<span>' + escapeHtml(isLocal ? 'in coda locale' : mission.status) + '</span>' +
    '<span class="tag">' + escapeHtml(mission.id) + '</span>';

  let body;
  if (mission.error) {
    body = '<div class="turn"><div class="turn-head">Errore</div><pre class="output">' +
      escapeHtml(mission.error) + '</pre></div>';
  } else if (mission.deliverable) {
    body = '<pre class="output">' + escapeHtml(mission.deliverable) + '</pre>';
  } else if (isLocal) {
    body = '<p class="empty">Non ancora inviata. Apri il setup, poi usa Aggiorna per svuotare la coda.</p>';
  } else {
    body = '<p class="empty">In attesa che l\'agenzia la esegua.</p>';
  }
  if (mission.context) {
    body += '<div class="turn" style="margin-top:16px"><div class="turn-head">Contesto</div><pre class="output">' +
      escapeHtml(mission.context) + '</pre></div>';
  }
  $('detail-body').innerHTML = body;
  $('btn-copy').dataset.text = mission.deliverable || '';
  $('modal-detail').classList.add('open');
}

/* ----------------------------------------------------------------- setup */

function openSettings() {
  const s = settings();
  $('set-owner').value = s.owner;
  $('set-repo').value = s.repo;
  $('set-branch').value = s.branch || 'main';
  $('set-token').value = s.token;
  $('modal-settings').classList.add('open');
}

function saveSettings() {
  writeLS(LS.settings, {
    owner: $('set-owner').value.trim(),
    repo: $('set-repo').value.trim(),
    branch: $('set-branch').value.trim() || 'main',
    token: $('set-token').value.trim()
  });
  $('modal-settings').classList.remove('open');
  toast('Setup salvato', 'ok');
  refresh(false);
}

async function refresh(announce) {
  await loadState(announce);
  await flushQueue();
  render();
}

/* ------------------------------------------------------------------ bind */

document.addEventListener('DOMContentLoaded', () => {
  $('btn-send').addEventListener('click', sendMission);
  $('btn-refresh').addEventListener('click', () => refresh(true));
  $('btn-settings').addEventListener('click', openSettings);
  $('btn-save-settings').addEventListener('click', saveSettings);

  $('btn-clear-token').addEventListener('click', () => {
    const s = settings();
    s.token = '';
    writeLS(LS.settings, s);
    $('set-token').value = '';
    toast('Token rimosso da questo dispositivo', 'ok');
    render();
  });

  $('btn-copy').addEventListener('click', event => {
    const text = event.currentTarget.dataset.text || '';
    if (!text) { toast('Nessun deliverable da copiare', 'err'); return; }
    navigator.clipboard.writeText(text)
      .then(() => toast('Copiato', 'ok'))
      .catch(() => toast('Copia non consentita dal browser', 'err'));
  });

  document.querySelectorAll('[data-close]').forEach(button => {
    button.addEventListener('click', () => {
      $(button.dataset.close).classList.remove('open');
    });
  });

  document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', event => {
      if (event.target === modal) modal.classList.remove('open');
    });
  });

  $('topology-pills').addEventListener('click', event => {
    const pill = event.target.closest('.filter-pill');
    if (!pill) return;
    document.querySelectorAll('#topology-pills .filter-pill')
      .forEach(p => p.classList.remove('active'));
    pill.classList.add('active');
    topology = pill.dataset.topology;
    $('topology-hint').textContent = TOPOLOGY_HINTS[topology];
    $('agent-row').style.display = topology === 'team' ? 'none' : 'block';
  });

  $('status-pills').addEventListener('click', event => {
    const pill = event.target.closest('.filter-pill');
    if (!pill) return;
    document.querySelectorAll('#status-pills .filter-pill')
      .forEach(p => p.classList.remove('active'));
    pill.classList.add('active');
    filter = pill.dataset.status;
    render();
  });

  $('missions').addEventListener('click', event => {
    const card = event.target.closest('.mission');
    if (card) openMission(card.dataset.id, card.dataset.local === '1');
  });

  // Stato dalla cache subito: la UI e' utile prima ancora della rete.
  state = readLS(LS.cache, state);
  render();
  refresh(false);

  window.addEventListener('online', () => refresh(false));

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js').catch(() => {});
  }
});
