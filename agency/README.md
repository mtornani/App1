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

| Agente | Ruolo |
|---|---|
| `pm` | Scompone la missione in un piano JSON. Non esegue |
| `researcher` | Fatti e fonti. Marca `[STIMA]` e `[DATO MANCANTE]`, non inventa numeri |
| `analyst` | Metriche, scoring, analisi situazionale. Nessuna conclusione senza il numero |
| `engineer` | Python / JS offline-first. Codice eseguibile, modifiche chirurgiche |
| `writer` | Deliverable finale in markdown, denso, senza preamboli |
| `critic` | QA avversariale. Cerca allucinazioni e requisiti scoperti |

Il `critic` è il motivo per cui un team batte un modello solo: un singolo agente
non mette mai in discussione le proprie allucinazioni.

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

## Test

```bash
python -m unittest agency.tests.test_agency -v
```

30 test, stdlib, **nessuna rete e nessuna chiave**: le topologie sono verificate
con un provider scriptato deterministico.

## Vincoli di progetto

- **Zero dipendenze**: solo stdlib Python e JS nativo. Gira identico su Termux,
  in CI e in un container minimale. Niente lockfile da mantenere.
- **Offline-first**: la console si apre e resta leggibile senza rete, con
  l'ultimo stato noto dichiarato come tale.
- **Nessuna esecuzione lato client**: il telefono può spegnersi, il lavoro no.
- **Fallimento isolato**: una missione che esplode non ferma la coda; l'errore
  resta scritto sulla missione e lo vedi dal telefono.
