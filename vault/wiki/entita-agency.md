---
type: entity
title: Agency
updated: 2026-09-21
sources: [raw/sessione-2026-09-21.md]
status: attiva
---

# Agency

Sistema multi-agente costruito il 2026-09-21 dentro il monorepo App1. Sei ruoli, tre
topologie, strumenti reali, stato versionato in git.

## Cosa fa oggi

- Esegue missioni descritte come file JSON, con tre topologie: `solo`, `team`, `swarm`.
- Gli agenti hanno strumenti veri: `fetch` con allowlist, scrittura file, lettura
  del repository, e ora lettura e scrittura del vault.
- Il runtime non presidiato e' GitHub Actions: cron ogni 30 minuti, piu' push e
  dispatch manuale.
- La console e' una PWA offline-first che si installa sul telefono.

## Cosa non fa

- Non ha ancora girato con un modello vero. Vedi [[thread-primo-giro-reale]].
- Non ha un'interfaccia locale immediata: oggi il percorso non presidiato passa
  dalla CI, che per un assistente continuo e' la forma sbagliata.
  Vedi [[decisione-runtime-in-ci]].

## Numeri

| Voce | Valore |
|---|---|
| Ruoli | 7 con l'archivista |
| Test | 88, senza rete e senza chiavi |
| Dipendenze a runtime | nessuna, solo standard library |

Collegate: [[decisione-stato-in-git]], [[decisione-confini-nel-codice]],
[[decisione-protocollo-testuale]], [[entita-provider-llm]].
