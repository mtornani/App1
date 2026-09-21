# Z.ai Startup Program — application

Compilata a partire dal form su startup.z.ai e dall'email di Luna Yu del
20 settembre 2026, che ti ha indirizzato qui dal Sovereign Partner Program.

---

## Campi del form

| Campo | Cosa scrivere | Nota |
|---|---|---|
| Z.ai Email | `mirkotornani@gmail.com` | già auto-compilato |
| Company Name | `Tornani Sport Tech` | deciso |
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

`Tornani Sport Tech` è il contenitore, `OpenScout` resta il prodotto. La
distinzione conta nel form: loro finanziano una società, non un repository.

### Su "Daily LLM spend"

Rispondere zero sembra debole, ma mentire è peggio: Luna ha già il tuo thread
con dentro il tuo stadio reale, e una cifra gonfiata qui la contraddice. Il
testo dell'Other Info gira il problema spiegando la *forma* del consumo invece
della cifra di oggi, che è l'argomento vero.

---

## Other Info — testo da incollare

Versione definitiva. Nome società inserito, e il baricentro spostato:
il football resta il dominio, ma il soggetto della pitch è la società a una
persona più un team di agenti.

```
Tornani Sport Tech builds football intelligence from open data: scouting,
situational analysis and national-team eligibility, as a low-cost alternative to
Wyscout and InStat for federations and clubs that cannot afford them.
Everything is open source: https://github.com/mtornani/App1

The company is one person and an agent team. That is not a slogan, it is the
cost structure, and it is why I am writing to you. Delivery capacity comes from
Agency, an autonomous multi-agent system I built: a mission is a JSON file, the
runtime is GitHub Actions, the console is an offline-first PWA. Seven
specialised roles (planner, researcher, analyst, engineer, writer, adversarial
QA, librarian), each with real tools: sandboxed HTTP fetch behind a domain
allowlist, file writes confined to the mission folder, repository read, and
read/write access to a knowledge vault that persists between missions. 88 tests,
zero runtime dependencies, boundaries enforced in code rather than in prompts.

I integrated Z.ai before applying, not after. GLM-5.3 is a first-class provider
in the codebase, alongside the others:
https://github.com/mtornani/App1/commit/1107961e833316634ec751ea7afe7f714d4e47c8
Your OpenAI-compatible endpoint made it a small change; the always-on reasoning
and the empty-response case are handled explicitly.

On consumption, honestly: my spend today is close to zero because I have been
testing against a deterministic offline provider. Two things change that. One
mission run by a seven-role team with tool loops costs far more tokens than a
single-agent call. And the vault is re-read and re-linked by an unattended job
on a schedule, so consumption is continuous rather than per-request. When
headcount stays at one, every unit of growth is tokens. That is the workload
where GLM-5.3's 1M-token context and your pricing matter to me far more than
they would to a chat product.

Stage, stated plainly: solo founder, bootstrapped, no external funding,
pre-revenue. Luna Yu suggested this program in our email thread on 20 September.
What I need is model access to move from a tested system to a running one.
```

319 parole. La frase che porta più peso di tutte è una:
**"When headcount stays at one, every unit of growth is tokens."**
È vera, è verificabile, e dice a un fornitore di modelli esattamente quello che
vuole sapere. Se devi tagliare qualcosa, non tagliare quella.

## Cosa resta prima di premere Submit

1. ~~Metti il link al commit dell'integrazione.~~ **Fatto.** Il commit è già
   pushato e pubblico, quindi il link funziona senza aspettare il merge:
   `https://github.com/mtornani/App1/commit/1107961e833316634ec751ea7afe7f714d4e47c8`
2. ~~Decidi il nome della società.~~ **Fatto:** `Tornani Sport Tech`.
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
