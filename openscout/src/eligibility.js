// Eligibility Intelligence: which players could represent a national federation?
//
// Two layers:
//  1. assess(profile, federation)  — rules engine applying FIFA eligibility
//     paths (RGAS art. 6-8) + the federation's citizenship law to a researched
//     player profile (ancestry, birthplace, residency). This generalizes the
//     Radar SMR San Marino logic to any federation.
//  2. scanDataset(players, federation) — fast screening of a synced open-data
//     dataset: flags players whose nationality matches the federation's
//     diaspora countries as ancestry-investigation candidates.
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { per90, positionGroup } from './metrics.js';

const FEDERATIONS = JSON.parse(
  readFileSync(path.join(path.dirname(fileURLToPath(import.meta.url)), 'federations.json'), 'utf8'),
);

export const listFederations = () =>
  Object.entries(FEDERATIONS).map(([code, f]) => ({ code, name: f.name }));

export const getFederation = (code) => {
  const f = FEDERATIONS[code.toUpperCase()];
  if (!f) throw new Error(`Unknown federation '${code}'. Available: ${Object.keys(FEDERATIONS).join(', ')}`);
  return { code: code.toUpperCase(), ...f };
};

/**
 * profile = {
 *   name, birth_country, citizenships: [..],
 *   parents_born_in: [..countries..], grandparents_born_in: [..],
 *   residency: { country, years, years_after_18 },
 *   caps_for_other_nation: { competitive: bool }
 * }
 */
export function assess(profile, federationCode) {
  const fed = getFederation(federationCode);
  const target = fed.fifa_country;
  const law = fed.citizenship_law;
  const paths = [];
  const has = (arr, c) => (arr || []).includes(c);
  const hasCitizenship = has(profile.citizenships, target);

  if (profile.caps_for_other_nation?.competitive) {
    return {
      federation: fed.name, player: profile.name, status: 'INELIGIBLE',
      score: 0, paths: [],
      summary: 'Already capped competitively for another senior national team (FIFA RGAS art. 8: switch not possible after competitive senior appearance, save for the one-time switch conditions).',
    };
  }

  // FIFA territorial-link paths (a nationality/citizenship is always required on top)
  if (profile.birth_country === target) {
    paths.push({ type: 'birthplace', tier: 'NOW', detail: `Born in ${target}` });
  }
  if (has(profile.parents_born_in, target)) {
    paths.push({ type: 'parent', tier: 'NOW', detail: `Biological parent born in ${target}` });
  }
  if (has(profile.grandparents_born_in, target)) {
    paths.push({ type: 'grandparent', tier: 'NOW', detail: `Biological grandparent born in ${target}` });
  }
  const res = profile.residency;
  if (res?.country === target) {
    if ((res.years_after_18 ?? 0) >= 5) {
      paths.push({ type: 'residency', tier: 'NOW', detail: '5+ years of residence after age 18 (FIFA art. 6.1d)' });
    } else if ((res.years_after_18 ?? 0) > 0) {
      const remaining = 5 - res.years_after_18;
      paths.push({ type: 'residency', tier: 'WHAT_IF', detail: `Residency path: ~${remaining.toFixed(1)} more years needed after age 18` });
    }
  }

  // Citizenship layer
  let citizenship;
  if (hasCitizenship) {
    citizenship = { status: 'HELD', detail: `Already holds ${target} citizenship` };
  } else {
    const generationOk =
      (has(profile.parents_born_in, target) && law.jus_sanguinis_generations >= 1) ||
      (has(profile.grandparents_born_in, target) && law.jus_sanguinis_generations >= 2);
    if (generationOk) {
      citizenship = { status: 'CLAIMABLE', detail: `Citizenship claimable by descent (jus sanguinis, up to ${law.jus_sanguinis_generations} generation(s))` };
    } else if (res?.country === target) {
      const needed = law.naturalization_residency_years - (res.years ?? 0);
      citizenship = {
        status: needed <= 0 ? 'CLAIMABLE' : 'LONG_SHOT',
        detail: needed <= 0
          ? 'Naturalization residency requirement already met'
          : `Naturalization needs ${needed} more year(s) of residence` + (law.dual_citizenship_allowed ? '' : ' and renouncing current citizenship'),
      };
    } else {
      citizenship = { status: 'NONE', detail: 'No known citizenship route' };
    }
  }

  const nowPaths = paths.filter((p) => p.tier === 'NOW');
  let status, score;
  if (nowPaths.length && citizenship.status === 'HELD') { status = 'NOW'; score = 95; }
  else if (nowPaths.length && citizenship.status === 'CLAIMABLE') { status = 'NOW_AFTER_PAPERWORK'; score = 80; }
  else if (paths.length && citizenship.status !== 'NONE') { status = 'WHAT_IF'; score = 55; }
  else if (citizenship.status === 'CLAIMABLE' || citizenship.status === 'LONG_SHOT') { status = 'WHAT_IF'; score = 35; }
  else { status = 'INELIGIBLE'; score = 5; }

  return {
    federation: fed.name, player: profile.name, status, score,
    paths, citizenship,
    summary: status === 'INELIGIBLE'
      ? 'No FIFA territorial link or citizenship route found.'
      : `${status}: ${nowPaths[0]?.detail || paths[0]?.detail || citizenship.detail}. ${citizenship.detail}.`,
  };
}

// Screen a synced dataset: rank diaspora-nationality players as candidates for
// an ancestry deep-dive (the Radar SMR RAG pipeline is the follow-up step).
export function scanDataset(players, federationCode, { minMinutes = 90 } = {}) {
  const fed = getFederation(federationCode);
  const diaspora = new Set(fed.diaspora_countries);
  const candidates = [];
  for (const p of players.values()) {
    if (p.stats.minutes < minMinutes || !p.country) continue;
    if (p.country === fed.fifa_country) continue;
    if (!diaspora.has(p.country)) continue;
    const r = per90(p);
    candidates.push({
      id: p.id, name: p.name, team: p.team, nationality: p.country,
      position: positionGroup(p), minutes: Math.round(p.stats.minutes),
      npxgPlusXa90: +r.npxgPlusXa90.toFixed(2),
      progActions90: +(r.progPasses90 + r.progCarries90).toFixed(1),
      action: 'INVESTIGATE_ANCESTRY',
    });
  }
  candidates.sort((a, b) => b.npxgPlusXa90 - a.npxgPlusXa90);
  return { federation: fed.name, diaspora_countries: fed.diaspora_countries, notes: fed.scouting_notes, candidates };
}
