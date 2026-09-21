# Agency — agenzia autonoma, sempre accesa

Un team di agenti che esegue missioni **senza che tu sia davanti al computer**.
Nessun server da pagare, nessun deploy: il runtime è GitHub Actions, la console è
una PWA che installi sul telefono.

```
telefono / browser          GitHub                        runtime
┌──────────────┐   PUT    ┌────────────────────┐  cron   ┌──────────────────┐
│ PWA console  │ ───────► │ agency/state/      │ ──────► │ Actions:         │
│ (offline ok) │ ◄─────── │   missions/*.json  │ ◄────── │ python -m agency │
└──────────────┘  index   │   runs/*.json      │ commit  │      work        │
                          └────────────────────┘         └──────────────────┘
```

La missione è un file JSON. Lo stato è versionato in git: ogni esecuzione lascia
una traccia diffabile, quindi l'agenzia è **auditabile scorrendo la history**.

## Le tre topologie

| Topologia | Come funziona | Quando serve |
|---|---|---|
| `solo` | Un agente, un turno | Baseline. Veloce, economico, nessun controllo incrociato |
| `team` | Il PM scompone in 2-5 passi, gli specialisti eseguono in sequenza vedendo chi li precede | Default. Lavoro strutturato con deliverable |
| `swarm` | Nessun centro: ogni agente chiude con `DONE` o delega con `HANDOFF: <id>` | Problemi aperti dove il percorso non è noto in partenza |

Il tetto sui passi (`AGENCY_MAX_STEPS`, default 12) esiste perché uno swarm senza
freno gira all'infinito mentre nessuno guarda.

## Il roster

Gli agenti sono **dati, non codice**: un file JSON in `agency/agents/`.
Aggiungere un ruolo non richiede di toccare l'orchestratore.

| Agente | Ruolo | Strumenti |
|---|---|---|
| `pm` | Scompone la missione in un piano JSON. Non esegue | nessuno |
| `researcher` | Fatti e fonti. Marca `[STIMA]` e `[DATO MANCANTE]`, non inventa numeri | `fetch` |
| `analyst` | Metriche, scoring, analisi situazionale. Nessuna conclusione senza il numero | `fetch`, `write_file` |
| `engineer` | Python / JS offline-first. Codice eseguibile, modifiche chirurgiche | `read_file`, `write_file` |
| `writer` | Deliverable finale in markdown, denso, senza preamboli | `write_file` |
| `critic` | QA avversariale. Cerca allucinazioni e requisiti scoperti | `read_file`, `vault_read` |
| `librarian` | Archivista del vault. Ingerisce fonti, aggiorna la wiki, fa il lint | `vault_*` |

Il `critic` è il motivo per cui un team batte un modello solo: un singolo agente
non mette mai in discussione le proprie allucinazioni.

## Gli strumenti

Senza strumenti un'agenzia produce testo. Con gli strumenti produce **file veri**,
committati nel repo dalla CI e apribili dal telefono con un tap.

| Strumento | Cosa fa | Confine applicato nel codice |
|---|---|---|
| `fetch` | Scarica una pagina o una API pubblica e ne restituisce il testo | Solo HTTPS, solo domini in allowlist, mai indirizzi privati, tetto a 200 KB |
| `write_file` | Salva un file tra gli artefatti della missione | Solo dentro `agency/output/<mission_id>/`, niente traversal, max 12 file |
| `read_file` | Legge un file già presente nel repository | Solo estensioni testuali, niente `.git` né file nascosti |
| `vault_list` | Elenca le pagine del vault | Confinato al vault |
| `vault_read` | Legge una pagina della wiki o una fonte | Confinato al vault, solo testo |
| `vault_write` | Scrive una pagina della wiki | **Solo `wiki/`**, più `index.md` e `log.md`. `raw/` è immutabile |

I confini stanno nel codice, non nel prompt: **un prompt non è un controllo di
sicurezza**. Un errore di uno strumento torna all'agente come messaggio, così può
correggersi da solo invece di far fallire tutta la missione.

### Allowlist di `fetch`

Default stretto su fonti aperte: Wikipedia, Wikidata, GitHub, football-data,
openfootball, FIFA, UEFA. Una allowlist larga trasforma l'agente in un crawler
che gira da solo in CI. Si estende senza toccare il codice:

```bash
AGENCY_FETCH_ALLOWLIST=fbref.com,sofascore.com python -m agency work
```

