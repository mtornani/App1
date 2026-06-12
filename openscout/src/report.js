// Self-contained HTML scouting reports: shareable single files, no external assets.
import { per90, computePercentiles, positionGroup, primaryPosition, rating, GROUP_LABELS } from './metrics.js';
import { similarPlayers } from './similarity.js';

const CSS = `
  :root { --bg:#0d1117; --card:#161b22; --line:#30363d; --fg:#e6edf3; --dim:#8b949e; --acc:#3fb950; --acc2:#58a6ff; }
  * { box-sizing: border-box; }
  body { font-family: -apple-system, 'Segoe UI', Roboto, sans-serif; background: var(--bg); color: var(--fg); margin: 0; padding: 32px 16px; }
  .wrap { max-width: 880px; margin: 0 auto; }
  .card { background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 24px; margin-bottom: 16px; }
  h1 { margin: 0 0 4px; font-size: 26px; } h2 { font-size: 15px; color: var(--dim); margin: 0 0 16px; text-transform: uppercase; letter-spacing: .08em; }
  .sub { color: var(--dim); margin-bottom: 24px; }
  .badge { display: inline-block; background: var(--acc); color: #04260f; font-weight: 700; border-radius: 8px; padding: 4px 12px; font-size: 22px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; }
  .stat { background: var(--bg); border: 1px solid var(--line); border-radius: 8px; padding: 10px 12px; }
  .stat b { display: block; font-size: 20px; } .stat span { color: var(--dim); font-size: 12px; }
  .bar { display: grid; grid-template-columns: 180px 1fr 48px; gap: 10px; align-items: center; margin: 6px 0; font-size: 13px; }
  .bar .track { background: var(--bg); border-radius: 4px; height: 10px; overflow: hidden; }
  .bar .fill { height: 100%; border-radius: 4px; }
  table { width: 100%; border-collapse: collapse; font-size: 14px; }
  td, th { padding: 8px 10px; border-bottom: 1px solid var(--line); text-align: left; }
  th { color: var(--dim); font-weight: 600; font-size: 12px; text-transform: uppercase; }
  .footer { color: var(--dim); font-size: 12px; text-align: center; margin-top: 24px; }
`;

const pctColor = (v) => (v >= 80 ? '#3fb950' : v >= 60 ? '#90c978' : v >= 40 ? '#d29922' : v >= 20 ? '#db6d28' : '#f85149');

function radarSVG(labels, values, size = 360) {
  const cx = size / 2, cy = size / 2, R = size / 2 - 56;
  const n = labels.length;
  const pt = (i, r) => {
    const a = (Math.PI * 2 * i) / n - Math.PI / 2;
    return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
  };
  let rings = '';
  for (const f of [0.25, 0.5, 0.75, 1]) {
    rings += `<polygon points="${labels.map((_, i) => pt(i, R * f).join(',')).join(' ')}" fill="none" stroke="#30363d" stroke-width="1"/>`;
  }
  const axes = labels.map((_, i) => { const [x, y] = pt(i, R); return `<line x1="${cx}" y1="${cy}" x2="${x}" y2="${y}" stroke="#30363d"/>`; }).join('');
  const poly = labels.map((_, i) => pt(i, (R * Math.max(values[i], 2)) / 100).join(',')).join(' ');
  const texts = labels.map((l, i) => {
    const [x, y] = pt(i, R + 28);
    return `<text x="${x}" y="${y}" fill="#8b949e" font-size="11" text-anchor="middle" dominant-baseline="middle">${l} <tspan fill="#e6edf3" font-weight="bold">${Math.round(values[i])}</tspan></text>`;
  }).join('');
  return `<svg viewBox="0 0 ${size} ${size}" width="100%" style="max-width:${size}px;display:block;margin:0 auto" xmlns="http://www.w3.org/2000/svg">
    ${rings}${axes}<polygon points="${poly}" fill="rgba(88,166,255,.25)" stroke="#58a6ff" stroke-width="2"/>${texts}</svg>`;
}

