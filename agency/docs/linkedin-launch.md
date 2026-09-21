# Post di lancio — Agency

Testo pronto da incollare. LinkedIn non interpreta il markdown: qui sotto è già
tutto testo semplice con interruzioni di riga.

**Prima di pubblicare, leggi la sezione "Verità da rispettare" in fondo.**

---

## Immagini, in quest'ordine

1. `post-1-console-desktop.png` — la console, vista desktop
2. `post-4-terminale.png` — roster, 64 test verdi, gli strumenti che rifiutano ciò che devono rifiutare
3. `post-2-dettaglio-mobile.png` — dettaglio missione con i file prodotti, da telefono

LinkedIn mostra bene fino a 3 immagini in griglia. La prima è quella che ferma
lo scroll: tienila come copertina.

---

## Versione italiana

Ho smesso di chiedere a un solo agente AI di fare tutto.

Un modello da solo satura la context window, non mette mai in discussione le proprie allucinazioni, e con un prompt generalista perde contro ruoli specializzati. Così ho costruito un'agenzia: sei ruoli, ognuno con il suo mandato e i suoi strumenti.

Come funziona, in una riga: la missione è un file JSON, il runtime è GitHub Actions, la console è una PWA che si installa sul telefono.

Tre modi di far lavorare il team:

• Team — un Project Manager scompone la missione in 2-5 passi e gli specialisti eseguono in sequenza, ognuno vedendo il lavoro di chi lo precede.
• Swarm — nessun centro. Ogni agente chiude da solo o passa la palla a un altro.
• Solo — un agente, un turno. È il baseline con cui confronto gli altri due.

Il ruolo che cambia davvero i risultati non è il PM. È il Critic: un QA avversariale il cui unico compito è trovare dove il team ha sbagliato. Fatti inventati, conclusioni che non seguono dai dati, codice che non gira. Un modello solo non fa mai questo lavoro su se stesso.

Poi ho dato agli agenti strumenti veri, perché senza strumenti un'agenzia produce testo, non lavoro:

• fetch — scarica pagine e API pubbliche. Solo HTTPS, allowlist di domini, indirizzi privati bloccati, tetto sulla dimensione.
• write_file — salva il risultato come file, confinato nella cartella della missione.
• read_file — legge il repository prima di riscriverlo a memoria.

I confini stanno nel codice, non nel prompt. Un prompt non è un controllo di sicurezza: se l'unica cosa che impedisce a un agente di uscire dalla sua cartella è una frase gentile nel system prompt, quel controllo non esiste.

Cosa mi piace di questa architettura:

• Costo infrastrutturale zero. Nessun server, nessun deploy, nessun container da tenere vivo.
• Lo stato è versionato in git. Ogni esecuzione lascia un diff: l'agenzia è auditabile scorrendo la history.
• Zero dipendenze. Solo standard library Python e JavaScript nativo. Nessun lockfile da mantenere, gira identico su Termux e in CI.
• Il telefono può spegnersi. L'esecuzione è sempre della CI, mai del client.
• 64 test, senza rete e senza chiavi API. Due difetti li hanno trovati i test, non io: un percorso assoluto veniva riscritto in silenzio, e una riga di protocollo poteva finire nel deliverable.

Cosa non mi piace, e va detto:

• "Costo zero" è solo l'infrastruttura. Le chiamate al modello si pagano, e un team di sei ruoli consuma più token di un agente solo. Per un compito semplice, solo vince.
• Il protocollo degli strumenti è testuale, non tool-use nativa. Guadagno portabilità fra provider, perdo un po' di affidabilità.
• L'allowlist di fetch è volutamente stretta. Molte fonti che mi servirebbero restano fuori finché non le aggiungo a mano. È una scelta: un'allowlist larga trasforma l'agente in un crawler che gira da solo in CI.
• Il cron di GitHub Actions è best-effort. Non è uno scheduler real time.
• Il Critic riduce le allucinazioni. Non le elimina.
• Nessuna memoria fra una missione e l'altra. Ogni missione riparte da zero.

Codice, README e workflow:
https://github.com/mtornani/App1/tree/main/agency

Il resto del monorepo, fra cui ScoutPad che gira già online:
https://mtornani.github.io/App1/scoutpad/

