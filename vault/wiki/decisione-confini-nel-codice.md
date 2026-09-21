---
type: decision
title: I confini degli strumenti stanno nel codice, non nel prompt
updated: 2026-09-21
sources: [raw/sessione-2026-09-21.md]
status: attiva
---

# I confini stanno nel codice

Allowlist di domini, blocco degli indirizzi privati, traversal, percorsi
assoluti, immutabilita' di `raw/`: tutto applicato in Python, niente affidato
alle istruzioni date al modello.

## Perche'

Un prompt non e' un controllo di sicurezza. Se l'unica cosa che impedisce a un
agente di uscire dalla sua cartella e' una frase gentile nel system prompt,
quel controllo non esiste.

## Prova

I test coprono i confini, non solo il percorso felice. Due difetti veri sono
stati trovati dai test e non a occhio:

1. Un percorso assoluto veniva riscritto in silenzio invece di essere rifiutato.
2. Una riga di protocollo poteva finire dentro il deliverable.

## Cosa la falsificherebbe

Niente di noto. E' la decisione piu' solida dell'intero sistema.
