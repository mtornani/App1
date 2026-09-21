---
type: entity
title: Fonti di dati calcistici aperti
updated: 2026-09-21
sources: [https://github.com/topics/football-data]
status: attiva
---

# Fonti di dati calcistici aperti

Ogni riga è stata **provata**, non supposta: richiesta reale via Jina Reader il
2026-09-21. Le dimensioni sono quelle effettivamente scaricate.

## Raggiungibili, in allowlist

| Fonte | Cosa dà | Prova |
|---|---|---|
| `raw.githubusercontent.com` | Tutti i dataset su GitHub in CSV e JSON | 3,7 MB di risultati internazionali in una richiesta |
| `understat.com` | xG per lega, squadra, giocatore | 22 KB, nessun blocco |
| `football-data.co.uk` | Storico risultati e quote in CSV, decenni di campionati | 41 KB, nessun blocco |
| `api.football-data.org` | API con competizioni, partite, classifiche | 190 competizioni senza token |
| `openfootball.github.io` | Calendari e risultati in formato aperto | ok |
| `wikipedia.org`, `wikidata.org` | Biografie, nazionalità, carriere | adattatore dedicato al testo piano |

## Bloccate da protezione anti-bot

Provate e respinte. Non sono in allowlist di proposito: aggiungerle
significherebbe solo collezionare fallimenti con un messaggio poco chiaro.

| Fonte | Esito |
|---|---|
| `fbref.com` | Pagina di verifica di sicurezza, anche passando da Jina |
| `worldfootball.net` | Stessa cosa, sia diretto sia via Jina |
| `transfermarkt` | Non provato: protezione nota e condizioni d'uso restrittive |

[INFERENZA] Per fbref e Transfermarkt la strada praticabile non è lo scraping
diretto ma i dataset già estratti e pubblicati su GitHub, per esempio
`dcaribou/transfermarkt-datasets` e `salimt/football-datasets`. Passano da
`raw.githubusercontent.com`, che è già consentito, e non violano nessuna
protezione.

## Repository interessanti trovati

Da `github.com/topics/football-data`, quelli che pubblicano dati e non tutorial.

- `hudl/open-data` — dati StatsBomb liberi, eventi con coordinate
- `martj42/international_results` — risultati delle nazionali, CSV unico
- `footballcsv/england` — campionati inglesi in CSV
- `dcaribou/transfermarkt-datasets` — Transfermarkt già estratto e pubblicato
- `withqwerty/reep` — mappatura delle identità giocatore fra oltre 25 provider
- `jfjelstul/worldcup` — database completo dei Mondiali maschili e femminili

[DATO MANCANTE] Nessuno di questi è ancora stato ingerito. Il primo che vale la
pena guardare è `withqwerty/reep`: il matching delle identità fra provider è il
problema noioso che si ripresenta in ogni pipeline di scouting.
