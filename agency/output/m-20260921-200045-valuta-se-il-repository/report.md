# Scheda di valutazione — `withqwerty/reep` per il matching identità giocatore (Transfermarkt / FBref / StatsBomb)

**Fonte unica verificata**: `https://raw.githubusercontent.com/withqwerty/reep/main/README.md`
Scaricata il: sessione corrente. Ramo `main`. Non è stato scaricato nessun altro file del repo, né `data/*.csv`, né `data/meta.json`, né i siti esterni `reep.football/*`.
**Unità di misura / convenzioni**: i conteggi di riga sono "record dichiarati nel README", non conteggi verificati sui file. Le citazioni sono riportate verbatim fra virgolette.

---

## (a) Provider effettivamente coperti — con citazione testuale

**Dichiarazione di copertura complessiva** (citazione):
> "The football entity register. Maps player, team, coach, competition, and season identities across Transfermarkt, FBref, UEFA, Sofascore, and 30+ data providers."

**Transfermarkt — COPERTOCONFERMATO** (schema colonne, citazione):
> "| `key_transfermarkt` | [Transfermarkt](https://www.transfermarkt.com/) player ID | `568177` |"
> "| `key_transfermarkt_manager` | Transfermarkt manager ID (coaches only) | `50100` |"

**FBref — COPERTOCONFERMATO** (schema colonne, citazione):
> "| `key_fbref` | [FBref](https://fbref.com/) player ID | `dc7f8a28` |"
> "| `key_fbref_verified` | FBref ID (cross-verified via worldfootballR) | `dc7f8a28` |"

**StatsBomb — NON CITATO** : la stringa "StatsBomb" (e varianti "statsbomb"/"StatsBomb") **non compare nel README**. Non esiste alcuna colonna `key_statsbomb` nello schema People, Teams, Competitions o Seasons, e StatsBomb non figura nella tabella "Coverage". Verifica: assenza per scansione del testo del README.

**Altri provider con colonna dedicata nello schema People** (elenco ricavato dai campi `key_*` del README):
Transfermarkt, FBref, Soccerway, Sofascore, Flashscore, Opta (alphanumeric), Premier League, 11v11, ESPN, National Football Teams, WorldFootball.net, Soccerbase, Kicker, UEFA, L'Equipe, FFF.fr, Lega Serie A, BeSoccer, FootballDatabase.eu, EU-Football.info, Barry Hugman's Footballers, DFB (German FA), StatMuse, SoFIFA/EA FC, Soccerdonna, Dongqiudi, Understat, WhoScored, SportMonks, API-Football, FotMob, Opta numeric, TheSportsDB, SkillCorner, Wyscout, Impect, heim:spiel, Capology.
**Nota metodologica**: conteggio eseguito da me sulle righe `key_*` del README = ~38 namespace su People; il README dichiara "30+ data providers" — la mia conta è una stima, non un dato certificato dal README.

**Fonti di mapping** (citazione dalla sezione Coverage):
> "**Wikidata** IDs are community-maintained; they updated automatically with each refresh while v0 was live, and are now fixed at the `2026.25` snapshot. **Verified** IDs were matched independently using DOB, name, and cross-provider bridges, then validated before inclusion."

---

## (b) Formato di output dei dati — con citazione testuale

**v0 (dentro questo repo) — CSV + JSON** (citazione):
> "| File | Records | Description |"
> "| [`data/people.csv`](data/people.csv) | 444,707 | Players and coaches with provider IDs and bio |"
> "| [`data/teams.csv`](data/teams.csv) | 45,337 | Clubs with provider IDs and metadata |"
> "| [`data/competitions.csv`](data/competitions.csv) | 212 | Leagues, cups, and tournaments with provider IDs |"
> "| [`data/seasons.csv`](data/seasons.csv) | 1,200 | Season editions of competitions |"
> "| [`data/names.csv`](data/names.csv) | 27,591 | Alternate names and aliases |"
> "| [`data/meta.json`](data/meta.json) | — | Generation timestamp and counts |"
- Conteggi: **dichiarati** nel README, non verificati da me sul file.

**v1 (fuori repo, superficie pubblica) — CSV canonici + bundle DuckDB + metadata** (citazione):
> "The v1 release files use a different bridge-register contract with canonical CSVs, a DuckDB convenience bundle, release metadata, namespace-scoped bridges, bridge-only provider roles and overlay-only Wikidata aliases."
> "| Download the register (CSV + DuckDB) | [reep.football/downloads](https://reep.football/downloads) |"

**Superficie API** (citazione):
> "The API in this repository is the v0 REST interface served through RapidAPI and the legacy Cloudflare Worker."
> "The v1 API is release-backed, uses direct Reep API keys, and requires namespace-aware provider ID resolution:"
> `curl -H "Authorization: Bearer $REEP_API_KEY" "https://reep.football/api/v1/resolve/transfermarkt/568177?namespace=spieler&type=player"`

**Chiave canonica** (citazione):
> "Every entity in the register has a self-minted Reep ID as its canonical identifier. The format is `reep_<type_prefix><8hex>`"

---

## (c) Licenza dichiarata — con citazione testuale

**Sezione "License", citazione integrale:**
> "The data is derived from [Wikidata](https://www.wikidata.org/) and is available under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)."

