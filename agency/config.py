"""Percorsi, default e lettura configurazione da ambiente.

Nessuna dipendenza esterna: tutto stdlib, cosi' gira identico su Termux,
su GitHub Actions e dentro un container minimale.
"""

from __future__ import annotations

import os
from pathlib import Path

# ---------- Percorsi ----------
PACKAGE_DIR = Path(__file__).resolve().parent
AGENTS_DIR = PACKAGE_DIR / "agents"
STATE_DIR = Path(os.environ.get("AGENCY_STATE_DIR", PACKAGE_DIR / "state"))
MISSIONS_DIR = STATE_DIR / "missions"
RUNS_DIR = STATE_DIR / "runs"
INDEX_FILE = STATE_DIR / "index.json"

# ---------- Provider LLM ----------
# "anthropic" | "openrouter" | "echo" (offline, deterministico: test e dry-run)
PROVIDER = os.environ.get("AGENCY_PROVIDER", "echo").strip().lower()
MODEL = os.environ.get("AGENCY_MODEL", "").strip()
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "").strip()

# Default di modello per provider, sovrascrivibili con AGENCY_MODEL.
DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-5",
    "openrouter": "anthropic/claude-sonnet-4.5",
    "echo": "echo-local",
}

# ---------- Limiti di sicurezza ----------
# Tetto duro sui passi di una missione: impedisce che uno swarm giri all'infinito
# bruciando token mentre nessuno guarda.
MAX_STEPS = int(os.environ.get("AGENCY_MAX_STEPS", "12"))
MAX_TOKENS_PER_CALL = int(os.environ.get("AGENCY_MAX_TOKENS", "2000"))
HTTP_TIMEOUT = int(os.environ.get("AGENCY_HTTP_TIMEOUT", "120"))

# Quante missioni al massimo esegue un singolo giro automatico.
MAX_MISSIONS_PER_RUN = int(os.environ.get("AGENCY_MAX_MISSIONS", "3"))

STATUSES = ("pending", "running", "done", "failed")


def model_for(provider: str) -> str:
    """Modello effettivo: override esplicito, altrimenti default del provider."""

    return MODEL or DEFAULT_MODELS.get(provider, DEFAULT_MODELS["echo"])


def ensure_dirs() -> None:
    """Crea le cartelle di stato se mancano (prima esecuzione, clone pulito)."""

    for directory in (STATE_DIR, MISSIONS_DIR, RUNS_DIR):
        directory.mkdir(parents=True, exist_ok=True)
