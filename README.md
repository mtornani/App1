# Tornani Sport Tech

Monorepo di strumenti di football intelligence da dati aperti, più l'agenzia di
agenti che li costruisce e li mantiene.

Una persona sola più un team di agenti. Non è uno slogan: è la struttura dei
costi, ed è il motivo per cui in questo repository lo stato è versionato invece
che nascosto in un servizio.

## Da aprire sul telefono

| | Cosa fa |
|---|---|
| [Console dell'agenzia](https://mtornani.github.io/App1/agency/web/) | Crea missioni e leggi i risultati. Offline-first, si installa come app |
| [ScoutPad](https://mtornani.github.io/App1/scoutpad/) | Scouting dal vivo a bordo campo, senza rete |

Entrambe funzionano in aereo: niente CDN, niente build, niente dipendenze.

## I progetti

| Cartella | Cos'è | Stato |
|---|---|---|
| [`agency/`](./agency/README.md) | Sistema multi-agente. Tre topologie, sette ruoli, strumenti con confini nel codice. Gira su GitHub Actions senza server | Attivo, 113 test |
| [`vault/`](./vault/AGENTS.md) | La memoria. Wiki mantenuta dagli agenti, non da un umano, sul pattern LLM Wiki di Karpathy | Attivo |
| [`openscout/`](./openscout/README.md) | Piattaforma di scouting e match analysis open-data, con eligibility intelligence per qualsiasi federazione | Attivo |
| [`scoutpad/`](./scoutpad/README.md) | PWA mobile per lo scouting dal vivo | Attivo, online |
| `poa/` | Assistente operativo personale da riga di comando | Sperimentale |
| `backend/` + `frontend/` | Radar SMR: pipeline RAG per l'eleggibilità sammarinese. Il progetto da cui è nato OpenScout | Storico, generalizzato in OpenScout |
| `android/` | Watcher Android per la modalità focus | Sperimentale |

## Partire in due minuti

L'agenzia è solo standard library: niente `pip install`, niente lockfile.

```bash
python -m agency brief      # cosa c'è da fare adesso, letto dal vault
python -m agency roster     # chi lavora qui, e con quali strumenti
python -m agency new "Il tuo obiettivo" --run
python -m unittest agency.tests.test_agency
```

Senza chiavi API gira in dry-run deterministico, quindi puoi provare la
pipeline senza spendere un token. Il resto è in
[`agency/README.md`](./agency/README.md).

## Come è fatto

Tre scelte che spiegano quasi tutto il resto.

**Lo stato vive in git.** Missioni, risultati e wiki sono file versionati. Ogni
esecuzione lascia un diff, quindi l'audit è gratis e il sistema sopravvive a
mesi di disinteresse senza niente da tenere acceso.

**I confini stanno nel codice, non nei prompt.** Allowlist dei domini, blocco
degli indirizzi privati, scrittura confinata, sorgenti immutabili. Un prompt non
è un controllo di sicurezza: se l'unica cosa che ferma un agente è una frase
gentile nel system prompt, quel controllo non esiste.

**Le interfacce funzionano offline.** Si usano a bordo campo e in metropolitana.
Nessun CDN, nessuno strumento di build, apribili con un doppio clic.

## Licenza

MIT. Vedi [LICENSE](./LICENSE).
