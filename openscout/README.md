# OpenScout

**Open-data scouting, match analysis & eligibility intelligence.**
Zero npm dependencies · free professional event data · runs anywhere Node 18+ runs.

OpenScout is a low-cost alternative to Wyscout/InStat built around a niche the
incumbents don't serve: **national-team eligibility scouting** (oriundi /
diaspora talent discovery) plus open-data analytics for federations, agents and
semi-pro clubs. See [STRATEGY.md](./STRATEGY.md) for the market thesis.

## Quick start

```bash
cd openscout

# 1. See what's available for free (80+ competition-seasons of pro event data)
node cli.js competitions

# 2. Sync one (e.g. Euro 2024: competition 55, season 282)
node cli.js sync 55 282

# 3. Explore
node cli.js players --pos FW            # ranked by OpenScout rating
node cli.js player "Lamine Yamal"       # percentile profile
node cli.js similar "Rodri"             # statistical doppelgängers
node cli.js match list
node cli.js match 3943043               # the Euro 2024 final
node cli.js eligibility SMR             # San Marino diaspora screening

# 4. Shareable single-file HTML reports
node cli.js report player "Nico Williams" --o nico.html
node cli.js report match 3943043 --o final.html

# 5. Web UI + JSON API
node cli.js serve --port 3030
```

No `npm install` needed — there are no dependencies.

## What's inside

| Module | What it does |
|---|---|
| `src/statsbomb.js` | fetch + disk cache for StatsBomb open data |
| `src/metrics.js` | events → per-player metrics, per-90 rates, positional percentiles, OS rating |
| `src/similarity.js` | z-scored cosine similarity ("find me another X") |
| `src/match.js` | xG race, shot maps, pass networks, momentum, top performers |
| `src/eligibility.js` | FIFA eligibility rules engine + diaspora screening per federation |
| `src/federations.json` | citizenship-law knowledge base (SMR, MLT, FRO, LUX — extensible) |
| `src/report.js` | self-contained HTML reports with SVG radar/pitch charts |
| `src/server.js` | zero-dep HTTP server: web UI + JSON API |

## JSON API

```
GET  /api/competitions          free competitions list
GET  /api/datasets              synced datasets
POST /api/sync?competition_id=55&season_id=282
GET  /api/players?q=&group=FW&min_minutes=180
GET  /api/player/:id            profile + percentiles + similar players
GET  /api/matches
GET  /api/match/:id             full match analysis
GET  /api/federations
GET  /api/eligibility/:CODE     diaspora screening
POST /api/assess                {profile, federation} → FIFA eligibility assessment
GET  /report/player/:id         HTML report
GET  /report/match/:id          HTML report
```

## Eligibility assessment example

```bash
curl -X POST localhost:3030/api/assess -d '{
  "federation": "MLT",
  "profile": {
    "name": "Example Player",
    "birth_country": "Australia",
    "citizenships": ["Australia"],
    "grandparents_born_in": ["Malta"]
  }
}'
# → status NOW_AFTER_PAPERWORK, grandparent path, citizenship claimable by descent
```

The screening layer flags candidates; the [Radar SMR](../README.md) RAG
pipeline in this repo is the deep-dive layer that verifies ancestry from public
sources.

## Tests

```bash
npm test   # node:test, no dependencies
```

## Data credits

Player/match data from the [StatsBomb open data](https://github.com/statsbomb/open-data)
repository — free for research and non-commercial use under their terms. Always
credit StatsBomb when publishing derived work.
