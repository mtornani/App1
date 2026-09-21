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
| DeepSeek | `deepseek-flash` | **chiave configurata in CI** | Thinking spento di default: acceso costa budget nei turni corti |
| Z.ai | `glm-5.3` | integrato, candidatura al programma startup aperta | Contesto 1M, tool calling nativo |
| Anthropic | `claude-sonnet-5` | integrato, nessuna chiave | |
| OpenRouter | `anthropic/claude-sonnet-5` | integrato | Utile come fallback |
| echo | offline | sempre disponibile | Deterministico, per test e dry-run |

## TypeSafe / Jev

**Integrato**, in attesa di chiave. Lo schema implementato combacia con la
documentazione API verificata il 2026-09-21: POST su `/v1/systemone`,
autenticazione Bearer, corpo con `state`, `model` e la mappa `questions`.
La chiave si ottiene registrandosi su `console.typesafe.ai` e prendendola da
`/keys`. Non risulta una pagina pubblica dei prezzi oltre a quella dei modelli.

Usato in un punto solo: l'instradamento dello swarm quando il testo dell'agente
e' ambiguo. Senza chiave il comportamento resta quello di prima.
 Non genera testo: restituisce decisioni tipizzate con
probabilita' calibrate, tramite tre primitive Choice, Score e Noul.
Prezzo documentato 0,042 dollari per milione di token in ingresso, output gratis.

Non e' un'alternativa a un modello generativo, e' un complemento in tre punti:
il verdetto del critic, l'handoff dello swarm, il filtro sulle fonti.
[INFERENZA] L'uso piu' interessante non e' nell'agenzia ma negli score di
eleggibilita' di OpenScout, oggi scritti come regole a mano.

## Jina

**Chiave configurata in CI**, dieci miliardi di token. Usato per il Reader, che
scarica dall'infrastruttura di Jina e converte in markdown: sei volte meno token
a parita' di contenuto, e arriva dove il fetch diretto viene respinto.
Secondo impiego non ancora attivato: embedding e reranking per la ricerca nel
vault, quando l'indice non bastera' piu'.

## GuppyLM

Valutato e scartato come componente. E' un artefatto didattico da 8,7 milioni di
parametri. Utile per capire la catena da tokenizer a inferenza, inutile in
produzione.
