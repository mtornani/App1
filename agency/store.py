"""Persistenza su file JSON: missioni, run, indice per la PWA.

Niente database: lo stato e' fatto di file versionati in git. Ogni esecuzione
lascia una traccia leggibile e diffabile, quindi l'agenzia e' auditabile
scorrendo la history del repo.
"""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import config


def utc_now() -> str:
    """Timestamp ISO-8601 UTC al millisecondo.

    La precisione al secondo non basta: due missioni create nello stesso
    secondo diventerebbero indistinguibili e la coda perderebbe l'ordine FIFO.
    """

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def slugify(text: str, max_len: int = 32) -> str:
    """Slug ASCII sicuro per nomi file (accenti italiani inclusi)."""

    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    return (slug[:max_len].strip("-")) or "mission"


def new_mission_id(objective: str) -> str:
    """Id ordinabile cronologicamente, riconoscibile a occhio e senza collisioni.

    Se nello stesso secondo arriva un id identico (stesso obiettivo inviato due
    volte dal telefono), si aggiunge un suffisso invece di sovrascrivere.
    """

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    base = f"m-{stamp}-{slugify(objective, 24)}"
    candidate, suffix = base, 2
    while (config.MISSIONS_DIR / f"{candidate}.json").exists():
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    """Scrittura atomica: file temporaneo + replace, cosi' un'interruzione
    non lascia mai un JSON troncato che romperebbe la PWA."""

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    tmp.replace(path)


# ---------------------------------------------------------------- missioni


def create_mission(
    objective: str,
    topology: str = "team",
    agents: Optional[List[str]] = None,
    context: str = "",
    source: str = "cli",
) -> Dict[str, Any]:
    """Registra una nuova missione in stato `pending`."""

    config.ensure_dirs()
    mission = {
        "id": new_mission_id(objective),
        "objective": objective.strip(),
        "topology": topology,
        "agents": agents or [],
        "context": context.strip(),
        "status": "pending",
        "source": source,
        "created_at": utc_now(),
        "started_at": None,
        "finished_at": None,
        "deliverable": None,
        "artifacts": [],
        "vault_pages": [],
        "error": None,
    }
    _write_json(config.MISSIONS_DIR / f"{mission['id']}.json", mission)
    return mission


def load_mission(mission_id: str) -> Dict[str, Any]:
    path = config.MISSIONS_DIR / f"{mission_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Missione sconosciuta: {mission_id}")
    return _read_json(path)


def save_mission(mission: Dict[str, Any]) -> None:
    _write_json(config.MISSIONS_DIR / f"{mission['id']}.json", mission)


def list_missions(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Missioni ordinate dalla piu' recente, opzionalmente filtrate."""

    config.ensure_dirs()
    missions: List[Dict[str, Any]] = []
    for path in sorted(config.MISSIONS_DIR.glob("m-*.json")):
        try:
            mission = _read_json(path)
        except (json.JSONDecodeError, OSError):
            # Un file corrotto (push a meta') non deve bloccare l'intero giro.
            continue
        if status is None or mission.get("status") == status:
            missions.append(mission)
    missions.sort(key=lambda item: (item.get("created_at", ""), item.get("id", "")), reverse=True)
    return missions


def pending_missions(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Coda da lavorare: le piu' vecchie per prime (FIFO, niente starvation)."""

    queue = list(reversed(list_missions("pending")))
    return queue[:limit] if limit else queue


# --------------------------------------------------------------------- run


def save_run(mission_id: str, run: Dict[str, Any]) -> Path:
    """Salva il transcript completo (ogni turno di ogni agente)."""

    path = config.RUNS_DIR / f"{mission_id}.json"
    _write_json(path, run)
    return path


def load_run(mission_id: str) -> Optional[Dict[str, Any]]:
    path = config.RUNS_DIR / f"{mission_id}.json"
    return _read_json(path) if path.exists() else None


# ------------------------------------------------------------------ indice


def rebuild_index() -> Dict[str, Any]:
    """Genera il feed unico che la PWA scarica: una richiesta, tutto lo stato."""

    missions = list_missions()
    index = {
        "generated_at": utc_now(),
        "counts": {
            status: sum(1 for m in missions if m.get("status") == status)
            for status in config.STATUSES
        },
        "missions": [
            {
                "id": m["id"],
                "objective": m["objective"],
                "topology": m.get("topology", "team"),
                "status": m.get("status", "pending"),
                "created_at": m.get("created_at"),
                "finished_at": m.get("finished_at"),
                "source": m.get("source", "cli"),
                "error": m.get("error"),
                # Anteprima: la PWA mostra il testo senza aprire il run completo.
                "deliverable": m.get("deliverable"),
                # I file prodotti: e' la parte che si apre dal telefono.
                "artifacts": m.get("artifacts", []),
                "vault_pages": m.get("vault_pages", []),
            }
            for m in missions[:100]
        ],
    }
    _write_json(config.INDEX_FILE, index)
    return index
