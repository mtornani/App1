// Zero-dependency HTTP server: JSON API + single-page web UI + HTML reports.
import http from 'node:http';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { getCompetitions, getMatches, getEvents, getLineups } from './statsbomb.js';
import { loadAll, listDatasets, syncCompetition } from './store.js';
import { computePercentiles, per90, positionGroup, primaryPosition, rating } from './metrics.js';
import { similarPlayers } from './similarity.js';
import { analyzeMatch } from './match.js';
import { listFederations, scanDataset, assess } from './eligibility.js';
import { playerReportHTML, matchReportHTML } from './report.js';

const WEB = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'web');

export async function startServer({ port = 3030 } = {}) {
  let cache = await loadAll(); // { players, matches }
  const reload = async () => { cache = await loadAll(); };

  const json = (res, code, body) => {
    res.writeHead(code, { 'content-type': 'application/json' });
    res.end(JSON.stringify(body));
  };
  const html = (res, body) => {
    res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
    res.end(body);
  };

  const playerSummary = (p, ctx) => ({
    id: p.id, name: p.name, team: p.team, country: p.country,
    position: primaryPosition(p), group: ctx?.group || positionGroup(p),
    minutes: Math.round(p.stats.minutes), matches: p.stats.matches,
    goals: p.stats.goals, assists: p.stats.assists,
    npxg90: ctx ? +ctx.per90.npxg90.toFixed(2) : null,
    xa90: ctx ? +ctx.per90.xa90.toFixed(2) : null,
    rating: ctx ? rating(ctx.percentiles, ctx.group) : null,
  });

  const server = http.createServer(async (req, res) => {
    const url = new URL(req.url, `http://${req.headers.host}`);
    const route = url.pathname;
    try {
      if (route === '/' || route === '/index.html') {
        return html(res, await readFile(path.join(WEB, 'index.html'), 'utf8'));
      }
      if (route === '/api/competitions') {
        const comps = await getCompetitions();
        return json(res, 200, comps.map((c) => ({
          competition_id: c.competition_id, season_id: c.season_id,
          name: c.competition_name, season: c.season_name,
          country: c.country_name, gender: c.competition_gender,
        })));
      }
      if (route === '/api/datasets') return json(res, 200, await listDatasets());
      if (route === '/api/sync' && req.method === 'POST') {
        const comp = Number(url.searchParams.get('competition_id'));
        const season = Number(url.searchParams.get('season_id'));
        const result = await syncCompetition(comp, season);
        await reload();
        return json(res, 200, { ok: true, matches: result.matches, players: result.players, failed: result.failed });
      }
      if (route === '/api/players') {
        const q = (url.searchParams.get('q') || '').toLowerCase();
        const group = url.searchParams.get('group');
        const minMinutes = Number(url.searchParams.get('min_minutes') || 180);
        const percentiles = computePercentiles(cache.players, { minMinutes });
        let list = [...cache.players.values()]
          .filter((p) => p.stats.minutes >= minMinutes)
          .map((p) => playerSummary(p, percentiles.get(p.id)));
        if (q) list = list.filter((p) => p.name.toLowerCase().includes(q) || (p.team || '').toLowerCase().includes(q));
        if (group) list = list.filter((p) => p.group === group);
        list.sort((a, b) => (b.rating ?? 0) - (a.rating ?? 0));
        return json(res, 200, list.slice(0, 300));
      }
      const playerMatch = route.match(/^\/api\/player\/(\d+)$/);
      if (playerMatch) {
        const id = Number(playerMatch[1]);
        const p = cache.players.get(id);
        if (!p) return json(res, 404, { error: 'player not found' });
        const percentiles = computePercentiles(cache.players);
        const ctx = percentiles.get(id);
        return json(res, 200, {
          ...playerSummary(p, ctx),
          stats: p.stats, per90: ctx?.per90 || per90(p), percentiles: ctx?.percentiles || null,
          similar: similarPlayers(id, cache.players, { limit: 8 }).map((s) => ({
            id: s.player.id, name: s.player.name, team: s.player.team, group: s.group,
            similarity: +(s.similarity * 100).toFixed(0),
          })),
        });
      }
      if (route === '/api/matches') return json(res, 200, cache.matches.slice(0, 400));
      const matchMatch = route.match(/^\/api\/match\/(\d+)$/);
      if (matchMatch) {
        const id = Number(matchMatch[1]);
        const meta = cache.matches.find((m) => m.match_id === id);
        if (!meta) return json(res, 404, { error: 'match not in synced datasets' });
        const [events, lineups] = await Promise.all([getEvents(id), getLineups(id)]);
        const info = {
          match_id: id, match_date: meta.date,
          home_team: { home_team_name: meta.home }, away_team: { away_team_name: meta.away },
          home_score: meta.score.split('-')[0], away_score: meta.score.split('-')[1],
          competition_stage: { name: meta.stage },
        };
        return json(res, 200, analyzeMatch(info, events, lineups));
      }
      if (route === '/api/federations') return json(res, 200, listFederations());
      const eligMatch = route.match(/^\/api\/eligibility\/(\w+)$/);
      if (eligMatch) return json(res, 200, scanDataset(cache.players, eligMatch[1]));
      if (route === '/api/assess' && req.method === 'POST') {
        const body = await new Promise((resolve) => {
          let data = '';
          req.on('data', (c) => { data += c; });
          req.on('end', () => resolve(data));
        });
        const { profile, federation } = JSON.parse(body);
        return json(res, 200, assess(profile, federation));
      }
      const reportPlayer = route.match(/^\/report\/player\/(\d+)$/);
      if (reportPlayer) return html(res, playerReportHTML(Number(reportPlayer[1]), cache.players));
      const reportMatch = route.match(/^\/report\/match\/(\d+)$/);
      if (reportMatch) {
        const id = Number(reportMatch[1]);
        const meta = cache.matches.find((m) => m.match_id === id);
        if (!meta) return json(res, 404, { error: 'match not in synced datasets' });
        const [events, lineups] = await Promise.all([getEvents(id), getLineups(id)]);
        const info = {
          match_id: id, match_date: meta.date,
          home_team: { home_team_name: meta.home }, away_team: { away_team_name: meta.away },
          home_score: meta.score.split('-')[0], away_score: meta.score.split('-')[1],
          competition_stage: { name: meta.stage },
        };
        return html(res, matchReportHTML(analyzeMatch(info, events, lineups)));
      }
      json(res, 404, { error: 'not found' });
    } catch (err) {
      json(res, 500, { error: err.message });
    }
  });

  await new Promise((resolve) => server.listen(port, resolve));
  return server;
}
