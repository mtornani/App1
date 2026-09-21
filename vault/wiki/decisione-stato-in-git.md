---
type: decision
title: Lo stato dell'agenzia vive in git, non in un database
updated: 2026-09-21
sources: [raw/sessione-2026-09-21.md]
status: attiva
---

# Lo stato vive in git

Missioni, run e artefatti sono file JSON e markdown versionati nel repository.

## Perche'

- Ogni esecuzione lascia un diff: l'audit e' gratis e non richiede strumenti.
- Il backup e la storia arrivano senza scriverli.
- Nessun servizio da tenere vivo, quindi il sistema sopravvive a mesi di
  disinteresse. [INFERENZA] Questo criterio pesa piu' del normale per come
  lavora il proprietario. Vedi [[concetto-come-lavoro]].

## Cosa la falsificherebbe

- Un commit ogni mezz'ora rende la history illeggibile e annega i commit veri.
  Rischio gia' identificato, non ancora mitigato.
- Se lo stato diventasse grande o concorrente, i file JSON smetterebbero di bastare.

## Alternativa scartata

Postgres su Cloud Run. Aggiunge costo fisso e toglie la history leggibile.
