# Z.ai Startup Program — application

Compilata a partire dal form su startup.z.ai e dall'email di Luna Yu del
20 settembre 2026, che ti ha indirizzato qui dal Sovereign Partner Program.

---

## Campi del form

| Campo | Cosa scrivere | Nota |
|---|---|---|
| Z.ai Email | `mirkotornani@gmail.com` | già auto-compilato |
| Company Name | `OpenScout` | **decisione tua**, vedi sotto |
| First Name | `Mirko` | |
| Last Name | `Tornani` | |
| Job Title | `Founder` | non "CEO": con un dipendente umano suona gonfiato |
| Phone Number | il tuo | opzionale, ma un contatto diretto aiuta la review |
| Company Size | `1` (o la fascia più bassa disponibile) | |
| Country | `Italy` | cambia in San Marino se la tua base è lì |
| Latest round of funding | `Bootstrapped` / `None` / `Pre-seed` | la voce più bassa che offre il menu |
| Company Website | `https://github.com/mtornani/App1` | il campo è opzionale, il repo è più verificabile di una landing |
| Daily LLM spend | il numero vero, oggi vicino a `0` | il testo sotto spiega perché, non mentire qui |

### Sul nome

`OpenScout` è il nome che ricorre di più nel repo ed è il prodotto, non il
contenitore. Se hai già un'entità registrata o un brand che usi altrove, usa
quello e sostituiscilo anche nel testo qui sotto.

### Su "Daily LLM spend"

Rispondere zero sembra debole, ma mentire è peggio: Luna ha già il tuo thread
con dentro il tuo stadio reale, e una cifra gonfiata qui la contraddice. Il
testo dell'Other Info gira il problema spiegando la *forma* del consumo invece
della cifra di oggi, che è l'argomento vero.

---

## Other Info — testo da incollare

Aggiornato il 2026-09-21 dopo il vault e il provider DeepSeek. La versione
precedente diceva 6 ruoli e 71 test: erano veri quando l'ho scritta, non lo sono
più. **Usa questa.**

```
I build football intelligence tools: scouting, situational analysis and
national-team eligibility assessment from open data, as a low-cost alternative
to Wyscout and InStat for federations and clubs that cannot afford them.
Everything is open source: https://github.com/mtornani/App1

The product I want to scale with Z.ai is Agency, an autonomous multi-agent
system. A mission is a JSON file, the runtime is GitHub Actions, the console is
an offline-first PWA. Seven specialised roles (planner, researcher, analyst,
engineer, writer, adversarial QA, librarian), each with real tools: sandboxed
HTTP fetch behind a domain allowlist, file writes confined to the mission
folder, repository read, and read/write access to a persistent knowledge vault.
88 tests, zero runtime dependencies, boundaries enforced in code rather than in
prompts.

I integrated Z.ai before applying, not after. GLM-5.3 is a first-class provider
in the codebase, alongside the others:
https://github.com/mtornani/App1/commit/1107961e833316634ec751ea7afe7f714d4e47c8
Your OpenAI-compatible endpoint made it a small change; the always-on reasoning
and the empty-response case are handled explicitly.

On consumption, honestly: my spend today is close to zero because I have been
testing against a deterministic offline provider. Two things change that. One
mission run by a seven-role team with tool loops costs far more tokens than a
single-agent call. And the knowledge vault is maintained by an unattended job
that re-reads and re-links the whole knowledge base on a schedule, so
consumption is continuous rather than per-request. That is the workload where
GLM-5.3's 1M-token context and your pricing matter to me far more than they
would to a chat product.

Stage, stated plainly: solo founder, bootstrapped, no external funding,
pre-revenue. Luna Yu suggested this program in our email thread on 20 September.
What I need is model access to move from a tested system to a running one.
```

287 parole. Non allungarlo: ogni frase in più diluisce le tre che contano.

1. Hai integrato Z.ai **prima** di chiedere, e il link al commit lo dimostra in
   dieci secondi.
2. Il tuo carico consuma token sul serio, e adesso puoi dire perché: non è solo
   il team a sette ruoli, è il vault che viene rimantenuto a ciclo. Il consumo è
   continuo, non a richiesta. È l'argomento che un fornitore di modelli capisce.
3. Dichiari lo stadio senza giri di parole, e combacia con quello che Luna ha
   già nel thread.

### Cosa è cambiato rispetto alla prima versione

| Prima | Adesso | Perché |
|---|---|---|
| Six specialised roles | Seven | È arrivato il `librarian`, l'archivista del vault |
| 71 tests | 88 | Vault, DeepSeek e i loro confini |
| tre strumenti elencati | quattro, col vault | La memoria persistente è il pezzo che mancava |
| nessun link al commit | link diretto | Il commit è già pubblico, non serve il merge |
| consumo solo per missione | consumo anche continuo | Il lint del vault gira a ciclo |

## Tre cose da fare prima di premere Submit

1. ~~Metti il link al commit dell'integrazione.~~ **Fatto.** Il commit è già
   pushato e pubblico, quindi il link funziona senza aspettare il merge:
   `https://github.com/mtornani/App1/commit/1107961e833316634ec751ea7afe7f714d4e47c8`
2. **Decidi il nome della società e sostituiscilo ovunque**, nel form e nel
   testo. È l'unica cosa che blocca l'invio.
3. **Fai girare una missione vera.** Hai 50 dollari di credito DeepSeek: basta
   una missione per rendere incontestabile la frase "tested system". Non è
   strettamente necessaria per inviare, ma se un revisore chiede "l'hai usata?"
   la risposta cambia.

---

## Sulla frase "prima startup italiana con dipendenti AI"

Come narrativa è ottima e la userei. Come affermazione dentro un form, no.

"Prima" è una rivendicazione di primato che nessuno può verificare e che un
revisore tecnico legge come rumore. In più ti espone alla domanda peggiore
possibile: quanti clienti, quanto fatturato, quanti agenti in produzione.

La stessa idea, detta in modo che regge: *una società di una persona, dove la
capacità di consegna è un team di agenti, e il codice è pubblico.* Questo lo
puoi dimostrare oggi. Il primato tienilo per il post LinkedIn, dove è retorica e
non una dichiarazione a un valutatore.
