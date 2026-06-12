// Single-match analysis: xG race, shot maps, pass networks, momentum, top performers.

export function analyzeMatch(matchInfo, events, lineups) {
  const teams = [matchInfo.home_team.home_team_name, matchInfo.away_team.away_team_name];

  const shots = events
    .filter((e) => e.type.name === 'Shot')
    .map((e) => ({
      minute: e.minute, second: e.second, period: e.period,
      team: e.team.name, player: e.player.name,
      x: e.location?.[0], y: e.location?.[1],
      xg: e.shot.statsbomb_xg || 0,
      outcome: e.shot.outcome?.name,
      penalty: e.shot.type?.name === 'Penalty',
    }));

  // Cumulative xG timeline per team
  const xgRace = teams.map((team) => {
    let cum = 0;
    const points = [{ minute: 0, xg: 0 }];
    for (const s of shots.filter((s) => s.team === team).sort((a, b) => a.minute - b.minute || a.second - b.second)) {
      cum += s.xg;
      points.push({ minute: s.minute + s.second / 60, xg: +cum.toFixed(3), goal: s.outcome === 'Goal', player: s.player });
    }
    return { team, total: +cum.toFixed(2), points };
  });

  // Pass network per team: average position + pass links among the starting XI.
  const startersByTeam = new Map();
  for (const e of events.filter((e) => e.type.name === 'Starting XI')) {
    startersByTeam.set(e.team.name, new Set(e.tactics.lineup.map((l) => l.player.id)));
  }
  const passNetworks = teams.map((team) => {
    const starters = startersByTeam.get(team) || new Set();
    const nodes = new Map(); // id -> {name, x, y, n, passes}
    const links = new Map(); // "a>b" -> count
    for (const e of events) {
      if (e.team?.name !== team || !e.player || !starters.has(e.player.id)) continue;
      if (!e.location) continue;
      if (e.type.name === 'Pass' || e.type.name === 'Ball Receipt*' || e.type.name === 'Carry') {
        let node = nodes.get(e.player.id);
        if (!node) { node = { id: e.player.id, name: e.player.name, sx: 0, sy: 0, n: 0, passes: 0 }; nodes.set(e.player.id, node); }
        node.sx += e.location[0]; node.sy += e.location[1]; node.n += 1;
      }
      if (e.type.name === 'Pass' && !e.pass.outcome && e.pass.recipient && starters.has(e.pass.recipient.id)) {
        const key = `${e.player.id}>${e.pass.recipient.id}`;
        links.set(key, (links.get(key) || 0) + 1);
        const node = nodes.get(e.player.id);
        if (node) node.passes += 1;
      }
    }
    return {
      team,
      nodes: [...nodes.values()].map((n) => ({ id: n.id, name: n.name, x: +(n.sx / n.n).toFixed(1), y: +(n.sy / n.n).toFixed(1), passes: n.passes })),
      links: [...links.entries()]
        .map(([k, count]) => { const [a, b] = k.split('>').map(Number); return { from: a, to: b, count }; })
        .filter((l) => l.count >= 3),
    };
  });

  // Momentum: 5-minute windows, danger-weighted territorial dominance.
  const maxMinute = Math.ceil(events.reduce((m, e) => Math.max(m, e.minute), 90));
  const windows = [];
  for (let start = 0; start < maxMinute; start += 5) {
    const w = { from: start, to: start + 5 };
    const score = { [teams[0]]: 0, [teams[1]]: 0 };
    for (const e of events) {
      if (e.minute < start || e.minute >= start + 5 || !e.team) continue;
      if (e.type.name === 'Shot') score[e.team.name] += 1 + (e.shot.statsbomb_xg || 0) * 8;
      else if (e.type.name === 'Pass' && e.location?.[0] >= 80 && !e.pass.outcome) score[e.team.name] += 0.15;
      else if (e.type.name === 'Carry' && e.carry?.end_location?.[0] >= 80) score[e.team.name] += 0.1;
    }
    w.value = +(score[teams[0]] - score[teams[1]]).toFixed(2); // + = home dominance
    windows.push(w);
  }

  // Top performers: quick composite from match events.
  const perf = new Map();
  const bump = (e, pts) => {
    if (!e.player) return;
    const cur = perf.get(e.player.id) || { name: e.player.name, team: e.team.name, score: 0 };
    cur.score += pts;
    perf.set(e.player.id, cur);
  };
  for (const e of events) {
    switch (e.type.name) {
      case 'Shot':
        bump(e, (e.shot.statsbomb_xg || 0) * 1.2 + (e.shot.outcome?.name === 'Goal' ? 0.8 : 0));
        break;
      case 'Pass':
        if (e.pass.goal_assist) bump(e, 0.7);
        else if (e.pass.shot_assist) bump(e, 0.25);
        else if (!e.pass.outcome && e.location && e.pass.end_location && e.pass.end_location[0] - e.location[0] >= 10 && e.pass.end_location[0] >= 60) bump(e, 0.04);
        break;
      case 'Carry':
        if (e.location && e.carry?.end_location && e.carry.end_location[0] - e.location[0] >= 10) bump(e, 0.04);
        break;
      case 'Dribble': if (e.dribble?.outcome?.name === 'Complete') bump(e, 0.1); break;
      case 'Interception': bump(e, 0.08); break;
      case 'Ball Recovery': if (!e.ball_recovery?.recovery_failure) bump(e, 0.04); break;
      case 'Block': bump(e, 0.06); break;
      case 'Duel': if (e.duel?.type?.name === 'Tackle' && /^(Won|Success)/.test(e.duel.outcome?.name || '')) bump(e, 0.08); break;
      case 'Goal Keeper': if (e.goalkeeper?.type?.name === 'Shot Saved') bump(e, 0.3); break;
    }
  }
  const topPerformers = [...perf.values()].sort((a, b) => b.score - a.score).slice(0, 8)
    .map((p) => ({ ...p, score: +p.score.toFixed(2) }));

  return {
    match: {
      id: matchInfo.match_id,
      date: matchInfo.match_date,
      home: teams[0], away: teams[1],
      score: `${matchInfo.home_score}-${matchInfo.away_score}`,
      stage: matchInfo.competition_stage?.name,
    },
    xgRace, shots, passNetworks, momentum: windows, topPerformers,
  };
}
