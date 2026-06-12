// Turns raw StatsBomb events + lineups into per-player aggregated metrics.

const POSITION_GROUPS = {
  Goalkeeper: 'GK',
  'Right Center Back': 'CB', 'Left Center Back': 'CB', 'Center Back': 'CB',
  'Right Back': 'FB', 'Left Back': 'FB', 'Right Wing Back': 'FB', 'Left Wing Back': 'FB',
  'Center Defensive Midfield': 'MF', 'Right Defensive Midfield': 'MF', 'Left Defensive Midfield': 'MF',
  'Center Midfield': 'MF', 'Right Center Midfield': 'MF', 'Left Center Midfield': 'MF',
  'Center Attacking Midfield': 'AM', 'Right Attacking Midfield': 'AM', 'Left Attacking Midfield': 'AM',
  'Right Midfield': 'AM', 'Left Midfield': 'AM',
  'Right Wing': 'AM', 'Left Wing': 'AM',
  'Center Forward': 'FW', 'Right Center Forward': 'FW', 'Left Center Forward': 'FW',
  'Secondary Striker': 'FW', Striker: 'FW',
};

export const GROUP_LABELS = {
  GK: 'Goalkeeper', CB: 'Centre-back', FB: 'Full-back / Wing-back',
  MF: 'Central / Defensive Midfield', AM: 'Attacking Mid / Winger', FW: 'Forward',
};

function parseClock(str) {
  if (!str) return null;
  const [m, s] = str.split(':').map(Number);
  return m + s / 60;
}

// Minutes per player from lineup position stints. `matchEnd` (in minutes) caps
// open-ended stints (to: null = on pitch at the final whistle).
export function playerMinutes(lineups, matchEnd) {
  const minutes = new Map();
  for (const team of lineups) {
    for (const p of team.lineup) {
      let total = 0;
      for (const stint of p.positions || []) {
        const from = parseClock(stint.from) ?? 0;
        const to = parseClock(stint.to) ?? matchEnd;
        total += Math.max(0, to - from);
      }
      if (total > 0) minutes.set(p.player_id, total);
    }
  }
  return minutes;
}

function blankStats() {
  return {
    minutes: 0, matches: 0, starts: 0,
    goals: 0, npGoals: 0, xg: 0, npxg: 0, shots: 0, shotsOnTarget: 0,
    assists: 0, xa: 0, keyPasses: 0,
    passes: 0, passesCompleted: 0, progressivePasses: 0, passesIntoBox: 0, crosses: 0,
    carries: 0, progressiveCarries: 0, carryDistance: 0, dribbles: 0, dribblesCompleted: 0,
    pressures: 0, counterpressures: 0, tackles: 0, tacklesWon: 0,
    interceptions: 0, recoveries: 0, blocks: 0, clearances: 0, aerialsWon: 0,
    foulsWon: 0, foulsCommitted: 0, dispossessed: 0, miscontrols: 0,
    yellowCards: 0, redCards: 0,
    saves: 0, goalsConceded: 0, psxgFaced: 0,
  };
}

const IN_BOX = ([x, y]) => x >= 102 && y >= 18 && y <= 62;

