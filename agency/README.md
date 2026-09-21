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
| `critic` | QA avversariale. Cerca allucinazioni e requisiti scoperti | `read_file` |

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

## Setup in 5 minuti

### 1. Chiave del modello

`Settings → Secrets and variables → Actions → New repository secret`

- `ANTHROPIC_API_KEY`, **oppure** `OPENROUTER_API_KEY`

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
| `AGENCY_PROVIDER` | `echo` | `anthropic` / `openrouter` / `echo` |
| `AGENCY_MODEL` | per provider | Override del modello |
| `AGENCY_MAX_STEPS` | `12` | Tetto sui passi di una missione |
| `AGENCY_MAX_TOKENS` | `2000` | Tetto per singola chiamata |
| `AGENCY_MAX_MISSIONS` | `3` | Missioni per giro di CI |
| `AGENCY_STATE_DIR` | `agency/state` | Dove vive lo stato |
| `AGENCY_OUTPUT_DIR` | `agency/output` | Dove finiscono gli artefatti |
| `AGENCY_MAX_TOOL_CALLS` | `6` | Chiamate a strumenti per turno |
| `AGENCY_FETCH_ALLOWLIST` | vuoto | Domini extra consentiti a `fetch` |
| `AGENCY_FETCH_MAX_BYTES` | `200000` | Tetto su una pagina scaricata |
| `AGENCY_MAX_ARTIFACTS` | `12` | File per missione |

## Test

```bash
python -m unittest agency.tests.test_agency -v
```

64 test, stdlib, **nessuna rete e nessuna chiave**: topologie e strumenti sono
verificati con un provider scriptato deterministico. I test sugli strumenti
coprono i confini reali: traversal, percorsi assoluti, domini fuori allowlist,
indirizzi privati, tetti su dimensione e numero di file.

## Vincoli di progetto

- **Zero dipendenze**: solo stdlib Python e JS nativo. Gira identico su Termux,
  in CI e in un container minimale. Niente lockfile da mantenere.
- **Offline-first**: la console si apre e resta leggibile senza rete, con
  l'ultimo stato noto dichiarato come tale.
- **Nessuna esecuzione lato client**: il telefono può spegnersi, il lavoro no.
- **Fallimento isolato**: una missione che esplode non ferma la coda; l'errore
  resta scritto sulla missione e lo vedi dal telefono.
