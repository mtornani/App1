---
type: entity
title: reep, registro di identità giocatore fra provider
updated: 2026-09-21
sources: [agency/output/m-20260921-200045-valuta-se-il-repository/report.md]
status: attiva
---

# reep

Valutato dall'agenzia il 2026-09-21, su fonte unica scaricata:
il README di `withqwerty/reep` su ramo `main`.

## La risposta breve

| Crosswalk | Esito |
|---|---|
| Transfermarkt ↔ FBref | **Usabile.** Colonne dedicate `key_transfermarkt` e `key_fbref` |
| StatsBomb ↔ qualsiasi | **Non coperto.** La stringa StatsBomb non compare nel README |

## Cosa serve sapere prima di usarlo

- **Dati in CC0 1.0**, dichiarato. Il motore che li costruisce no: sta in un
  repository privato commerciale.
- **La v0 in questo repo è congelata** al rilascio `2026.25` del 21 giugno 2026.
  Nessuna scrittura nel database dal 25 aprile 2026. Se servono aggiornamenti
  più recenti, la v0 è rumore e bisogna passare alla v1 su `reep.football`.
- **444.707 persone, 45.337 squadre, 27.591 alias**, ma sono numeri dichiarati
  nel README e non riscontrati sui file.
- **Chi è sia giocatore sia allenatore ha due record distinti.** Un join per
  persona fisica richiede logica di aggregazione a valle.

## Conseguenza per lo scouting

[INFERENZA] Risolve il pezzo noioso del matching fra Transfermarkt e FBref, che
è la coppia più usata. Non risolve StatsBomb, quindi chi lavora sui dati evento
deve comunque costruirsi un ponte verso StatsBomb a parte, quantificandone
copertura ed errore.

## Cosa resta non verificato

Il report elenca dieci punti, fra cui: nessun CSV scaricato, nessun endpoint
chiamato, nessuna misura di precision e recall, e la licenza confermata solo
come affermazione nel README e non come file.