// Aggregate one match's events into the players map keyed by player_id.
export function aggregateMatch({ events, lineups }, players) {
  const matchEnd = events.reduce((m, e) => Math.max(m, e.minute + e.second / 60), 90);
  const minutes = playerMinutes(lineups, matchEnd);
  const shotsById = new Map();
  for (const e of events) if (e.type.name === 'Shot') shotsById.set(e.id, e);

  const touch = (e) => {
    const id = e.player?.id;
    if (id == null) return null;
    let p = players.get(id);
    if (!p) {
      p = { id, name: e.player.name, team: e.team?.name, positions: {}, country: null, stats: blankStats() };
      players.set(id, p);
    }
    return p;
  };

  // Roster metadata: nickname, nationality, position stints, starts.
  for (const team of lineups) {
    for (const lp of team.lineup) {
      const mins = minutes.get(lp.player_id);
      if (!mins) continue;
      let p = players.get(lp.player_id);
      if (!p) {
        p = { id: lp.player_id, name: lp.player_name, team: team.team_name, positions: {}, country: null, stats: blankStats() };
        players.set(lp.player_id, p);
      }
      p.name = lp.player_nickname || lp.player_name;
      p.fullName = lp.player_name;
      p.team = team.team_name;
      p.country = lp.country?.name || p.country;
      p.stats.minutes += mins;
      p.stats.matches += 1;
      for (const stint of lp.positions || []) {
        const from = parseClock(stint.from) ?? 0;
        const to = parseClock(stint.to) ?? matchEnd;
        p.positions[stint.position] = (p.positions[stint.position] || 0) + Math.max(0, to - from);
        if (stint.start_reason === 'Starting XI') p.stats.starts += 1;
      }
      for (const card of lp.cards || []) {
        if (/Yellow/.test(card.card_type)) p.stats.yellowCards += 1;
        if (/Red/.test(card.card_type)) p.stats.redCards += 1;
      }
    }
  }

  for (const e of events) {
    const p = touch(e);
    if (!p) continue;
    const s = p.stats;
    switch (e.type.name) {
      case 'Shot': {
        const shot = e.shot;
        const isPen = shot.type?.name === 'Penalty';
        s.shots += 1;
        s.xg += shot.statsbomb_xg || 0;
        if (!isPen) s.npxg += shot.statsbomb_xg || 0;
        const out = shot.outcome?.name;
        if (out === 'Goal') { s.goals += 1; if (!isPen) s.npGoals += 1; }
        if (out === 'Goal' || out === 'Saved' || out === 'Saved To Post') s.shotsOnTarget += 1;
        break;
      }
      case 'Pass': {
        const pass = e.pass;
        if (['Throw-in', 'Corner', 'Free Kick', 'Goal Kick', 'Kick Off'].includes(pass.type?.name) && pass.type?.name === 'Throw-in') break;
        s.passes += 1;
        const completed = !pass.outcome;
        if (completed) s.passesCompleted += 1;
        if (pass.goal_assist) s.assists += 1;
        if (pass.shot_assist || pass.goal_assist) {
          s.keyPasses += 1;
          const shot = shotsById.get(pass.assisted_shot_id);
          if (shot) s.xa += shot.shot.statsbomb_xg || 0;
        }
        if (pass.cross) s.crosses += 1;
        if (completed && e.location && pass.end_location) {
          const gain = pass.end_location[0] - e.location[0];
          if (gain >= 10 && pass.end_location[0] >= 60) s.progressivePasses += 1;
          if (IN_BOX(pass.end_location) && !IN_BOX(e.location)) s.passesIntoBox += 1;
        }
        break;
      }
      case 'Carry': {
        s.carries += 1;
        if (e.location && e.carry?.end_location) {
          const gain = e.carry.end_location[0] - e.location[0];
          if (gain > 0) s.carryDistance += gain;
          if (gain >= 10) s.progressiveCarries += 1;
        }
        break;
      }
      case 'Dribble':
        s.dribbles += 1;
        if (e.dribble?.outcome?.name === 'Complete') s.dribblesCompleted += 1;
        break;
      case 'Pressure':
        s.pressures += 1;
        if (e.counterpress) s.counterpressures += 1;
        break;
      case 'Duel': {
        const dt = e.duel?.type?.name;
        if (dt === 'Tackle') {
          s.tackles += 1;
          if (/^(Won|Success)/.test(e.duel.outcome?.name || '')) s.tacklesWon += 1;
        }
        if (dt === 'Aerial Lost') { /* lost aerial: no-op, wins counted via miscellaneous */ }
        break;
      }
      case 'Interception':
        if (/^(Won|Success)/.test(e.interception?.outcome?.name || '')) s.interceptions += 1;
        break;
      case 'Ball Recovery':
        if (!e.ball_recovery?.recovery_failure) s.recoveries += 1;
        break;
      case 'Block': s.blocks += 1; break;
      case 'Clearance':
        s.clearances += 1;
        if (e.clearance?.aerial_won) s.aerialsWon += 1;
        break;
      case 'Foul Won': s.foulsWon += 1; break;
      case 'Foul Committed': s.foulsCommitted += 1; break;
      case 'Dispossessed': s.dispossessed += 1; break;
      case 'Miscontrol': s.miscontrols += 1; break;
      case 'Goal Keeper': {
        const gk = e.goalkeeper;
        if (gk?.type?.name === 'Shot Saved' || gk?.type?.name === 'Penalty Saved') s.saves += 1;
        if (gk?.type?.name === 'Goal Conceded') s.goalsConceded += 1;
        break;
      }
      case 'Miscellaneous':
        if (e.miscellaneous?.aerial_won) s.aerialsWon += 1;
        break;
    }
  }
}

