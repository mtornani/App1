// Dataset persistence: synced competitions are aggregated once and saved as
// compact JSON so the app starts instantly without re-parsing event files.
import { mkdir, readFile, writeFile, readdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { getMatches, fetchMatchData } from './statsbomb.js';
import { aggregateMatch } from './metrics.js';

const DATASETS = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'data', 'datasets');

export async function syncCompetition(competitionId, seasonId, { onProgress } = {}) {
  const matches = await getMatches(competitionId, seasonId);
  const ids = matches.map((m) => m.match_id);
  const players = new Map();
  const data = await fetchMatchData(ids, { onProgress });
  let failed = 0;
  for (const id of ids) {
    const d = data.get(id);
    if (!d || d.error) { failed += 1; continue; }
    aggregateMatch(d, players);
  }
  const meta = matches[0] || {};
  const dataset = {
    competition_id: competitionId,
    season_id: seasonId,
    competition: meta.competition?.competition_name,
    season: meta.season?.season_name,
    synced_at: new Date().toISOString(),
    matches: matches.map((m) => ({
      match_id: m.match_id, date: m.match_date,
      home: m.home_team.home_team_name, away: m.away_team.away_team_name,
      score: `${m.home_score}-${m.away_score}`, stage: m.competition_stage?.name,
    })),
    players: [...players.values()],
  };
  await mkdir(DATASETS, { recursive: true });
  await writeFile(path.join(DATASETS, `${competitionId}-${seasonId}.json`), JSON.stringify(dataset));
  return { matches: matches.length, failed, players: players.size, dataset };
}

export async function listDatasets() {
  if (!existsSync(DATASETS)) return [];
  const files = (await readdir(DATASETS)).filter((f) => f.endsWith('.json'));
  const out = [];
  for (const f of files) {
    const d = JSON.parse(await readFile(path.join(DATASETS, f), 'utf8'));
    out.push({
      competition_id: d.competition_id, season_id: d.season_id,
      competition: d.competition, season: d.season,
      matches: d.matches.length, players: d.players.length, synced_at: d.synced_at,
    });
  }
  return out;
}

// Merge every synced dataset into one players Map (stats summed across
// competitions) plus a global match index.
export async function loadAll() {
  const players = new Map();
  const matches = [];
  if (!existsSync(DATASETS)) return { players, matches };
  const files = (await readdir(DATASETS)).filter((f) => f.endsWith('.json'));
  for (const f of files) {
    const d = JSON.parse(await readFile(path.join(DATASETS, f), 'utf8'));
    for (const m of d.matches) matches.push({ ...m, competition: d.competition, season: d.season });
    for (const p of d.players) {
      const existing = players.get(p.id);
      if (!existing) { players.set(p.id, structuredClone(p)); continue; }
      for (const [k, v] of Object.entries(p.stats)) existing.stats[k] += v;
      for (const [pos, mins] of Object.entries(p.positions)) {
        existing.positions[pos] = (existing.positions[pos] || 0) + mins;
      }
    }
  }
  matches.sort((a, b) => (a.date < b.date ? 1 : -1));
  return { players, matches };
}