const RADAR_BY_GROUP = {
  GK: [['Save %', 'savePct'], ['Saves/90', 'saves90'], ['Pass %', 'passPct'], ['Passes/90', 'passes90'], ['Recoveries', 'recoveries90'], ['Clearances', 'clearances90']],
  CB: [['Pass %', 'passPct'], ['Prog. passes', 'progPasses90'], ['Interceptions', 'interceptions90'], ['Tackles', 'tackles90'], ['Blocks', 'blocks90'], ['Clearances', 'clearances90'], ['Aerials won', 'aerialsWon90'], ['Recoveries', 'recoveries90']],
  FB: [['Prog. passes', 'progPasses90'], ['Prog. carries', 'progCarries90'], ['Crosses', 'crosses90'], ['xA', 'xa90'], ['Tackles', 'tackles90'], ['Interceptions', 'interceptions90'], ['Pressures', 'pressures90'], ['Pass %', 'passPct']],
  MF: [['Pass %', 'passPct'], ['Prog. passes', 'progPasses90'], ['Prog. carries', 'progCarries90'], ['xA', 'xa90'], ['npxG', 'npxg90'], ['Recoveries', 'recoveries90'], ['Tackles', 'tackles90'], ['Pressures', 'pressures90']],
  AM: [['npxG', 'npxg90'], ['xA', 'xa90'], ['Key passes', 'keyPasses90'], ['Dribbles', 'dribbles90'], ['Prog. carries', 'progCarries90'], ['Box passes', 'passesIntoBox90'], ['Shots', 'shots90'], ['Pressures', 'pressures90']],
  FW: [['npGoals', 'npGoals90'], ['npxG', 'npxg90'], ['Shots', 'shots90'], ['xA', 'xa90'], ['Key passes', 'keyPasses90'], ['Dribbles', 'dribbles90'], ['Aerials won', 'aerialsWon90'], ['Pressures', 'pressures90']],
};