export function primaryPosition(p) {
  let best = null, bestMin = -1;
  for (const [pos, mins] of Object.entries(p.positions)) {
    if (mins > bestMin) { best = pos; bestMin = mins; }
  }
  return best;
}

export function positionGroup(p) {
  const pos = primaryPosition(p);
  return POSITION_GROUPS[pos] || 'MF';
}

// Per-90 rates for every counting stat, plus ratios.
export function per90(p) {
  const m = p.stats.minutes;
  const f = m > 0 ? 90 / m : 0;
  const s = p.stats;
  return {
    goals90: s.goals * f, npGoals90: s.npGoals * f, xg90: s.xg * f, npxg90: s.npxg * f,
    shots90: s.shots * f, assists90: s.assists * f, xa90: s.xa * f, keyPasses90: s.keyPasses * f,
    passes90: s.passes * f, passPct: s.passes ? (s.passesCompleted / s.passes) * 100 : 0,
    progPasses90: s.progressivePasses * f, passesIntoBox90: s.passesIntoBox * f, crosses90: s.crosses * f,
    progCarries90: s.progressiveCarries * f, carryDistance90: s.carryDistance * f,
    dribbles90: s.dribbles * f,
    dribblePct: s.dribbles ? (s.dribblesCompleted / s.dribbles) * 100 : 0,
    pressures90: s.pressures * f, tackles90: s.tackles * f, interceptions90: s.interceptions * f,
    recoveries90: s.recoveries * f, blocks90: s.blocks * f, clearances90: s.clearances * f,
    aerialsWon90: s.aerialsWon * f, foulsWon90: s.foulsWon * f,
    npxgPlusXa90: (s.npxg + s.xa) * f,
    saves90: s.saves * f,
    savePct: (s.saves + s.goalsConceded) ? (s.saves / (s.saves + s.goalsConceded)) * 100 : 0,
  };
}

// Percentile rank (0-100) of each per-90 metric within the player's position
// group, among players with at least `minMinutes`.
export function computePercentiles(players, { minMinutes = 180 } = {}) {
  const qualified = [...players.values()].filter((p) => p.stats.minutes >= minMinutes);
  const byGroup = new Map();
  for (const p of qualified) {
    const g = positionGroup(p);
    if (!byGroup.has(g)) byGroup.set(g, []);
    byGroup.get(g).push(p);
  }
  const result = new Map();
  for (const [group, members] of byGroup) {
    const rates = members.map((p) => ({ p, r: per90(p) }));
    const keys = Object.keys(rates[0]?.r || {});
    const sorted = {};
    for (const k of keys) sorted[k] = rates.map((x) => x.r[k]).sort((a, b) => a - b);
    for (const { p, r } of rates) {
      const pct = {};
      for (const k of keys) {
        const arr = sorted[k];
        let below = 0, equal = 0;
        for (const v of arr) { if (v < r[k]) below += 1; else if (v === r[k]) equal += 1; }
        pct[k] = arr.length > 1 ? ((below + equal / 2) / arr.length) * 100 : 50;
      }
      result.set(p.id, { group, per90: r, percentiles: pct });
    }
  }
  return result;
}

// Headline 0-100 rating: average of the percentiles that matter for the role.
const RATING_KEYS = {
  GK: ['savePct', 'saves90', 'passPct'],
  CB: ['passPct', 'progPasses90', 'interceptions90', 'blocks90', 'clearances90', 'aerialsWon90', 'tackles90'],
  FB: ['progPasses90', 'progCarries90', 'crosses90', 'tackles90', 'interceptions90', 'xa90', 'pressures90'],
  MF: ['passPct', 'progPasses90', 'progCarries90', 'recoveries90', 'tackles90', 'xa90', 'npxg90', 'pressures90'],
  AM: ['npxg90', 'xa90', 'keyPasses90', 'dribbles90', 'progCarries90', 'passesIntoBox90', 'shots90'],
  FW: ['npGoals90', 'npxg90', 'shots90', 'xa90', 'aerialsWon90', 'pressures90'],
};

export function rating(percentiles, group) {
  const keys = RATING_KEYS[group] || RATING_KEYS.MF;
  const vals = keys.map((k) => percentiles[k] ?? 50);
  return Math.round(vals.reduce((a, b) => a + b, 0) / vals.length);
}
