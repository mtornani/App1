"""Decisioni tipizzate con Jev (TypeSafe System One).

Jev non genera testo: restituisce una decisione con le probabilita' calibrate,
in un passaggio solo e in decine o centinaia di millisecondi. Qui serve a una
cosa precisa: togliere il parsing di testo dai punti in cui l'agenzia deve
scegliere fra alternative note in anticipo.

Il punto piu' fragile era l'handoff dello swarm, dove un agente doveva scrivere
esattamente "HANDOFF: <id>" e bastava una virgola di troppo per far deragliare
la catena. Una Choice su un insieme chiuso non puo' sbagliare tipo.

Senza chiave questo modulo non fa nulla e l'agenzia resta sul protocollo
testuale: e' un miglioramento opzionale, non una dipendenza.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from . import config
from .providers import ProviderError, _post_json

ENDPOINT = "https://api.typesafe.ai/v1/systemone"


@dataclass
class Scelta:
    """Una decisione di Jev, con quanto e' sicuro di averla presa bene."""

    valore: str
    confidenza: float
    probabilita: Dict[str, float]

    @property
    def sicura(self) -> bool:
        """Sopra la soglia si agisce, sotto si ricade sul percorso normale.

        La calibrazione e' una proprieta' del gruppo di predizioni, non della
        singola risposta: la confidenza dice quando fidarsi, non che la
        risposta sia giusta.
        """

        return self.confidenza >= config.JEV_MIN_CONFIDENCE


def disponibile() -> bool:
    """Se Jev e' utilizzabile. Senza chiave si prosegue senza."""

    return bool(config.TYPESAFE_API_KEY)


def chiedi(state: str, questions: Dict[str, Dict[str, object]]) -> Dict[str, Dict]:
    """Una chiamata, piu' domande valutate in parallelo sullo stesso stato."""

    if not disponibile():
        raise ProviderError("TYPESAFE_API_KEY mancante.")
    dati = _post_json(
        ENDPOINT,
        {
            "content-type": "application/json",
            "authorization": f"Bearer {config.TYPESAFE_API_KEY}",
        },
        {"state": state[: config.JEV_MAX_STATE], "model": config.JEV_MODEL,
         "questions": questions},
        retries=2,
    )
    return dati.get("answers", {})


def scegli(state: str, istruzioni: str, criteri: Dict[str, str]) -> Optional[Scelta]:
    """Una Choice su un insieme chiuso. None se Jev non e' disponibile o fallisce.

    Restituire None invece di sollevare e' voluto: questa e' una scorciatoia,
    e una scorciatoia rotta deve far tornare sulla strada lunga, non fermare
    la missione.
    """

    if not disponibile() or len(criteri) < 2:
        return None
    try:
        risposte = chiedi(state, {
            "scelta": {"type": "choice", "instructions": istruzioni, "criteria": criteri}
        })
    except (ProviderError, KeyError, ValueError):
        return None

    risposta = risposte.get("scelta") or {}
    valore = risposta.get("choice")
    if valore not in criteri:
        return None
    return Scelta(
        valore=valore,
        confidenza=float(risposta.get("confidence", 0.0)),
        probabilita={k: float(v) for k, v in (risposta.get("probabilities") or {}).items()},
    )


def prossimo_agente(obiettivo: str, ultimo_output: str, agente: str,
                    consentiti: List[str], descrizioni: Dict[str, str]) -> Optional[Scelta]:
    """Chi tocca adesso nello swarm, oppure chiudere.

    Le opzioni sono gli agenti raggiungibili piu' "concludi": un insieme
    chiuso, che e' esattamente la forma che Jev sa trattare senza sbagliare.
    """

    criteri = {
        slug: descrizioni.get(slug, slug) for slug in consentiti
    }
    criteri["concludi"] = (
        "Il lavoro sull'obiettivo e' completo e non serve nessun altro ruolo."
    )
    state = (
        f"OBIETTIVO DELLA MISSIONE:\n{obiettivo}\n\n"
        f"ULTIMO TURNO, svolto da {agente}:\n{ultimo_output}"
    )
    return scegli(
        state,
        "Dato l'ultimo turno, quale ruolo deve lavorare adesso per avvicinare "
        "l'obiettivo? Scegli concludi solo se non resta niente di utile da fare.",
        criteri,
    )
