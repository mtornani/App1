// "Find me another X": cosine similarity over z-scored per-90 profiles.
import { per90, positionGroup } from './metrics.js';

const VECTOR_KEYS = [
  'npxg90', 'xa90', 'shots90', 'keyPasses90', 'passes90', 'passPct',
  'progPasses90', 'passesIntoBox90', 'crosses90', 'progCarries90', 'carryDistance90',
  'dribbles90', 'pressures90', 'tackles90', 'interceptions90', 'recoveries90',
  'blocks90', 'clearances90', 'aerialsWon90', 'foulsWon90',
];

export function similarPlayers(targetId, players, { minMinutes = 180, limit = 10, sameGroupOnly = false } = {}) {
  const pool = [...players.values()].filter((p) => p.stats.minutes >= minMinutes);
  const target = players.get(targetId);
  if (!target) throw new Error(`Player ${targetId} not in dataset`);
  if (!pool.some((p) => p.id === targetId)) pool.push(target);

  const rates = pool.map((p) => ({ p, r: per90(p) }));
  // z-score each dimension across the pool
  const stats = VECTOR_KEYS.map((k) => {
    const vals = rates.map((x) => x.r[k]);
    const mean = vals.reduce((a, b) => a + b, 0) / vals.length;
    const sd = Math.sqrt(vals.reduce((a, v) => a + (v - mean) ** 2, 0) / vals.length) || 1;
    return { k, mean, sd };
  });
  const vectors = new Map(rates.map(({ p, r }) => [
    p.id, stats.map(({ k, mean, sd }) => (r[k] - mean) / sd),
  ]));

  const tv = vectors.get(targetId);
  const tGroup = positionGroup(target);
  const scored = [];
  for (const { p } of rates) {
    if (p.id === targetId) continue;
    if (sameGroupOnly && positionGroup(p) !== tGroup) continue;
    const v = vectors.get(p.id);
    let dot = 0, na = 0, nb = 0;
    for (let i = 0; i < tv.length; i++) { dot += tv[i] * v[i]; na += tv[i] ** 2; nb += v[i] ** 2; }
    const sim = dot / (Math.sqrt(na) * Math.sqrt(nb) || 1);
    scored.push({ player: p, similarity: sim, group: positionGroup(p) });
  }
  scored.sort((a, b) => b.similarity - a.similarity);
  return scored.slice(0, limit);
}