export function playerReportHTML(playerId, players, { minMinutes = 180 } = {}) {
  const p = players.get(playerId);
  if (!p) throw new Error(`Player ${playerId} not found`);
  const percentiles = computePercentiles(players, { minMinutes });
  const ctx = percentiles.get(playerId);
  if (!ctx) throw new Error(`${p.name} has fewer than ${minMinutes} minutes — not enough sample for a report`);
  const group = ctx.group;
  const r = ctx.per90;
  const os = rating(ctx.percentiles, group);
  const radarSpec = RADAR_BY_GROUP[group] || RADAR_BY_GROUP.MF;
  const radar = radarSVG(radarSpec.map(([l]) => l), radarSpec.map(([, k]) => ctx.percentiles[k] ?? 50));

  const bars = Object.entries(ctx.percentiles)
    .filter(([k]) => !['savePct', 'saves90'].includes(k) || group === 'GK')
    .sort((a, b) => b[1] - a[1])
    .map(([k, v]) => `<div class="bar"><span>${k}</span><div class="track"><div class="fill" style="width:${v}%;background:${pctColor(v)}"></div></div><b>${Math.round(v)}</b></div>`)
    .join('');

  const similar = similarPlayers(playerId, players, { minMinutes, limit: 6 })
    .map((s) => `<tr><td>${s.player.name}</td><td>${s.player.team}</td><td>${s.group}</td><td>${(s.similarity * 100).toFixed(0)}%</td></tr>`)
    .join('');

  const keyStats = [
    ['Minutes', Math.round(p.stats.minutes)], ['Matches', p.stats.matches],
    ['Goals', p.stats.goals], ['Assists', p.stats.assists],
    ['npxG/90', r.npxg90.toFixed(2)], ['xA/90', r.xa90.toFixed(2)],
    ['Prog. passes/90', r.progPasses90.toFixed(1)], ['Pass %', `${r.passPct.toFixed(0)}%`],
  ].map(([l, v]) => `<div class="stat"><b>${v}</b><span>${l}</span></div>`).join('');

  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${p.name} — OpenScout report</title><style>${CSS}</style></head><body><div class="wrap">
<div class="card"><h1>${p.name} <span class="badge">OS ${os}</span></h1>
<div class="sub">${p.team} · ${primaryPosition(p)} (${GROUP_LABELS[group]}) · ${p.country || ''}</div>
<div class="grid">${keyStats}</div></div>
<div class="card"><h2>Percentile radar vs ${GROUP_LABELS[group]}s (min. ${minMinutes}')</h2>${radar}</div>
<div class="card"><h2>All percentiles</h2>${bars}</div>
<div class="card"><h2>Similar players</h2><table><tr><th>Player</th><th>Team</th><th>Pos</th><th>Style match</th></tr>${similar}</table></div>
<div class="footer">Generated by OpenScout · data: StatsBomb open data · ${new Date().toISOString().slice(0, 10)}</div>
</div></body></html>`;
}

export function matchReportHTML(analysis) {
  const { match, xgRace, shots, momentum, topPerformers, passNetworks } = analysis;
  const W = 760, H = 280, maxMin = Math.max(95, ...xgRace.flatMap((t) => t.points.map((p) => p.minute)));
  const maxXg = Math.max(0.5, ...xgRace.map((t) => t.total)) * 1.15;
  const X = (m) => 40 + (m / maxMin) * (W - 60);
  const Y = (v) => H - 30 - (v / maxXg) * (H - 50);
  const colors = ['#58a6ff', '#f85149'];
  let race = `<svg viewBox="0 0 ${W} ${H}" width="100%" xmlns="http://www.w3.org/2000/svg">`;
  race += `<line x1="40" y1="${H - 30}" x2="${W - 20}" y2="${H - 30}" stroke="#30363d"/>`;
  for (const m of [0, 15, 30, 45, 60, 75, 90]) race += `<text x="${X(m)}" y="${H - 12}" fill="#8b949e" font-size="11" text-anchor="middle">${m}'</text>`;
  xgRace.forEach((t, i) => {
    let d = '', prev = null;
    for (const pt of t.points) {
      if (!prev) d = `M ${X(pt.minute)} ${Y(pt.xg)}`;
      else d += ` L ${X(pt.minute)} ${Y(prev.xg)} L ${X(pt.minute)} ${Y(pt.xg)}`;
      prev = pt;
    }
    d += ` L ${X(maxMin)} ${Y(t.total)}`;
    race += `<path d="${d}" fill="none" stroke="${colors[i]}" stroke-width="2.5"/>`;
    for (const pt of t.points.filter((p) => p.goal)) {
      race += `<circle cx="${X(pt.minute)}" cy="${Y(pt.xg)}" r="6" fill="${colors[i]}"/><title>${pt.player}</title>`;
    }
    race += `<text x="${W - 16}" y="${Y(t.total) + 4}" fill="${colors[i]}" font-size="12" text-anchor="end">${t.team} ${t.total}</text>`;
  });
  race += '</svg>';

  // Momentum bars
  const MW = 760, MH = 140, maxV = Math.max(1, ...momentum.map((w) => Math.abs(w.value)));
  let mom = `<svg viewBox="0 0 ${MW} ${MH}" width="100%" xmlns="http://www.w3.org/2000/svg"><line x1="0" y1="${MH / 2}" x2="${MW}" y2="${MH / 2}" stroke="#30363d"/>`;
  const bw = MW / momentum.length - 2;
  momentum.forEach((w, i) => {
    const h = (Math.abs(w.value) / maxV) * (MH / 2 - 8);
    const up = w.value >= 0;
    mom += `<rect x="${i * (bw + 2)}" y="${up ? MH / 2 - h : MH / 2}" width="${bw}" height="${h}" fill="${up ? colors[0] : colors[1]}" opacity=".85"><title>${w.from}'-${w.to}'</title></rect>`;
  });
  mom += '</svg>';

  // Shot maps (attacking right, half pitch per team)
  const shotMap = (team, color) => {
    const SW = 360, SH = 246; // 60x80 StatsBomb half-pitch scaled x3
    let svg = `<svg viewBox="0 0 ${SW} ${SH}" width="100%" style="max-width:${SW}px" xmlns="http://www.w3.org/2000/svg">`;
    svg += `<rect x="0" y="3" width="${SW - 6}" height="${SH - 6}" fill="none" stroke="#30363d"/>`;
    svg += `<rect x="${SW - 6 - 54}" y="${(SH - 132) / 2}" width="54" height="132" fill="none" stroke="#30363d"/>`;
    svg += `<rect x="${SW - 6 - 18}" y="${(SH - 60) / 2}" width="18" height="60" fill="none" stroke="#30363d"/>`;
    for (const s of shots.filter((s) => s.team === team && s.x != null)) {
      const x = ((s.x - 60) / 60) * (SW - 6), y = (s.y / 80) * (SH - 6) + 3;
      const r = 4 + Math.sqrt(s.xg) * 14;
      svg += s.outcome === 'Goal'
        ? `<circle cx="${x}" cy="${y}" r="${r}" fill="${color}" stroke="#fff" stroke-width="1.5"><title>${s.player} ${s.minute}' — GOAL (xG ${s.xg.toFixed(2)})</title></circle>`
        : `<circle cx="${x}" cy="${y}" r="${r}" fill="${color}" opacity=".35"><title>${s.player} ${s.minute}' — ${s.outcome} (xG ${s.xg.toFixed(2)})</title></circle>`;
    }
    return svg + '</svg>';
  };

  // Pass networks (full pitch 120x80 scaled x4)
  const network = (net, color) => {
    const PW = 480, PH = 320;
    let svg = `<svg viewBox="0 0 ${PW} ${PH}" width="100%" style="max-width:${PW}px" xmlns="http://www.w3.org/2000/svg">`;
    svg += `<rect x="2" y="2" width="${PW - 4}" height="${PH - 4}" fill="none" stroke="#30363d"/><line x1="${PW / 2}" y1="2" x2="${PW / 2}" y2="${PH - 2}" stroke="#30363d"/>`;
    const px = (x) => (x / 120) * (PW - 4) + 2, py = (y) => (y / 80) * (PH - 4) + 2;
    const pos = new Map(net.nodes.map((n) => [n.id, n]));
    for (const l of net.links) {
      const a = pos.get(l.from), b = pos.get(l.to);
      if (!a || !b) continue;
      svg += `<line x1="${px(a.x)}" y1="${py(a.y)}" x2="${px(b.x)}" y2="${py(b.y)}" stroke="${color}" stroke-width="${Math.min(l.count / 2.5, 7)}" opacity=".3"/>`;
    }
    const maxP = Math.max(1, ...net.nodes.map((n) => n.passes));
    for (const n of net.nodes) {
      const r = 7 + (n.passes / maxP) * 11;
      const last = n.name.split(' ').pop();
      svg += `<circle cx="${px(n.x)}" cy="${py(n.y)}" r="${r}" fill="${color}"><title>${n.name} — ${n.passes} completed passes</title></circle>`;
      svg += `<text x="${px(n.x)}" y="${py(n.y) - r - 4}" fill="#e6edf3" font-size="10" text-anchor="middle">${last}</text>`;
    }
    return svg + '</svg>';
  };

  const perfRows = topPerformers.map((p, i) =>
    `<tr><td>${i + 1}</td><td>${p.name}</td><td>${p.team}</td><td>${p.score}</td></tr>`).join('');

  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${match.home} ${match.score} ${match.away} — OpenScout</title><style>${CSS}</style></head><body><div class="wrap">
<div class="card"><h1>${match.home} ${match.score} ${match.away}</h1>
<div class="sub">${match.date} · ${match.stage || ''} · xG ${xgRace[0].total} – ${xgRace[1].total}</div></div>
<div class="card"><h2>xG race</h2>${race}</div>
<div class="card"><h2>Momentum (5' windows — up: ${match.home}, down: ${match.away})</h2>${mom}</div>
<div class="card"><h2>Shot maps</h2>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px"><div><div class="sub">${match.home}</div>${shotMap(match.home, colors[0])}</div>
<div><div class="sub">${match.away}</div>${shotMap(match.away, colors[1])}</div></div></div>
<div class="card"><h2>Pass networks (starting XI, links ≥3 passes)</h2>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px"><div><div class="sub">${match.home}</div>${network(passNetworks[0], colors[0])}</div>
<div><div class="sub">${match.away}</div>${network(passNetworks[1], colors[1])}</div></div></div>
<div class="card"><h2>Top performers (event-based composite)</h2><table><tr><th>#</th><th>Player</th><th>Team</th><th>Score</th></tr>${perfRows}</table></div>
<div class="footer">Generated by OpenScout · data: StatsBomb open data</div>
</div></body></html>`;
}
