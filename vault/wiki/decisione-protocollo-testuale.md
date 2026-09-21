---
type: decision
title: Protocollo testuale degli strumenti invece della tool-use nativa
updated: 2026-09-21
sources: [raw/sessione-2026-09-21.md]
status: attiva
---

# Protocollo testuale

L'agente chiama uno strumento scrivendo due righe:

```
TOOL: fetch
{"url": "https://..."}
```

L'orchestratore fa il parsing, esegue, restituisce il risultato.

## Perche'

Un solo motore funziona identico su Anthropic, Z.ai, DeepSeek, OpenRouter e con
il provider offline. I test girano senza rete e senza chiavi.

## Cosa la falsificherebbe

Il primo giro con un modello vero. Se il modello sbaglia il formato o smette di
rispettarlo dopo qualche turno, la decisione cade.

## Il rimpiazzo e' gia' pronto

GLM-5.3 e DeepSeek hanno entrambi il tool calling nativo e l'output strutturato.
Se il protocollo testuale si sfalda, quella riga diventa uno schema.

Collegata: [[thread-primo-giro-reale]].