Se lo provate e trovate dove si rompe, scrivetemelo. È esattamente il lavoro del Critic.

#AI #MultiAgent #Python #OpenSource #FootballAnalytics #Automation

---

## English version

I stopped asking a single AI agent to do everything.

One model on its own saturates the context window, never challenges its own hallucinations, and a generalist prompt always loses to specialised roles. So I built an agency: six roles, each with its own mandate and its own tools.

How it works, in one line: a mission is a JSON file, the runtime is GitHub Actions, the console is a PWA you install on your phone.

Three ways to run the team:

• Team — a Project Manager breaks the mission into 2-5 steps, specialists execute in sequence, each seeing the work that came before.
• Swarm — no centre. Each agent either finishes or hands off to another.
• Solo — one agent, one turn. The baseline I compare the other two against.

The role that actually changes the output isn't the PM. It's the Critic: an adversarial QA whose only job is to find where the team got it wrong. Invented facts, conclusions that don't follow from the data, code that doesn't run. A single model never does this to itself.

Then I gave the agents real tools, because without tools an agency produces text, not work:

• fetch — pulls public pages and APIs. HTTPS only, domain allowlist, private addresses blocked, hard size cap.
• write_file — saves the result as a file, confined to the mission's own folder.
• read_file — reads the repository instead of rewriting it from memory.

The boundaries live in the code, not in the prompt. A prompt is not a security control: if the only thing stopping an agent from escaping its folder is a polite sentence in the system prompt, that control doesn't exist.

What I like about this architecture:

• Zero infrastructure cost. No server, no deploy, no container to keep alive.
• State is versioned in git. Every run leaves a diff, so the agency is auditable by scrolling the history.
• Zero dependencies. Python standard library and vanilla JavaScript. No lockfile to maintain, identical on Termux and in CI.
• The phone can die. Execution always belongs to CI, never to the client.
• 64 tests, no network and no API keys. Two defects were found by the tests, not by me: an absolute path was silently rewritten, and a protocol line could leak into the deliverable.

What I don't like, and it should be said:

• "Zero cost" is infrastructure only. Model calls are paid, and a six-role team burns more tokens than a single agent. For a simple task, solo wins.
• The tool protocol is text-based, not native tool use. I gain portability across providers and lose some reliability.
• The fetch allowlist is deliberately narrow. Sources I'd want stay out until I add them by hand. That's the trade: a wide allowlist turns the agent into a crawler running unattended in CI.
• GitHub Actions cron is best-effort. It is not a real-time scheduler.
• The Critic reduces hallucinations. It does not remove them.
• No memory between missions. Every mission starts from zero.

Code, README and workflow:
https://github.com/mtornani/App1/tree/main/agency

The rest of the monorepo, including ScoutPad which is already live:
https://mtornani.github.io/App1/scoutpad/

If you try it and find where it breaks, tell me. That's exactly the Critic's job.

#AI #MultiAgent #Python #OpenSource #FootballAnalytics #Automation

---

## Verità da rispettare

Tre cose da sistemare prima di pubblicare, altrimenti il post dice cose non vere.

**1. Gli screenshot della console mostrano dati demo.**
Le missioni visibili (shortlist oriundi, pressing situazionale, digest settimanale)
sono inventate per far vedere l'interfaccia piena. Non sono output reali
dell'agenzia. Prima di pubblicare, lancia due o tre missioni vere e rifai gli
screenshot: un post tecnico regge solo se le immagini sono vere.

```bash
python -m agency new "La tua missione reale" --run
python -m agency index
```

L'immagine del terminale invece è output reale, catturato durante lo sviluppo:
il roster, i 64 test verdi e gli strumenti che rifiutano un dominio fuori
allowlist e un percorso con traversal.

**2. I link puntano a `main`, il codice è su un branch.**
Finché non fai il merge, entrambi i link `tree/main/agency` danno 404.
Merge del branch, oppure cambia i link in `tree/claude/brave-knuth-eyrzom/agency`.

**3. La console online esiste solo dopo il merge.**
`https://mtornani.github.io/App1/agency/web/` funziona quando il codice è su
`main`, perché Pages serve quel branch. Se vuoi mettere quel link nel post,
merge prima. Se preferisci non farlo ora, lascia il post senza quel link: gli
altri due funzionano già.
