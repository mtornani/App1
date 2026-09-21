---
type: thread
title: L'agenzia non ha mai girato con un modello vero
updated: 2026-09-21
sources: [raw/sessione-2026-09-21.md]
status: chiuso
---

# Primo giro reale

## CHIUSO il 2026-09-21

Eseguito su GitHub Actions con DeepSeek: 5 passi, 62 secondi, esito success.
Ha trovato tre difetti veri, tutti corretti. Il dettaglio in
[[decisione-protocollo-testuale]].

## Il problema

88 test verdi, `fetch` provato dal vivo su Wikipedia, ciclo degli strumenti
verificato con un provider scriptato. Ma nessun agente e' mai stato mosso da un
modello vero. Tutto il resto e' impalcatura finche' questo non succede.

## Cosa lo sblocca

Credito DeepSeek da 50 dollari, gia' disponibile. Stima: circa 0,06 dollari a
missione a tariffa piena, quindi centinaia di missioni.

## Cosa si scopre facendolo

Non si testa DeepSeek, si testa [[decisione-protocollo-testuale]]. Se regge, e'
chiusa. Se si sfalda, il rimpiazzo nativo e' gia' disponibile su entrambi i
provider.

## Cosa blocca a valle

- [[thread-post-linkedin]]: gli screenshot oggi mostrano dati inventati.
- [[thread-application-zai]]: la frase "tested system" poggia solo sui test.

## Prossimo passo

Segreto `DEEPSEEK_API_KEY`, poi una missione sola.
