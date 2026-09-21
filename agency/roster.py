"""Caricamento del roster: gli agenti sono dati, non codice.

Aggiungere un ruolo = aggiungere un file JSON in agency/agents/.
Nessuna modifica all'orchestratore, nessun deploy.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List

from . import config


@dataclass(frozen=True)
class Agent:
    """Un ruolo dell'agenzia, caricato da agency/agents/<id>.json."""

    id: str
    name: str
    title: str
    emoji: str
    system: str
    can_handoff: List[str]

    @property
    def label(self) -> str:
        return f"{self.emoji} {self.name}".strip()


def _parse(payload: Dict) -> Agent:
    return Agent(
        id=payload["id"],
        name=payload.get("name", payload["id"].title()),
        title=payload.get("title", ""),
        emoji=payload.get("emoji", ""),
        system=payload["system"],
        can_handoff=list(payload.get("can_handoff", [])),
    )


@lru_cache(maxsize=1)
def load_roster() -> Dict[str, Agent]:
    """Tutti gli agenti disponibili, indicizzati per id."""

    roster: Dict[str, Agent] = {}
    for path in sorted(config.AGENTS_DIR.glob("*.json")):
        with path.open("r", encoding="utf-8") as handle:
            agent = _parse(json.load(handle))
        roster[agent.id] = agent
    if not roster:
        raise RuntimeError(f"Roster vuoto: nessun agente in {config.AGENTS_DIR}")
    return roster


def get_agent(agent_id: str) -> Agent:
    roster = load_roster()
    if agent_id not in roster:
        available = ", ".join(sorted(roster))
        raise KeyError(f"Agente '{agent_id}' inesistente. Disponibili: {available}")
    return roster[agent_id]


def worker_ids() -> List[str]:
    """Agenti che eseguono lavoro (il PM coordina e basta)."""

    return [agent_id for agent_id in sorted(load_roster()) if agent_id != "pm"]
