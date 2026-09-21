# Schema del vault

Questo file dice a un agente come si tiene questa wiki. È la configurazione che
trasforma un modello generico in un archivista disciplinato. Va letto per intero
prima di toccare qualsiasi pagina.

Pattern di riferimento: LLM Wiki di Andrej Karpathy.
https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

## Le tre zone

| Zona | Chi scrive | Regola |
|---|---|---|
| `raw/` | solo l'umano | **Immutabile.** Un agente legge e non modifica mai. È la fonte di verità |
| `wiki/` | solo l'agente | L'umano legge, non scrive. Se scrive, l'agente non deve sovrascriverlo senza dirlo |
| `index.md`, `log.md` | solo l'agente | Aggiornati a ogni ingest |

L'inversione rispetto a un vault normale è voluta: **tu non mantieni la wiki.**
Se dipendesse dalla tua manutenzione sarebbe già morta fra tre settimane.

## Tipi di pagina

Ogni pagina in `wiki/` è uno di questi tipi, dichiarato nel frontmatter.

- `source` — cosa dice una fonte. Una per documento in `raw/`. Non interpreta, riassume.
- `entity` — una cosa che ricorre: un progetto, una persona, uno strumento, un cliente.
- `concept` — un'idea o un metodo che attraversa più fonti.
- `decision` — una decisione presa, con il perché e cosa la falsificherebbe.
- `thread` — un filo aperto: una domanda senza risposta, un lavoro a metà.

Frontmatter obbligatorio:

```yaml
---
type: decision
title: Protocollo testuale invece di tool-use nativa
updated: 2026-09-21
sources: [raw/chat-2026-09-21.md]
status: attiva        # attiva | superata | abbandonata
---
```

## Le quattro operazioni

### ingest
Arriva un file in `raw/`. L'agente lo legge, scrive la pagina `source`,
poi **aggiorna tutte le pagine esistenti che quella fonte tocca**: entità
citate, concetti, decisioni che conferma o contraddice. Infine aggiorna
`index.md` e appende a `log.md`.

Una fonte sola può toccare dieci pagine. È normale ed è il punto.

### query
Una domanda. L'agente legge `index.md`, apre le pagine rilevanti, risponde
**con le citazioni delle pagine usate**. Se la risposta è utile, la filia come
nuova pagina: le esplorazioni devono accumulare come le fonti, non evaporare
nella chat.

### lint
Controllo di salute, periodico e non presidiato. Cerca, in quest'ordine:

1. **Contraddizioni** fra pagine. Due pagine che dicono cose incompatibili.
2. **Decisioni superate** da fonti più recenti, ancora marcate `attiva`.
3. **Thread fermi.** Un `thread` non aggiornato da più di 21 giorni.
4. **Pagine orfane**, senza nessun link in entrata.
5. **Concetti nominati ma senza pagina.**

Output: una pagina `wiki/lint-<data>.md` con i problemi trovati e, per ognuno,
la correzione precisa. Non correggere da solo contraddizioni sostanziali:
segnalale.

### prune
Una pagina `thread` o `decision` che resta ferma oltre 90 giorni viene marcata
`abbandonata` con la data. Non si cancella niente: l'abbandono è un dato, e in
questo vault è il dato più informativo che ci sia.

## Regole di scrittura

- **Italiano**, denso, senza preamboli e senza chiusure di cortesia.
- Ogni affermazione che viene da una fonte porta il link alla fonte.
- Quello che l'agente deduce e che nessuna fonte dice va marcato `[INFERENZA]`.
- Quello che manca va marcato `[DATO MANCANTE: cosa serve]`. Non riempire i buchi.
- Una contraddizione si dichiara, non si media.
- Wikilink in stile Obsidian: `[[nome-pagina]]`.

## Formato del log

Prefisso fisso, così `grep "^## \[" log.md | tail -5` basta come interfaccia.

```
## [2026-09-21] ingest | Titolo della fonte
## [2026-09-21] query | La domanda posta
## [2026-09-21] lint | 3 contraddizioni, 2 thread fermi
```

## Come muore questo vault

Va detto qui, perché è il rischio vero e non un dettaglio.

Una wiki personale scritta da un LLM è esattamente il tipo di progetto che
sembra profondo e non produce niente. La difesa è una sola: **deve rispondere a
domande che fai davvero.** Se dopo due settimane non l'hai mai interrogata,
chiudila invece di continuare a nutrirla. Il `log.md` te lo dice senza
interpretazioni: se contiene solo righe `ingest` e nessuna `query`, stai
facendo archiviazione, non pensiero.