**Cosa NON copre la licenza pubblica** (citazione):
> "**Why isn't the v1 engine in this repository?** The register is open; the engine that builds and repairs it is not."
> "This repo publishes IDs, the API, and the published CSVs — not scraping logic or raw data dumps from providers. Matching and ingestion scripts are maintained in a separate private repo."

**Sintesi**: i **dati** (CSV / DuckDB / API outputs della superficie pubblica) sono dichiarati CC0 1.0. Il motore di matching/ingestion NON è in licenza aperta (repo privato).

---

## (d) Sezione "Non verificato"

Tutto ciò che segue è **Non verificato**: il README lo dichiara, lo lascia ambiguo, oppure rimanda a risorse esterne che non ho potuto scaricare.

1. **StatsBomb — copertura reale = ZERO sulla base del README.**
   - Non verificato se esista una copertura StatsBomb fuori dal README (es. su `reep.football/coverage`): URL non scaricato.
   - Il README non menziona mai StatsBomb. Di conseguenza, allo stato attuale delle evidenze documentali, **il crosswalk TM↔FBref↔StatsBomb non è supportato da questo registro**; serve un layer di mapping esterno.

2. **Mapping ID cross-provider: non verificato sui dati.**
   - Il README **dichiara** il crosswalk (esempio Cole Palmer: `reep_p2804f5db`, `key_transfermarkt=568177`, `key_fbref=dc7f8a28`) ma io non ho scaricato `data/people.csv` per confermare che le righe esistano e che le colonne siano valorizzate come dichiarato.
   - **Copertura per-provider in termini numerici**: il README afferma che "Coverage depends on what the Wikidata community has mapped plus independently verified mappings" e rinvia a `GET /stats` (endpoint non testato). **Percentuale di righe in `people.csv` con `key_transfermarkt` non vuoto, `key_fbref` non vuoto, o entrambi, non verificata.**
   - **Qualità del matching**: il README non riporta precision/recall numerici per la release v0 pubblicata. La pagina `reep.football/entity-resolution` e `reep.football/sponsorship` sono citate come contenenti "measured precision and recall of each release" ma **non scaricate**.

3. **Formato dei dati v1 — non verificato.**
   - Il README dice "canonical CSVs, a DuckDB convenience bundle, release metadata" ma non documenta le colonne, gli schemi, né una versione di schema. `reep.football/downloads` non scaricato.

4. **Data di aggiornamento — confermata solo via README, non dal file.**
   - Citazione: "The last CSV release was `2026.25` (21 June 2026), and the API's database has taken no writes since 25 April 2026."
   - Il README dice che `data/meta.json` "records when the current CSVs were generated", ma **il file `data/meta.json` non è stato scaricato**: la data `2026.25` è quindi *dichiarata*, non riscontrata sul metadata di release.

5. **Contenuto reale dei CSV — non verificato.**
   - I conteggi 444.707 / 45.337 / 212 / 1.200 / 27.591 sono **dichiarati nel README**; nessun confronto con `wc -l` sui file.

6. **Ramo `master` — non testato.** README su `main` esistente e completo; non ho verificato se `master` contenga una versione diversa.

7. **Licenza — verifica formale del file di licenza nel repo non eseguita.**
   - Il README dichiara CC0 1.0 per i dati, ma **non ho scaricato un eventuale file `LICENSE` nel repo** per verificare che la licenza sia formalmente presente come file e non solo come affermazione testuale del README.

8. **Endpoint RapidAPI / Worker / API v1 — non testati.**
   - `/search`, `/resolve`, `/lookup`, `/stats` di v0 e `/api/v1/resolve/...` di v1 non chiamati.

9. **"30+ data providers" — non verificato in modo indipendente.**
   - La mia conta delle colonne `key_*` è una **stima** da README (~38 namespace su People), non un dato certificato.

10. **Rischio di doppia classificazione player/coach — dichiarato ma non verificato sui dati.**
    - Citazione: "People who are both players and coaches (e.g. Pep Guardiola) have separate records with distinct Reep IDs — `reep_p*` for the player record, `reep_c*` for the coach record."
    - Implicazione operativa: un join per persona fisica richiede una logica di aggregazione player+coach lato utente. **Non verificato**: quante persone fisiche siano effettivamente sdoppiate in due `reep_id`.

---

## Conclusione operativa (con la soglia segnale/rumore)

- **TM ↔ FBref**: **usabile**, se si accettano due condizioni verificate dal README: (1) licenza dei dati = CC0 1.0 (dichiarata), (2) snapshot v0 congelato al 2026.25. Soglia: se servono aggiornamenti post-21 giugno 2026, la v0 è rumore e bisogna passare a v1 (`reep.football/downloads`).
- **StatsBomb ↔ TM/FBref**: **non coperto dal README**. Segnale = assenza. Per usare StatsBomb occorre costruire un mapping StatsBomb↔TM esterno, con sample size e bias da quantificare fuori da questo registro.
- **Blocco alla decisione finale**: la copertura reale per-provider (quante righe hanno davvero `key_transfermarkt` e `key_fbref` valorizzati, e quanti duplicati player/coach) **non è verificabile dal README**; serve scaricare `data/people.csv` e calcolare i tassi di valorizzazione per colonna. Finché quel numero non c'è, la scelta "usare reep per il crosswalk" resta supportata solo da dichiarazioni del produttore, non da misure indipendenti.