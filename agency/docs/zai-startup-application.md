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

```
I build football intelligence tools: scouting, situational analysis and
national-team eligibility assessment from open data, as a low-cost alternative
to Wyscout and InStat for federations and clubs that cannot afford them.
Everything is open source: https://github.com/mtornani/App1

The product I want to scale with Z.ai is Agency, an autonomous multi-agent
system. A mission is a JSON file, the runtime is GitHub Actions, the console is
an offline-first PWA. Six specialised roles (planner, researcher, analyst,
engineer, writer, adversarial QA), each with real tools: sandboxed HTTP fetch
with a domain allowlist, file write confined to the mission folder, repository
read. 71 tests, zero runtime dependencies, boundaries enforced in code rather
than in prompts.

I integrated Z.ai before applying, not after. GLM-5.3 is already a first-class
provider in the codebase, alongside the others. Your OpenAI-compatible endpoint
made it a small change; the always-on reasoning and the empty-response case are
handled explicitly.

On consumption, honestly: my spend today is close to zero because I have been
testing against a deterministic offline provider. One mission run by a six-role
team with tool loops costs far more tokens than a single-agent call, and the
system is built to run unattended on a schedule. That is the workload where
GLM-5.3's 1M-token context and your pricing matter to me far more than they
would to a chat product.

Stage, stated plainly: solo founder, bootstrapped, no external funding,
pre-revenue. Luna Yu suggested this program in our email thread on 20 September.
What I need is model access to move from a tested system to a running one.
```

Conta circa 260 parole. Non allungarlo: ogni frase in più diluisce le due che
contano, cioè che hai integrato Z.ai prima di chiedere e che il tuo carico
consuma davvero token.

---

## Tre cose da fare prima di premere Submit

1. **Metti il link al commit dell'integrazione.** Se il branch è già su `main`,
   aggiungi in fondo all'Other Info una riga sola con l'URL del commit che
   aggiunge il provider Z.ai. È la sola affermazione dell'intera application che
   un revisore può verificare in dieci secondi.
2. **Fai girare una missione vera con GLM.** Ti serve una chiave di prova, anche
   a consumo. Se il protocollo regge, la frase "tested system" è vera. Se non
   regge, lo scopri prima che lo scopra loro.
3. **Decidi il nome e sostituiscilo ovunque**, form e testo.

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
