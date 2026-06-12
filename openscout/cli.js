#!/usr/bin/env node
// OpenScout CLI — open-data scouting, match analysis & eligibility intelligence.
import { writeFile } from 'node:fs/promises';
import { getCompetitions, getEvents, getLineups } from './src/statsbomb.js';
import { syncCompetition, loadAll, listDatasets } from './src/store.js';
import { computePercentiles, positionGroup, primaryPosition, rating } from './src/metrics.js';
import { similarPlayers } from './src/similarity.js';
import { analyzeMatch } from './src/match.js';
import { scanDataset, listFederations } from './src/eligibility.js';
import { playerReportHTML, matchReportHTML } from './src/report.js';
import { startServer } from './src/server.js';

const [cmd, ...args] = process.argv.slice(2);

const flag = (name, fallback) => {
  const i = args.indexOf(`--${name}`);
  return i >= 0 ? args[i + 1] : fallback;
};

// Positional args with `--flag value` pairs stripped out.
const positionals = (list) => {
  const out = [];
  for (let i = 0; i < list.length; i++) {
    if (list[i].startsWith('--')) { i += 1; continue; }
    out.push(list[i]);
  }
  return out;
};

function table(rows, cols) {
  const widths = cols.map((c) => Math.max(c.label.length, ...rows.map((r) => String(c.get(r)).length)));
  console.log(cols.map((c, i) => c.label.padEnd(widths[i])).join('  '));
  console.log(widths.map((w) => '-'.repeat(w)).join('  '));
  for (const r of rows) console.log(cols.map((c, i) => String(c.get(r)).padEnd(widths[i])).join('  '));
}

async function findPlayer(players, query) {
  const q = query.toLowerCase();
  const hits = [...players.values()].filter(
    (p) => p.name.toLowerCase().includes(q) || (p.fullName || '').toLowerCase().includes(q),
  );
  if (!hits.length) throw new Error(`No player matching '${query}'. Did you sync a competition? (openscout sync <comp> <season>)`);
  hits.sort((a, b) => b.stats.minutes - a.stats.minutes);
  return hits[0];
}

