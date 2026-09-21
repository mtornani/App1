# Post di lancio — Agency

Versione Morrison. Testo pronto da incollare: LinkedIn non interpreta il
markdown, qui sotto è già tutto testo semplice.

**Leggi "Cosa resta da fare" in fondo prima di pubblicare.**

---

## Perché l'aggancio funziona

La citazione è del 1969, intervista di Jerry Hopkins per Rolling Stone. È
verificabile e arcinota fra i musicisti, quindi non sembra una trovata.

Regge per tre motivi.

1. **La previsione si è avverata davvero**, e in un modo che nel 1969 sembrava
   assurdo. Non stai forzando un'analogia, stai citando un fatto.
2. **Ti dà il posizionamento senza rivendicare un primato.** "Una persona e un
   team di agenti" è verificabile. "Prima startup italiana" no, e invitava la
   domanda su clienti e fatturato.
3. **Il rovescio della previsione è il tuo argomento migliore.** Il sintetizzatore
   in camera ha prodotto anche un oceano di musica mediocre. È lo stesso
   fenomeno degli agenti, e dirlo ti separa da chiunque altro stia scrivendo di
   multi-agente questa settimana.

La regola per non scadere nella fuffa: **la metafora entra una volta all'inizio
e una volta alla fine, mai in mezzo.** Nel mezzo ci vanno solo numeri e difetti.
Il testo qui sotto rispetta questa regola.

---

## Immagini, in quest'ordine

1. `post-1-console-desktop.png` — la console, vista desktop
2. `post-4-terminale.png` — roster, test verdi, gli strumenti che rifiutano ciò che devono rifiutare
3. `post-2-dettaglio-mobile.png` — dettaglio missione con i file prodotti

---

## Versione italiana

```
Nel 1969 Jim Morrison, a cui nessuno chiedeva previsioni tecnologiche, disse questa cosa:

"Mi immagino una persona sola con un mucchio di macchine, nastri e apparecchiature elettroniche, che canta o parla usando le macchine."

Aveva ragione, e non come metafora. Quarant'anni dopo, il disco che ascolti in cuffia lo ha fatto un ragazzo in camera sua con un portatile.

Sta succedendo la stessa identica cosa alle aziende, e ho deciso di provarci.

Tornani Sport Tech è una persona e un team di agenti. Non è uno slogan, è la struttura dei costi. La capacità di consegna viene da Agency, un sistema multi-agente che ho costruito e che è tutto pubblico.

Come funziona: una missione è un file JSON, il runtime è GitHub Actions, la console è una web app che si installa sul telefono e funziona offline. Sette ruoli specializzati, dal pianificatore al QA avversariale all'archivista. Strumenti veri: scaricare pagine dietro una allowlist di domini, scrivere file, leggere il repository, mantenere una wiki che sopravvive fra una missione e l'altra.

113 test. Zero dipendenze a runtime. I confini degli agenti applicati nel codice e non nei prompt, perché un prompt non è un controllo di sicurezza: se l'unica cosa che impedisce a un agente di uscire dalla sua cartella è una frase gentile nel system prompt, quel controllo non esiste.

Ma la cosa che ho imparato costruendolo è un'altra, ed è la ragione per cui scrivo questo post.

La previsione di Morrison si è avverata anche nella parte che nessuno cita. Il sintetizzatore in camera da letto ha prodotto una quantità industriale di musica mediocre. Rendere gratuita la produzione non ha reso nessuno bravo: ha solo spostato la scarsità dalla produzione al gusto.

Con gli agenti succede lo stesso, e l'ho visto su di me. Il collo di bottiglia non è mai stato produrre. Con un team di agenti produco più di quanto riesca a verificare, e la verifica non scala aggiungendo agenti: peggiora. Dieci agenti fanno dieci volte il lavoro e tu resti la coda.

Da cui l'unica scelta di progetto che conta davvero: ogni cosa che un agente produce deve essere verificabile in trenta secondi. Ogni affermazione porta la sua fonte. I dati che mancano si dichiarano invece di riempirli. Un ruolo intero esiste solo per contestare gli altri, perché un modello da solo non mette mai in discussione le proprie allucinazioni.

Quello che non funziona, e va detto:

• "Costo zero" vale solo per l'infrastruttura. I modelli si pagano, e un team di sette ruoli brucia molti più token di un agente solo. Per un compito semplice, un agente solo vince.
• Un cron da trenta minuti che scrive su git non è un assistente continuo. L'ho marcato come decisione da rivedere invece di far finta di niente.
• Il QA avversariale riduce le allucinazioni. Non le elimina.
• Due difetti li hanno trovati i test e non io: un percorso assoluto riscritto in silenzio, e una riga di protocollo finita dentro il risultato.

La console, da aprire anche dal telefono:
https://mtornani.github.io/App1/agency/web/

Codice, README e workflow:
https://github.com/mtornani/App1/tree/main/agency

C'è qualcuno là fuori, in uno scantinato, che sta inventando una forma completamente nuova. Lo diceva sempre Morrison, nella stessa intervista.

#AI #MultiAgent #Python #OpenSource #FootballAnalytics
```

