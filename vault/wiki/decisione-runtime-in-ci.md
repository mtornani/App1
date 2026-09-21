---
type: decision
title: Il runtime non presidiato e' GitHub Actions
updated: 2026-09-21
sources: [raw/sessione-2026-09-21.md]
status: da rivedere
---

# Runtime in CI

Cron ogni 30 minuti, piu' push e dispatch manuale. Nessun server.

## Perche' regge

Costo infrastrutturale zero e nessun processo da tenere vivo. Per il lavoro
batch e' la forma giusta: il `lint` del vault gira mentre nessuno guarda, ed e'
esattamente cio' che una chat non puo' fare.

## Perche' e' da rivedere

Per un assistente continuo e' la forma sbagliata. Un ciclo da 30 minuti che
committa su git non e' un assistente, e' un cron. L'obiettivo dichiarato dal
proprietario il 2026-09-21 e' un'estensione del proprio pensiero, che richiede
risposta immediata e locale.

## Direzione

Divisione dei compiti, non sostituzione:

| Parte | Dove gira | Perche' |
|---|---|---|
| Ingest, query | Locale, immediato | Serve la risposta ora, con l'umano che guarda |
| Lint, prune | CI, non presidiato | Serve che giri quando l'umano non c'e' |

[DATO MANCANTE] La parte locale non esiste ancora. Vedi [[thread-jarvis-locale]].
