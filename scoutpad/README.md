# ScoutPad — il taccuino digitale dello scout

**PWA mobile, offline-first, zero backend.** Tagging live a bordo campo,
scheda di valutazione, report HTML professionale condivisibile su WhatsApp.
Distribuibile **oggi**: è un sito statico, niente app store, niente server.

## Il bisogno non soddisfatto

Nei dilettanti, nelle giovanili e nelle leghe minori **le partite non hanno né
video né dati**: Wyscout e InStat lì semplicemente non esistono. Lo scout in
tribuna è l'unico sensore — e oggi lavora con taccuino di carta, memoria e
WhatsApp. Procuratori, osservatori, DS di Serie C/D e settori giovanili:
migliaia di professionisti senza strumenti, che devono comunque produrre
relazioni credibili per club e agenzie.

ScoutPad trasforma il telefono che hanno già in tasca nello strumento di
lavoro: si installa dalla home screen, funziona senza rete (campi di periferia
inclusi), e il report che esce sembra fatto da un'area scouting professionale.

## Cosa fa

- **Setup partita in 30 secondi**: squadre, competizione, giocatori da osservare.
- **Tagging live a un tocco**: 16 eventi (gol, tiri, dribbling, duelli, recuperi,
  palle perse, falli, parate, errori...) col cronometro della partita; undo,
  note rapide, vibrazione di conferma.
- **Scheda di valutazione**: 6 categorie (tecnica, tattica, fisico, velocità,
  mentalità, personalità) su scala 1–10, verdetto FIRMARE / MONITORARE /
  SCARTARE, note libere.
- **Report HTML autosufficiente** con radar SVG, statistiche evento, timeline e
  note — condiviso direttamente su WhatsApp/Telegram via share nativo, o
  stampabile in PDF dal browser.
- **Dati solo sul telefono** (localStorage) + backup/ripristino JSON. Niente
  account, niente GDPR-grattacapi, costo server: zero.

## Distribuirlo adesso

Il repo ha già GitHub Pages attivo in modalità "deploy from branch" su `main`:
**basta il merge su main** e l'app è online su

> **https://mtornani.github.io/App1/scoutpad/**

senza toccare alcuna impostazione (Pages copia i file statici così come sono).
Chi apre il link dal telefono fa "Aggiungi a schermata Home" e ha l'app.

Opzionale, per avere ScoutPad alla radice dell'URL (`/App1/`): imposta
*Settings → Pages → Source: GitHub Actions* e lancia manualmente il workflow
`.github/workflows/deploy-scoutpad.yml` (sostituisce il sito attuale del
README). Dominio proprio (es. `scoutpad.app`): €10/anno, costo totale di
esercizio.

Test locale: `node serve.js` → http://localhost:8080 (oppure da telefono sulla
stessa rete).

## Monetizzare adesso

Modello: **freemium con licenza a vita**. 3 report gratuiti, poi sblocco PRO.

1. Crea il prodotto su Gumroad (o Stripe Payment Link): *"ScoutPad PRO —
   licenza a vita"*, prezzo lancio **€49** (ancoraggio: Wyscout parte da
   ~€5.000/anno).
2. Cambia `LICENSE_SECRET` in `app.js` e metti l'URL del prodotto in `BUY_URL`.
3. A ogni vendita Gumroad ti notifica l'email dell'acquirente: generi la chiave
   con `SCOUTPAD_SECRET=tuo-secret node tools/genkey.js email@cliente.it` e
   gliela mandi (2 minuti; automatizzabile poi con un webhook).

> La validazione licenza è volutamente "soft" (HMAC client-side): tiene onesti
> gli onesti. A questo prezzo e per questo pubblico è il trade-off giusto —
> zero infrastruttura.

### Go-to-market della prima settimana

- **Canale diretto**: gruppi WhatsApp/Facebook di procuratori e osservatori
  (es. "osservatori calcio", AIPES, corsi da osservatore), DS di Eccellenza/
  Promozione/Serie D. Pitch: *"il report che mandi al club, fatto dal telefono
  mentre guardi la partita — gratis per 3 partite"*.
- **Effetto virale incorporato**: ogni report condiviso porta il footer
  ScoutPad davanti a DS e procuratori — il destinatario del report È il
  prossimo cliente.
- **Corsi per osservatori**: licenze in blocco scontate come materiale
  didattico.

## Sinergia con OpenScout

ScoutPad genera dati proprietari su partite che nessun data provider copre.
È il punto d'ingresso del funnel: i dati taggati alimenteranno le metriche di
[OpenScout](../openscout/README.md) (import previsto in roadmap) e le shortlist
di Eligibility Intelligence — la strategia completa è in
[openscout/STRATEGY.md](../openscout/STRATEGY.md).

## Sviluppo

```bash
node serve.js          # server locale su :8080
npm install && npm test   # smoke test del flusso completo (jsdom, solo dev)
node tools/genkey.js email@cliente.it   # genera chiave licenza
```

File: `index.html` (shell+stili) · `app.js` (tutta la logica) · `sw.js`
(offline) · `manifest.webmanifest` + `icon.svg` (installabilità PWA).
Zero dipendenze a runtime.

## Roadmap

- [ ] Webhook Gumroad → consegna automatica della chiave
- [ ] Note vocali (Web Speech API) durante il live
- [ ] Export CSV eventi → import in OpenScout
- [ ] Shortlist multi-partita per giocatore (storico osservazioni)
- [ ] Modalità squadra: due scout, stessa partita, report unificato