Gli URL Wikipedia `/wiki/<titolo>` vengono riscritti sull'API di estrazione testo.
La pagina HTML è metà menu di navigazione e lista lingue: passarla al modello
brucia contesto senza aggiungere informazione. La fonte citata nel report resta
comunque l'articolo leggibile da un umano.

### Il protocollo

Protocollo testuale invece della tool-use nativa, così il motore resta uno solo
su Anthropic, su OpenRouter e offline. L'agente chiude il messaggio con due righe:

```
TOOL: fetch
{"url": "https://it.wikipedia.org/wiki/Aldo_Simoncini"}
```

Riceve il risultato e continua, fino al tetto di `AGENCY_MAX_TOOL_CALLS`
(default 6). Oltre quel tetto gli si chiede la risposta finale: è lì che si
ferma un agente che si incaponisce su una fonte che non risponde.

### Dove finiscono i file

`agency/output/<mission_id>/`, committati dalla CI insieme allo stato. Nella
console ogni missione mostra i file prodotti come link diretti. Il ciclo si
chiude senza che tu debba organizzare niente.

## Il vault: la memoria fra una missione e l'altra

Il limite più serio di questa agenzia era che ogni missione ripartiva da zero.
Il vault è la risposta, e segue il pattern
[LLM Wiki di Karpathy](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f):
invece di ritrovare le cose a ogni domanda, l'agente **compila una volta e
mantiene**. La conoscenza si accumula invece di essere riscoperta.

```
vault/
├── AGENTS.md    # lo schema: come si tiene questa wiki. Lo leggi e lo scrivi tu
├── raw/         # le tue fonti. IMMUTABILI: l'agente legge e non tocca mai
├── wiki/        # le pagine. Le scrive l'agente, tu le leggi
├── index.md     # catalogo, aggiornato a ogni ingest
└── log.md       # append-only: grep "^## \[" log.md | tail -5
```

L'inversione rispetto a un vault normale è il punto: **tu non mantieni la
wiki**. Karpathy lo dice meglio di me, e vale la pena riportarlo: le persone
abbandonano le wiki perché il costo di manutenzione cresce più in fretta del
valore. Un modello non si annoia e non dimentica di aggiornare un riferimento
incrociato.

### Puntarlo al tuo vault Obsidian vero

```bash
export AGENCY_VAULT_DIR=~/Documenti/ObsidianVault
python -m agency --provider deepseek new "Ingerisci raw/articolo.md nella wiki" \
  --topology solo --agents librarian --run
```

Obsidian è l'IDE, l'agente è il programmatore, la wiki è il codice sorgente.
Non serve nessun plugin: sono file markdown su disco.

### Le quattro operazioni

| Operazione | Cosa fa | Dove gira bene |
|---|---|---|
| `ingest` | Legge una fonte, scrive la pagina, **aggiorna tutte le pagine che tocca** | In locale, con te che guardi |
| `query` | Risponde citando le pagine, e filia la risposta come nuova pagina | In locale |
| `lint` | Cerca contraddizioni, decisioni superate, thread fermi, pagine orfane | **Non presidiato, a ciclo** |
| `prune` | Marca `abbandonato` quello che è fermo da oltre 90 giorni | Non presidiato |

Il lint è la cosa che questa agenzia sa fare e che una chat non può fare: gira
mentre non ci sei, e ti dice cosa si sta contraddicendo o marcendo.

### Quando chiuderlo

Sta scritto anche in `AGENTS.md`, perché è il rischio vero. Una wiki personale
scritta da un modello è esattamente il progetto che sembra profondo e non
produce niente. Se `log.md` contiene solo righe `ingest` e nessuna `query`, stai
facendo archiviazione, non pensiero. Chiudilo invece di continuare a nutrirlo.

## Setup in 5 minuti

### 1. Chiave del modello

`Settings → Secrets and variables → Actions → New repository secret`

- `ANTHROPIC_API_KEY`, `ZAI_API_KEY`, `DEEPSEEK_API_KEY` **oppure** `OPENROUTER_API_KEY`

Con più chiavi configurate, la variabile `AGENCY_PROVIDER` decide quale usare.

Z.ai e DeepSeek espongono endpoint compatibili OpenAI, quindi usano lo stesso
client di OpenRouter. Default `glm-5.3` e `deepseek-flash`.

Entrambi ragionano di default, e per turni corti è budget speso in
ragionamento invece che in risposta. GLM non permette di spegnerlo, quindi lo
sforzo parte da `low`. DeepSeek lo permette, quindi parte spento.

Senza chiavi il workflow gira lo stesso in **dry-run deterministico**
(provider `echo`): verifichi la pipeline senza spendere un token.

