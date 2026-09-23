# Indice

Catalogo di tutto quello che c'è in `wiki/`. Lo aggiorna l'agente a ogni ingest.

Ultimo aggiornamento: 2026-09-23

## Thread aperti

Quello che è a metà. È la sezione che conta di più.

- [[thread-application-zai]] — bozza completa, manca solo il Submit.
- [[thread-post-linkedin]] — testo pronto in entrambe le lingue, screenshot veri disponibili. Manca solo pubblicarlo.
- [[thread-jarvis-locale]] — sessione operatore e routine create il 2026-09-22, in attesa di conferma dal secondo dispositivo.
- [[thread-k-sport-dynamix]] — in attesa che Marcolini si faccia vivo. Non inseguire Bobo via mail.

## Thread chiusi di recente

- [[thread-primo-giro-reale]] — chiuso il 2026-09-21. Quattro difetti trovati in due giri reali, tutti corretti.

## Decisioni

- [[decisione-confini-nel-codice]] — i limiti degli strumenti stanno in Python, non nel prompt. `attiva`
- [[decisione-stato-in-git]] — niente database, lo stato è un diff. `attiva`
- [[decisione-protocollo-testuale]] — `TOOL:` invece della tool-use nativa. `attiva`, verificata su due giri reali
- [[decisione-allowlist-stretta]] — `fetch` parte chiuso per scelta. `attiva`
- [[decisione-runtime-in-ci]] — GitHub Actions come runtime di esecuzione. `da rivedere` come unica superficie
- [[decisione-jarvis-sessione-persistente]] — l'operatore cross-device è una sessione, non un'app. `attiva`

## Entità

- [[entita-agency]] — il sistema multi-agente
- [[entita-provider-llm]] — DeepSeek, Z.ai, Anthropic, OpenRouter, TypeSafe, GuppyLM
- [[entita-fonti-dati]] — quali fonti calcistiche aperte rispondono davvero, e quali no
- [[entita-reep]] — registro identità giocatore: Transfermarkt e FBref sì, StatsBomb no
- [[entita-k-sport]] — potenziale integratore upstream in Dynamix 2, in attesa di Marcolini
- [[entita-sentinel]] — uno dei tre sistemi di interesse K-Sport, dettagli non in questo repo
- [[entita-ob1]] — Global e Lega Pro, valutazione di fusione in corso

## Concetti

- [[concetto-come-lavoro]] — il modo di lavorare del proprietario, e cosa lo rompe

## Fonti

- [[source-k-sport-call-2026-09-23]] — prima fonte reale in `raw/`: la call
  K-Sport del 23/09. `raw/` non è più vuoto.

## Nota di manutenzione

Questa sezione "Thread aperti" è testo libero e va aggiornata a mano quando un
thread cambia stato: `agency brief` legge il frontmatter, non questa pagina, e
i due possono disallinearsi. È successo davvero il 2026-09-22, scoperto dal
primo check-in della sessione Jarvis: leggeva ancora qui un thread chiuso da
due commit. Ad ogni chiusura di thread, aggiornare **sia** il frontmatter
**sia** questa lista nello stesso commit.
