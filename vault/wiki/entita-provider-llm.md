---
type: entity
title: Provider LLM valutati
updated: 2026-09-21
sources: [raw/sessione-2026-09-21.md]
status: attiva
---

# Provider valutati

Tutti collegati dietro la stessa astrazione, quindi cambiarli costa una variabile.

| Provider | Modello default | Stato | Nota |
|---|---|---|---|
| DeepSeek | `deepseek-flash` | **credito disponibile, 50 dollari** | Thinking spento di default: acceso costa budget nei turni corti |
| Z.ai | `glm-5.3` | integrato, candidatura al programma startup aperta | Contesto 1M, tool calling nativo |
| Anthropic | `claude-sonnet-5` | integrato, nessuna chiave | |
| OpenRouter | `anthropic/claude-sonnet-5` | integrato | Utile come fallback |
| echo | offline | sempre disponibile | Deterministico, per test e dry-run |

## TypeSafe / Jev

Valutato ma non integrato. Non genera testo: restituisce decisioni tipizzate con
probabilita' calibrate, tramite tre primitive Choice, Score e Noul.
Prezzo documentato 0,042 dollari per milione di token in ingresso, output gratis.

Non e' un'alternativa a un modello generativo, e' un complemento in tre punti:
il verdetto del critic, l'handoff dello swarm, il filtro sulle fonti.
[INFERENZA] L'uso piu' interessante non e' nell'agenzia ma negli score di
eleggibilita' di OpenScout, oggi scritti come regole a mano.

## GuppyLM

Valutato e scartato come componente. E' un artefatto didattico da 8,7 milioni di
parametri. Utile per capire la catena da tokenizer a inferenza, inutile in
produzione.
