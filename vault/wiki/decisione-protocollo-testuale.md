---
type: decision
title: Protocollo testuale degli strumenti invece della tool-use nativa
updated: 2026-09-21
sources: [agency/state/runs/m-20260921-195239-valuta-se-il-repository.json]
status: attiva con correzioni
---

# Protocollo testuale

L'agente chiama uno strumento con due righe: `TOOL: nome` e gli argomenti JSON.

## Perche'

Un motore solo su Anthropic, Z.ai, DeepSeek, OpenRouter e offline. I test
girano senza rete e senza chiavi.

## Il primo giro reale l'ha messa alla prova, e in parte l'ha rotta

DeepSeek, topologia team, 5 passi, 62 secondi. Cosa e' successo davvero:

| | Esito |
|---|---|
| `fetch` via Jina | **funziona**, README scaricato al primo colpo |
| `vault_list`, `vault_read` | **funzionano**, 12 chiamate |
| `write_file` del writer | **fallito in silenzio** |

Il writer ha emesso una chiamata `write_file` valida, ma la risposta si e'
fermata a 6.449 caratteri, troncata dal tetto sui token a meta' del JSON. Il
JSON non si chiudeva, l'espressione regolare non ha trovato la chiamata, e il
testo e' stato scambiato per la risposta finale. **Nessun file scritto, nessun
errore segnalato.** Zero artefatti su cinque previsti dal piano.

## Le tre correzioni

1. **Una riga `TOOL:` senza JSON completo ora e' riconosciuta come troncatura**
   e torna all'agente con istruzioni, invece di passare per prosa.
2. **I contenuti lunghi escono dal JSON.** Si passa solo il percorso e il testo
   va in un blocco `<<<CONTENT ... CONTENT`: niente escape, niente virgolette
   da proteggere, molti meno token.
3. **Il tetto sui token passa da 2.000 a 8.000.** Un documento intero non ci
   stava.

## La cosa che ha funzionato meglio del previsto

Gli agenti si sono rifiutati di mentire. Il librarian ha scritto "non ho
prodotto sources.md, e dire il contrario sarebbe la violazione piu' grave
possibile in questo vault". Il critic ha dato VERDETTO: RIFARE spiegando che i
file da verificare non esistevano. Entrambi avevano verificato con
`vault_list`, non supposto.

[INFERENZA] La disciplina delle fonti e dei dati mancanti regge sotto stress:
messi davanti a un compito ineseguibile, gli agenti hanno dichiarato il
problema invece di produrre un risultato plausibile e falso. E' esattamente il
comportamento per cui esiste il ruolo del critic.

Collegata: [[thread-primo-giro-reale]], [[decisione-confini-nel-codice]].
