# OpenScout — Strategia: la nicchia che Wyscout non può occupare

## Il problema del mercato

Wyscout, InStat/Hudl, StatsBomb e SkillCorner si contendono lo stesso cliente:
il club professionistico con budget da €10.000–50.000/anno. Sotto quella soglia
c'è un deserto: **federazioni minori, procuratori indipendenti, club semi-pro,
direttori sportivi di Serie C/D, analisti freelance** — decine di migliaia di
operatori che oggi lavorano con Excel, YouTube e passaparola.

Competere frontalmente sui dati proprietari è impossibile (le aziende di event
data hanno centinaia di taggatori). La mossa giusta non è "Wyscout più
economico", è **cambiare l'asse della competizione**.

## La nicchia nuova: Eligibility Intelligence

Nessun incumbent risponde alla domanda: *"quali giocatori al mondo potrebbero
vestire la maglia della mia nazionale?"*

- Oltre 100 federazioni FIFA dipendono strutturalmente dagli oriundi
  (San Marino, Malta, Lussemburgo, Faroe, Gibilterra, ma anche Filippine,
  Indonesia, Giamaica, Marocco, Albania, Kosovo...).
- La risposta richiede di incrociare **performance + genealogia + diritto della
  cittadinanza + regolamento FIFA (RGAS art. 6–8)** — un problema di dati e
  regole, non di video. Perfetto per software, terribile per gli incumbent
  (fuori dal loro modello di business e dal loro cliente).
- I clienti: federazioni (budget piccolo ma reale), procuratori che vogliono
  "creare" un nazionale (il valore di mercato di un giocatore convocato sale),
  e le stesse associazioni di oriundi.

Questo repo aveva già il prototipo: **Radar SMR** (ricerca RAG di eleggibili
per San Marino). OpenScout lo generalizza a qualsiasi federazione e ci
costruisce attorno la piattaforma completa.

## Architettura del prodotto (3 livelli)

1. **Scouting & match analysis open-data** (gratis, acquisizione utenti)
   — metriche per-90, percentili per ruolo, rating OS, similarity engine,
   xG race, pass network, shot map, report HTML condivisibili.
   Dati: StatsBomb open data oggi; FBref/Transfermarkt e tagging manuale domani.
2. **Eligibility Intelligence** (il prodotto a pagamento)
   — motore di regole FIFA + leggi di cittadinanza per federazione, screening
   della diaspora sui dataset, shortlist "NOW / WHAT-IF".
3. **Ancestry deep-dive** (servizio premium)
   — la pipeline RAG di Radar SMR verifica genealogia e fonti sui nomi in
   shortlist. Umano nel loop, margini alti, difendibilissimo.

## Perché il costo è ~zero

- **Zero dipendenze npm**: tutto Node standard library. Niente build, niente
  supply chain, gira su qualsiasi Node 18+.
- **Dati gratuiti**: StatsBomb open data (event data professionale: Mondiali,
  Euro, Champions, Liga era-Messi, Bundesliga, calcio femminile...).
- **Cache su disco**: ogni file scaricato una volta sola.
- **Deploy**: un container da 256MB su Railway/Fly (free tier) o un VPS da €4.
  I report sono HTML statici autosufficienti: condivisibili via WhatsApp,
  pubblicabili su GitHub Pages.

## Pricing proposto

| Tier | Prezzo | Cosa include |
|---|---|---|
| Open | €0 | scouting open-data, report, self-host |
| Scout | €29/mese | dataset propri (CSV/tagging), report white-label |
| Federation | €490/anno | Eligibility Intelligence su misura, screening continuo |
| Deep-dive | €a progetto | dossier genealogico-legale per giocatore |

Wyscout parte da ~€5.000/anno per un singolo posto. Un'intera federazione
piccola spende qui meno di un decimo.

## Moat (perché non ti copiano)

1. **Knowledge base regolatoria**: le regole di cittadinanza di 100+ paesi +
   RGAS FIFA codificate e mantenute sono noiose da costruire — il vantaggio
   si accumula.
2. **Dati proprietari generati dagli utenti**: ogni deep-dive verificato
   arricchisce un grafo genealogico-calcistico che nessun altro ha.
3. **Community open-source** sul livello 1: distribuzione gratuita,
   contributi gratuiti.
4. Gli incumbent non possono seguirti senza cannibalizzare il proprio listino.

## Roadmap

- [x] MVP: ingestione open-data, metriche, percentili, rating, similarity,
      match analysis, eligibility engine, report HTML, web UI, CLI
- [ ] Import CSV/manuale per leghe non coperte (Serie D, NPL australiana...)
- [ ] Knowledge base cittadinanza: da 4 a 50 federazioni
- [ ] Integrazione diretta pipeline Radar SMR come worker "deep-dive"
- [ ] Multi-utente + shortlist condivise (il momento del SaaS)
- [ ] Video linking: timestamp evento → clip YouTube/Veo dei match amatoriali
