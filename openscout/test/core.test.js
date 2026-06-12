import test from 'node:test';
import assert from 'node:assert/strict';
import { aggregateMatch, per90, computePercentiles, playerMinutes, positionGroup } from '../src/metrics.js';
import { similarPlayers } from '../src/similarity.js';
import { assess } from '../src/eligibility.js';

const P1 = { id: 1, name: 'Striker One' };
const P2 = { id: 2, name: 'Mid Two' };
const TEAM = { id: 10, name: 'Test FC' };

function fixtureLineups() {
  const stint = (pos) => [{ position: pos, from: '00:00', to: null, from_period: 1, to_period: 2, start_reason: 'Starting XI', end_reason: 'Final Whistle' }];
  return [{
    team_id: 10, team_name: 'Test FC',
    lineup: [
      { player_id: 1, player_name: 'Striker One', country: { name: 'Italy' }, cards: [], positions: stint('Center Forward') },
      { player_id: 2, player_name: 'Mid Two', country: { name: 'France' }, cards: [], positions: stint('Center Midfield') },
    ],
  }];
}

function fixtureEvents() {
  return [
    { id: 'p1', type: { name: 'Pass' }, minute: 10, second: 0, player: P2, team: TEAM,
      location: [50, 40], pass: { end_location: [80, 40], shot_assist: true, assisted_shot_id: 's1' } },
    { id: 's1', type: { name: 'Shot' }, minute: 10, second: 5, player: P1, team: TEAM,
      location: [110, 40], shot: { statsbomb_xg: 0.4, outcome: { name: 'Goal' } } },
    { id: 's2', type: { name: 'Shot' }, minute: 40, second: 0, player: P1, team: TEAM,
      location: [105, 35], shot: { statsbomb_xg: 0.1, outcome: { name: 'Off T' } } },
    { id: 'c1', type: { name: 'Carry' }, minute: 60, second: 0, player: P2, team: TEAM,
      location: [40, 40], carry: { end_location: [65, 40] } },
    { id: 'e', type: { name: 'Half End' }, minute: 90, second: 0 },
  ];
}

test('playerMinutes handles open-ended stints', () => {
  const minutes = playerMinutes(fixtureLineups(), 90);
  assert.equal(minutes.get(1), 90);
  assert.equal(minutes.get(2), 90);
});

test('aggregateMatch counts goals, xG, xA and progressive actions', () => {
  const players = new Map();
  aggregateMatch({ events: fixtureEvents(), lineups: fixtureLineups() }, players);
  const striker = players.get(1);
  assert.equal(striker.stats.goals, 1);
  assert.equal(striker.stats.shots, 2);
  assert.ok(Math.abs(striker.stats.xg - 0.5) < 1e-9);
  const mid = players.get(2);
  assert.equal(mid.stats.keyPasses, 1);
  assert.ok(Math.abs(mid.stats.xa - 0.4) < 1e-9);
  assert.equal(mid.stats.progressivePasses, 1);
  assert.equal(mid.stats.progressiveCarries, 1);
  assert.equal(positionGroup(striker), 'FW');
  assert.equal(positionGroup(mid), 'MF');
});

test('per90 scales by minutes', () => {
  const players = new Map();
  aggregateMatch({ events: fixtureEvents(), lineups: fixtureLineups() }, players);
  const r = per90(players.get(1));
  assert.ok(Math.abs(r.goals90 - 1) < 1e-9); // 1 goal in 90 minutes
});

test('computePercentiles and similarity run on a small pool', () => {
  const players = new Map();
  // Three matches to pass the 180' threshold
  for (let i = 0; i < 3; i++) aggregateMatch({ events: fixtureEvents(), lineups: fixtureLineups() }, players);
  const pct = computePercentiles(players, { minMinutes: 180 });
  assert.ok(pct.get(1));
  const sims = similarPlayers(1, players, { minMinutes: 180, limit: 5 });
  assert.equal(sims.length, 1);
  assert.equal(sims[0].player.id, 2);
});

test('eligibility: grandparent path with claimable citizenship', () => {
  const r = assess({
    name: 'Test Player',
    birth_country: 'Australia',
    citizenships: ['Australia'],
    grandparents_born_in: ['Malta'],
  }, 'MLT');
  assert.equal(r.status, 'NOW_AFTER_PAPERWORK');
  assert.ok(r.paths.some((p) => p.type === 'grandparent'));
  assert.equal(r.citizenship.status, 'CLAIMABLE');
});

test('eligibility: competitive caps block a switch', () => {
  const r = assess({
    name: 'Capped Player', birth_country: 'Italy', citizenships: ['Italy', 'San Marino'],
    caps_for_other_nation: { competitive: true },
  }, 'SMR');
  assert.equal(r.status, 'INELIGIBLE');
});

test('eligibility: residency what-if path', () => {
  const r = assess({
    name: 'Resident Player', birth_country: 'Italy', citizenships: ['Italy'],
    residency: { country: 'San Marino', years: 4, years_after_18: 3 },
  }, 'SMR');
  assert.equal(r.status, 'WHAT_IF');
  assert.ok(r.paths.some((p) => p.type === 'residency' && p.tier === 'WHAT_IF'));
});