Variabili opzionali (tab *Variables*): `AGENCY_MODEL`, `AGENCY_MAX_MISSIONS`, `AGENCY_MAX_STEPS`.

### 2. Permessi di scrittura per il workflow

`Settings → Actions → General → Workflow permissions` → **Read and write permissions**.
Senza questo il runtime non può committare i risultati.

### 3. Pubblica la console

`Settings → Pages → Deploy from a branch → main / (root)`.
La console è su `https://<utente>.github.io/<repo>/agency/web/`.
Su Android: *Aggiungi a schermata Home* → si comporta da app.

### 4. Token per comandarla dal telefono

`github.com/settings/personal-access-tokens` → fine-grained, **solo su questo repo**:

- **Contents**: read and write (scrive il file della missione)
- **Actions**: read and write (sveglia il workflow; senza, la missione parte comunque al cron)

Incollalo in *Setup* nella console. Resta in `localStorage` sul tuo dispositivo:
non viene inviato a nessuno tranne `api.github.com`.

## Uso

### Dal telefono
Console → obiettivo → topologia → **Invia**. Il workflow parte subito.
Senza rete o senza token la missione finisce in **coda locale** e viene inviata
al primo *Aggiorna* utile: non si perde nulla.

### Da GitHub, senza console
`Actions → Agency → Run workflow` → compila *objective*. Funziona anche dall'app
GitHub per Android.

### Da riga di comando
```bash
python -m agency roster                       # chi lavora qui
python -m agency new "Shortlist oriundi SMR"  # crea (pending)
python -m agency new "..." --run              # crea ed esegue subito
python -m agency new "..." --topology swarm --agents analyst
python -m agency list --status done
python -m agency show <mission_id> --deliverable
python -m agency work --limit 3               # svuota la coda (è ciò che fa la CI)
python agency/serve.py                        # console in locale su :8787
```

Provare senza spendere:
```bash
python -m agency --provider echo new "Prova la pipeline" --run
```

## Configurazione

| Variabile | Default | Cosa fa |
|---|---|---|
| `AGENCY_PROVIDER` | `echo` | `anthropic` / `zai` / `deepseek` / `openrouter` / `echo` |
| `AGENCY_DEEPSEEK_THINKING` | `disabled` | Thinking DeepSeek: `disabled`, `low`, `high`, `max` |
| `AGENCY_ZAI_REASONING` | `low` | Sforzo di reasoning per i modelli GLM |
| `AGENCY_MODEL` | per provider | Override del modello |
| `AGENCY_MAX_STEPS` | `12` | Tetto sui passi di una missione |
| `AGENCY_MAX_TOKENS` | `2000` | Tetto per singola chiamata |
| `AGENCY_MAX_MISSIONS` | `3` | Missioni per giro di CI |
| `AGENCY_STATE_DIR` | `agency/state` | Dove vive lo stato |
| `AGENCY_OUTPUT_DIR` | `agency/output` | Dove finiscono gli artefatti |
| `AGENCY_VAULT_DIR` | `vault/` | Il vault. Puntalo al tuo Obsidian |
| `AGENCY_MAX_TOOL_CALLS` | `6` | Chiamate a strumenti per turno |
| `AGENCY_FETCH_ALLOWLIST` | vuoto | Domini extra consentiti a `fetch` |
| `AGENCY_FETCH_MAX_BYTES` | `200000` | Tetto su una pagina scaricata |
| `AGENCY_MAX_ARTIFACTS` | `12` | File per missione |

## Test

```bash
python -m unittest agency.tests.test_agency -v
```

88 test, stdlib, **nessuna rete e nessuna chiave**: topologie e strumenti sono
verificati con un provider scriptato deterministico. I test sugli strumenti
coprono i confini reali: traversal, percorsi assoluti, domini fuori allowlist,
indirizzi privati, tetti su dimensione e numero di file, e l'immutabilità di
`raw/` nel vault.

## Vincoli di progetto

- **Zero dipendenze**: solo stdlib Python e JS nativo. Gira identico su Termux,
  in CI e in un container minimale. Niente lockfile da mantenere.
- **Offline-first**: la console si apre e resta leggibile senza rete, con
  l'ultimo stato noto dichiarato come tale.
- **Nessuna esecuzione lato client**: il telefono può spegnersi, il lavoro no.
- **Fallimento isolato**: una missione che esplode non ferma la coda; l'errore
  resta scritto sulla missione e lo vedi dal telefono.
