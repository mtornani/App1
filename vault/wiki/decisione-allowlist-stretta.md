---
type: decision
title: L'allowlist di fetch parte stretta
updated: 2026-09-21
sources: [raw/sessione-2026-09-21.md]
status: attiva
---

# Allowlist stretta per scelta

Default: Wikipedia, Wikidata, GitHub, football-data, openfootball, FIFA, UEFA.
Si estende con una variabile d'ambiente, senza toccare il codice.

## Perche'

Un'allowlist larga trasforma un agente che gira in CI senza supervisione in un
crawler autonomo. Il costo di aggiungere un dominio a mano e' basso; il costo di
scoprire che il sistema ha scaricato mezzo web da solo e' alto.

## Costo accettato

Molte fonti utili restano fuori finche' non vengono aggiunte esplicitamente.
Transfermarkt, per dire, oggi e' bloccato.