536 parole. È lungo per LinkedIn ma il pubblico tecnico regge, e la struttura
alterna un'idea a un fatto.

---

## English version

```
In 1969, Jim Morrison, whom nobody was asking for technology predictions, said this:

"I can kind of envision maybe one person with a lot of machines, tapes and electronic setups, singing or speaking and using machines."

He was right, and not as a metaphor. Forty years later, the record in your headphones was made by one kid in a bedroom with a laptop.

The same thing is now happening to companies, and I decided to try it.

Tornani Sport Tech is one person and an agent team. That is not a slogan, it is the cost structure. Delivery capacity comes from Agency, a multi-agent system I built, and all of it is public.

How it works: a mission is a JSON file, the runtime is GitHub Actions, the console is a web app you install on your phone and that works offline. Seven specialised roles, from planner to adversarial QA to librarian. Real tools: fetching pages behind a domain allowlist, writing files, reading the repository, maintaining a knowledge vault that survives between missions.

113 tests. Zero runtime dependencies. Agent boundaries enforced in code, not in prompts, because a prompt is not a security control: if the only thing stopping an agent from escaping its folder is a polite sentence in the system prompt, that control does not exist.

But the thing I learned building it is something else, and it is why I am writing this.

Morrison's prediction also came true in the part nobody quotes. The bedroom synthesiser produced an industrial quantity of mediocre music. Making production free made nobody good at it: it just moved scarcity from production to taste.

The same is happening with agents, and I watched it happen to me. Production was never the bottleneck. With an agent team I produce more than I can verify, and verification does not scale by adding agents: it gets worse. Ten agents do ten times the work and you are still the queue.

Hence the only design choice that actually matters: everything an agent produces has to be verifiable in thirty seconds. Every claim carries its source. Missing data is declared instead of filled in. An entire role exists only to attack the others, because a single model never challenges its own hallucinations.

What does not work, and should be said:

• "Zero cost" is infrastructure only. Models are paid, and a seven-role team burns far more tokens than a single agent. For a simple task, a single agent wins.
• A thirty-minute cron writing to git is not a continuous assistant. I marked that decision as needing review rather than pretending otherwise.
• Adversarial QA reduces hallucinations. It does not remove them.
• Two defects were found by the tests, not by me: an absolute path silently rewritten, and a protocol line that leaked into the output.

The console, open it on your phone too:
https://mtornani.github.io/App1/agency/web/

Code, README and workflow:
https://github.com/mtornani/App1/tree/main/agency

There is somebody out there, working in a basement, inventing a whole new form. Morrison said that too, in the same interview.

#AI #MultiAgent #Python #OpenSource #FootballAnalytics
```

---

## Cosa resta da fare

**1. La console adesso è online davvero.** Il link nel testo funziona, l'ho
verificato dopo il merge su `main`. Questo era uno dei tre blocchi ed è caduto.

**2. Gli screenshot mostrano ancora dati demo.** Le missioni visibili sono
inventate per riempire l'interfaccia. Lancia due o tre missioni vere con la
chiave DeepSeek e rifai le immagini. Un post che apre con l'onestà come tema non
può avere screenshot finti.

```bash
python -m agency new "La tua missione reale" --run
```

**3. I numeri nel testo sono quelli veri di oggi**: 113 test, sette ruoli. Se
passa una settimana prima di pubblicare, ricontrollali con
`python -m unittest agency.tests.test_agency`.

## Fonti per la citazione

- [Open Culture](https://www.openculture.com/2022/04/jim-morrison-accurately-predicts-the-future-of-electronic-music-in-1969.html)
- [Rolling Stone](https://www.rollingstone.com/music/music-news/how-jim-morrison-predicted-edm-to-rolling-stone-in-1969-235437/)
- [Synthtopia](https://www.synthtopia.com/content/2014/10/09/jim-morrison-predicts-the-future-of-music/)
