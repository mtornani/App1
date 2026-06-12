// Fetch + cache layer for the StatsBomb open-data repository.
// All responses are cached on disk so repeated runs cost zero bandwidth.
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const BASE = 'https://raw.githubusercontent.com/statsbomb/open-data/master/data';
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'data', 'cache');

async function fetchJSON(relPath, { force = false } = {}) {
  const cacheFile = path.join(ROOT, relPath);
  if (!force && existsSync(cacheFile)) {
    return JSON.parse(await readFile(cacheFile, 'utf8'));
  }
  const res = await fetch(`${BASE}/${relPath}`);
  if (!res.ok) throw new Error(`StatsBomb fetch failed (${res.status}): ${relPath}`);
  const text = await res.text();
  await mkdir(path.dirname(cacheFile), { recursive: true });
  await writeFile(cacheFile, text);
  return JSON.parse(text);
}

export const getCompetitions = (opts) => fetchJSON('competitions.json', opts);
export const getMatches = (competitionId, seasonId, opts) =>
  fetchJSON(`matches/${competitionId}/${seasonId}.json`, opts);
export const getLineups = (matchId, opts) => fetchJSON(`lineups/${matchId}.json`, opts);
export const getEvents = (matchId, opts) => fetchJSON(`events/${matchId}.json`, opts);

// Fetch many matches with bounded concurrency; onProgress(done, total) is optional.
export async function fetchMatchData(matchIds, { concurrency = 6, onProgress } = {}) {
  const results = new Map();
  let done = 0;
  const queue = [...matchIds];
  async function worker() {
    while (queue.length) {
      const id = queue.shift();
      try {
        const [events, lineups] = await Promise.all([getEvents(id), getLineups(id)]);
        results.set(id, { events, lineups });
      } catch (err) {
        results.set(id, { error: err.message });
      }
      done += 1;
      onProgress?.(done, matchIds.length);
    }
  }
  await Promise.all(Array.from({ length: Math.min(concurrency, matchIds.length) }, worker));
  return results;
}