try {
  switch (cmd) {
    case 'competitions': {
      const comps = await getCompetitions();
      table(comps, [
        { label: 'COMP', get: (c) => c.competition_id },
        { label: 'SEASON', get: (c) => c.season_id },
        { label: 'NAME', get: (c) => c.competition_name },
        { label: 'YEAR', get: (c) => c.season_name },
        { label: 'COUNTRY', get: (c) => c.country_name },
        { label: 'GENDER', get: (c) => c.competition_gender },
      ]);
      console.log('\nSync one with: openscout sync <COMP> <SEASON>');
      break;
    }
    case 'sync': {
      const [comp, season] = args.map(Number);
      if (!comp || !season) throw new Error('Usage: openscout sync <competition_id> <season_id>');
      process.stdout.write(`Syncing competition ${comp}, season ${season}...\n`);
      const r = await syncCompetition(comp, season, {
        onProgress: (done, total) => process.stdout.write(`\r  matches ${done}/${total}`),
      });
      console.log(`\nDone: ${r.matches} matches (${r.failed} failed), ${r.players} players aggregated.`);
      break;
    }
    case 'datasets': {
      const ds = await listDatasets();
      if (!ds.length) { console.log('No datasets synced yet. Run: openscout competitions'); break; }
      table(ds, [
        { label: 'COMP', get: (d) => d.competition_id },
        { label: 'SEASON', get: (d) => d.season_id },
        { label: 'NAME', get: (d) => `${d.competition} ${d.season}` },
        { label: 'MATCHES', get: (d) => d.matches },
        { label: 'PLAYERS', get: (d) => d.players },
      ]);
      break;
    }
    case 'players': {
      const { players } = await loadAll();
      const minMinutes = Number(flag('min-minutes', 180));
      const group = flag('pos');
      const pct = computePercentiles(players, { minMinutes });
      let list = [...players.values()].filter((p) => p.stats.minutes >= minMinutes);
      if (group) list = list.filter((p) => positionGroup(p) === group.toUpperCase());
      const rows = list.map((p) => {
        const c = pct.get(p.id);
        return { p, c, os: c ? rating(c.percentiles, c.group) : 0 };
      }).sort((a, b) => b.os - a.os).slice(0, Number(flag('limit', 25)));
      table(rows, [
        { label: 'OS', get: (r) => r.os },
        { label: 'PLAYER', get: (r) => r.p.name },
        { label: 'TEAM', get: (r) => r.p.team },
        { label: 'POS', get: (r) => positionGroup(r.p) },
        { label: 'MIN', get: (r) => Math.round(r.p.stats.minutes) },
        { label: 'G', get: (r) => r.p.stats.goals },
        { label: 'A', get: (r) => r.p.stats.assists },
        { label: 'npxG/90', get: (r) => r.c.per90.npxg90.toFixed(2) },
        { label: 'xA/90', get: (r) => r.c.per90.xa90.toFixed(2) },
      ]);
      break;
    }
    case 'player': {
      const { players } = await loadAll();
      const p = await findPlayer(players, positionals(args).join(' '));
      const pct = computePercentiles(players);
      const c = pct.get(p.id);
      console.log(`\n${p.name} — ${p.team} — ${primaryPosition(p)} — ${p.country || '?'}`);
      console.log(`Minutes: ${Math.round(p.stats.minutes)} | Matches: ${p.stats.matches} | Goals: ${p.stats.goals} | Assists: ${p.stats.assists}`);
      if (c) {
        console.log(`OpenScout rating: ${rating(c.percentiles, c.group)} (vs ${c.group} group)\n`);
        const entries = Object.entries(c.percentiles).sort((a, b) => b[1] - a[1]);
        for (const [k, v] of entries) {
          const bar = '█'.repeat(Math.round(v / 4)).padEnd(25, '·');
          console.log(`  ${k.padEnd(18)} ${bar} ${Math.round(v)}`);
        }
      } else {
        console.log('(fewer than 180 minutes — percentiles unavailable)');
      }
      break;
    }
    case 'similar': {
      const { players } = await loadAll();
      const p = await findPlayer(players, positionals(args).join(' '));
      console.log(`\nPlayers with a similar statistical profile to ${p.name} (${p.team}):\n`);
      const sims = similarPlayers(p.id, players, { limit: Number(flag('limit', 10)) });
      table(sims, [
        { label: 'MATCH', get: (s) => `${(s.similarity * 100).toFixed(0)}%` },
        { label: 'PLAYER', get: (s) => s.player.name },
        { label: 'TEAM', get: (s) => s.player.team },
        { label: 'POS', get: (s) => s.group },
        { label: 'MIN', get: (s) => Math.round(s.player.stats.minutes) },
      ]);
      break;
    }
    case 'match': {
      const { matches } = await loadAll();
      if (!args[0] || args[0] === 'list') {
        table(matches.slice(0, Number(flag('limit', 30))), [
          { label: 'ID', get: (m) => m.match_id },
          { label: 'DATE', get: (m) => m.date },
          { label: 'MATCH', get: (m) => `${m.home} ${m.score} ${m.away}` },
          { label: 'STAGE', get: (m) => m.stage || '' },
        ]);
        break;
      }
      const id = Number(args[0]);
      const meta = matches.find((m) => m.match_id === id);
      if (!meta) throw new Error(`Match ${id} not in synced datasets`);
      const [events, lineups] = await Promise.all([getEvents(id), getLineups(id)]);
      const info = {
        match_id: id, match_date: meta.date,
        home_team: { home_team_name: meta.home }, away_team: { away_team_name: meta.away },
        home_score: meta.score.split('-')[0], away_score: meta.score.split('-')[1],
        competition_stage: { name: meta.stage },
      };
      const a = analyzeMatch(info, events, lineups);
      console.log(`\n${a.match.home} ${a.match.score} ${a.match.away} — xG ${a.xgRace[0].total} : ${a.xgRace[1].total}\n`);
      console.log('Top performers:');
      table(a.topPerformers, [
        { label: 'SCORE', get: (p) => p.score },
        { label: 'PLAYER', get: (p) => p.name },
        { label: 'TEAM', get: (p) => p.team },
      ]);
      console.log(`\nFull visual report: openscout report match ${id}`);
      break;
    }
    case 'eligibility': {
      const fed = args[0];
      if (!fed) {
        console.log('Available federations:');
        for (const f of listFederations()) console.log(`  ${f.code}  ${f.name}`);
        console.log('\nUsage: openscout eligibility <CODE>');
        break;
      }
      const { players } = await loadAll();
      const scan = scanDataset(players, fed, { minMinutes: Number(flag('min-minutes', 90)) });
      console.log(`\nEligibility screening for ${scan.federation}`);
      console.log(`Diaspora pool: ${scan.diaspora_countries.join(', ')}`);
      console.log(`${scan.notes}\n`);
      table(scan.candidates.slice(0, Number(flag('limit', 25))), [
        { label: 'PLAYER', get: (c) => c.name },
        { label: 'NATIONALITY', get: (c) => c.nationality },
        { label: 'TEAM', get: (c) => c.team },
        { label: 'POS', get: (c) => c.position },
        { label: 'MIN', get: (c) => c.minutes },
        { label: 'npxG+xA/90', get: (c) => c.npxgPlusXa90 },
      ]);
      console.log('\nNext step: run the Radar SMR RAG deep-dive on shortlisted names to verify ancestry.');
      break;
    }
    case 'report': {
      const kind = args[0];
      const out = flag('o');
      const { players, matches } = await loadAll();
      if (kind === 'player') {
        const p = await findPlayer(players, positionals(args.slice(1)).join(' '));
        const file = out || `report-${p.name.replace(/\W+/g, '-').toLowerCase()}.html`;
        await writeFile(file, playerReportHTML(p.id, players));
        console.log(`Report written: ${file}`);
      } else if (kind === 'match') {
        const id = Number(args[1]);
        const meta = matches.find((m) => m.match_id === id);
        if (!meta) throw new Error(`Match ${id} not in synced datasets`);
        const [events, lineups] = await Promise.all([getEvents(id), getLineups(id)]);
        const info = {
          match_id: id, match_date: meta.date,
          home_team: { home_team_name: meta.home }, away_team: { away_team_name: meta.away },
          home_score: meta.score.split('-')[0], away_score: meta.score.split('-')[1],
          competition_stage: { name: meta.stage },
        };
        const file = out || `report-match-${id}.html`;
        await writeFile(file, matchReportHTML(analyzeMatch(info, events, lineups)));
        console.log(`Report written: ${file}`);
      } else {
        throw new Error('Usage: openscout report player <name> | report match <id> [--o file.html]');
      }
      break;
    }
    case 'serve': {
      const port = Number(flag('port', process.env.PORT || 3030));
      await startServer({ port });
      console.log(`OpenScout running at http://localhost:${port}`);
      break;
    }
    default:
      console.log(`OpenScout — open-data scouting & match analysis

Usage:
  openscout competitions                      list free competitions (StatsBomb open data)
  openscout sync <comp_id> <season_id>        download & aggregate one competition
  openscout datasets                          list synced datasets
  openscout players [--pos FW] [--limit 25]   ranked player table
  openscout player <name>                     player profile with percentiles
  openscout similar <name>                    statistically similar players
  openscout match [list | <id>]               match analysis
  openscout eligibility [CODE]                national-team eligibility screening
  openscout report player <name> [--o f.html] shareable HTML scouting report
  openscout report match <id> [--o f.html]    shareable HTML match report
  openscout serve [--port 3030]               web UI + JSON API`);
  }
} catch (err) {
  console.error(`Error: ${err.message}`);
  process.exit(1);
}
