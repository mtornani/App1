# Jarvis — l'operatore cross-device dell'agenzia

Risponde a una domanda precisa: come si usa l'agenzia da locale fisso *e*
locale mobile, con la stessa continuità di una sessione Claude Code che
prosegue da un dispositivo all'altro.

**La risposta non è un'app nuova.** Questa conversazione stessa è già una
sessione Claude Code Remote, apribile identica da desktop, web e telefono.
Mancava solo una sessione **dedicata** all'agenzia — distinta dalle sessioni
di build come quella che ha scritto questo file — più un modo per farla
parlare per prima invece di aspettare che tu apra l'app e chieda.

## Cosa esiste

| Cosa | Identificativo |
|---|---|
| Sessione Jarvis | `session_01U2exBrt8M68PcRGL7S5ivb` |
| Routine di check-in | `trig_018HcvbHQ3Fza9iAwvSeaKER`, due volte al giorno (06:00 e 18:00 UTC) |

Apri `https://claude.ai/code/session_01U2exBrt8M68PcRGL7S5ivb` da qualunque
dispositivo: telefono, portatile, l'app desktop. È la stessa sessione, con
tutta la sua memoria.

## Cosa fa da sola, senza che tu le scriva

Due volte al giorno: `git pull`, `python -m agency brief`, confronto con
quello che già sa dalle conversazioni precedenti. Ti manda una notifica push
**solo** se è cambiato qualcosa di vero — un nuovo elemento prioritario, un
thread fermo da troppo, una missione fallita. Altrimenti tace.

Il pattern non è nuovo: replica una routine già in uso su questo account per
un altro progetto, che manda un messaggio solo quando ha trovato qualcosa.

## Cosa fai tu, scrivendole

Qualunque cosa scriveresti in una sessione Claude Code normale: lancia una
missione, chiedile lo stato, fatti aggiornare il vault, fatti spiegare un
report. Ha letto lo schema del vault e sa come muoversi dentro l'agenzia.

## Le quattro superfici

Non si sostituiscono. Ognuna ha un solo compito.

| Superficie | Compito | Presidiata |
|---|---|---|
| GitHub Actions | Esecuzione delle missioni | No |
| Vault | Memoria che sopravvive alle missioni | No |
| Console PWA | Sguardo veloce, crea missioni in 10 secondi | Quando la apri |
| Sessione Jarvis | Pensare insieme, notifiche proattive | Sveglia da sola |

## Collaudo

Lanciata manualmente il 2026-09-22 invece di aspettare la prima sveglia
schedulata. Ha trovato un difetto vero al primo giro: `vault/index.md`
elencava un thread come aperto mentre il suo frontmatter lo marcava chiuso da
due commit. Corretto nello stesso giro. Il dettaglio è in
`vault/wiki/decisione-jarvis-sessione-persistente.md`.

## Cosa manca, dichiarato

- La notifica push richiede Remote Control collegato sul tuo telefono. Non è
  qualcosa che si possa attivare da qui: verificalo tu nell'app.
- Nessuna sveglia guidata da evento. Oggi solo il cron due volte al giorno.
  Un webhook che la sveglia quando GitHub Actions fallisce è il passo
  successivo, non ancora costruito.
- Che tu riesca davvero a riaprirla da un secondo dispositivo non è ancora
  confermato: lo verifichi solo tu.

## Per cambiare la cadenza

```python
# dal codice, non serve toccare la sessione
mcp__Claude_Code_Remote__update_trigger(
    trigger_id="trig_018HcvbHQ3Fza9iAwvSeaKER",
    cron_expression="0 */4 * * *",  # esempio: ogni 4 ore
)
```

Oppure chiediglielo direttamente: è una conversazione, non un file di
configurazione.
