---
type: decision
title: Jarvis è una sessione Claude Code Remote persistente, non un'app nuova
updated: 2026-09-22
sources: [raw/richiesta-cross-device-2026-09-22.md]
status: attiva
---

# Jarvis è una sessione persistente

Mirko ha chiesto continuità cross-device sulla stessa base di Claude Code:
sessioni iniziate in locale fisso che proseguono su mobile e viceversa.

## La scoperta che ha risolto il problema

Questa conversazione **è già** una sessione Claude Code Remote
(`session_01JG4PKpuwZoqD4VUoqC8MhT`), con `cross_session_inbound: available`.
La continuità cross-device non andava costruita: **è una proprietà della
piattaforma**, non un problema dell'agenzia. Qualunque sessione Claude Code
Remote si apre identica da desktop, web e mobile.

Quello che mancava non era la sincronizzazione. Era una sessione **dedicata e
permanente** per operare l'agenzia, distinta dalle sessioni di build come
questa, più un modo per farla parlare per prima invece di aspettare che
Mirko apra l'app e chieda.

## Cosa è stato creato

- **Sessione**: `session_01U2exBrt8M68PcRGL7S5ivb`, titolo "Jarvis — Tornani
  Sport Tech", stesso repository e stesso ambiente di questa sessione di
  build. Si apre da qualunque dispositivo con la sua URL Claude Code.
- **Routine**: `trig_018HcvbHQ3Fza9iAwvSeaKER`, due volte al giorno
  (06:00 e 18:00 UTC). Ad ogni sveglia: `git pull`, `agency brief`,
  confronto con quanto già sa dalle conversazioni precedenti nella stessa
  sessione (la memoria si accumula da sola, senza bisogno di un file).
  Notifica push **solo** se è cambiato qualcosa di vero. Altrimenti silenzio.

Il pattern non è inventato: replica esattamente una routine già attiva su
questo account per un altro progetto (FindMeAJob), che manda un messaggio
solo se ha trovato qualcosa e altrimenti tace.

## Le quattro superfici, e cosa fa ciascuna

Non si sostituiscono a vicenda. Ognuna ha un solo compito.

| Superficie | Compito | Presidiata |
|---|---|---|
| GitHub Actions | **Esecuzione** delle missioni | No, cron ogni 30 min |
| Vault | **Memoria** che sopravvive alle missioni | No |
| Console PWA | **Sguardo veloce**, crea missioni in 10 secondi | Sì, quando Mirko la apre |
| Sessione Jarvis | **Pensare insieme**, notifiche proattive | Sì, ma sveglia da sola |

## Collaudo del 2026-09-22, esito

Lanciato manualmente alle 05:27 UTC invece di aspettare le 06:00. La sessione
si è avviata, ha letto lo schema e l'indice del vault, ha completato il turno
senza errori.

**Ha trovato un difetto vero al primo giro**, che non è un caso: leggere il
vault da zero, senza il contesto di chi lo scrive, è esattamente il test che
serve. `index.md` elencava ancora `thread-primo-giro-reale` come aperto,
mentre il frontmatter della pagina lo marcava `chiuso` da due commit. Il
frontmatter è la fonte per `agency brief`, `index.md` è testo libero
mantenuto a mano: i due si erano disallineati. Corretto, e aggiunta una nota
di manutenzione nello stesso file perché non ricapiti.

**Non ancora confermato**: che Mirko riesca davvero a riaprire la sessione da
un secondo dispositivo. Questo lo verifica solo lui.

## Cosa manca, dichiarato

- La notifica push richiede Remote Control collegato sul telefono di Mirko:
  non è qualcosa che si possa verificare o attivare da qui.
  [DATO MANCANTE] se è già collegato.
- Nessuna sveglia guidata da evento (per esempio un webhook quando GitHub
  Actions fallisce): oggi solo il cron due volte al giorno. `watch_url`
  esiste come strumento e sarebbe il passo successivo, non ancora costruito.
