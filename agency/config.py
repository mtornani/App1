"""Percorsi, default e lettura configurazione da ambiente.

Nessuna dipendenza esterna: tutto stdlib, cosi' gira identico su Termux,
su GitHub Actions e dentro un container minimale.
"""

from __future__ import annotations

import os
from pathlib import Path

# ---------- Percorsi ----------
PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(os.environ.get("AGENCY_REPO_ROOT", PACKAGE_DIR.parent))
AGENTS_DIR = PACKAGE_DIR / "agents"
# Gli artefatti delle missioni: e' qui che il lavoro diventa un file vero.
OUTPUT_DIR = Path(os.environ.get("AGENCY_OUTPUT_DIR", PACKAGE_DIR / "output"))
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
ZAI_API_KEY = os.environ.get("ZAI_API_KEY", "").strip()
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "").strip()
# DeepSeek ragiona di default a sforzo alto: per i turni brevi dell'agenzia
# conviene spegnerlo. Valori: disabled | low | high | max.
DEEPSEEK_THINKING = os.environ.get("AGENCY_DEEPSEEK_THINKING", "disabled").strip()
# GLM-5.3 ragiona sempre: "low" tiene i turni corti e il costo prevedibile.
ZAI_REASONING_EFFORT = os.environ.get("AGENCY_ZAI_REASONING", "low").strip()

# Default di modello per provider, sovrascrivibili con AGENCY_MODEL.
DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-5",
    "openrouter": "anthropic/claude-sonnet-5",
    "zai": "glm-5.3",
    "deepseek": "deepseek-flash",
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

# ---------- Strumenti degli agenti ----------
# Quante chiamate a tool puo' fare un agente in un singolo turno prima di
# dover concludere: evita che si incaponisca su una fonte che non risponde.
MAX_TOOL_CALLS = int(os.environ.get("AGENCY_MAX_TOOL_CALLS", "6"))

# fetch: solo questi domini, piu' quelli aggiunti via AGENCY_FETCH_ALLOWLIST.
# Default volutamente stretto su fonti aperte: una allowlist larga trasforma
# l'agente in un crawler che gira da solo in CI.
DEFAULT_FETCH_ALLOWLIST = (
    "wikipedia.org",
    "wikidata.org",
    "github.com",
    "raw.githubusercontent.com",
    "api.github.com",
    "api.football-data.org",
    "openfootball.github.io",
    "fifa.com",
    "uefa.com",
)
FETCH_TIMEOUT = int(os.environ.get("AGENCY_FETCH_TIMEOUT", "25"))
FETCH_MAX_BYTES = int(os.environ.get("AGENCY_FETCH_MAX_BYTES", "200000"))
FETCH_RETRY_WAIT = int(os.environ.get("AGENCY_FETCH_RETRY_WAIT", "4"))

# write_file / read_file
WRITE_MAX_BYTES = int(os.environ.get("AGENCY_WRITE_MAX_BYTES", "400000"))
READ_MAX_BYTES = int(os.environ.get("AGENCY_READ_MAX_BYTES", "80000"))
MAX_ARTIFACTS = int(os.environ.get("AGENCY_MAX_ARTIFACTS", "12"))
READABLE_SUFFIXES = {
    ".py", ".js", ".mjs", ".ts", ".tsx", ".json", ".md", ".txt",
    ".csv", ".html", ".css", ".yml", ".yaml", ".sql", ".toml",
}


def fetch_allowlist() -> set:
    """Domini consentiti a fetch: default piu' estensioni da ambiente."""

    extra = os.environ.get("AGENCY_FETCH_ALLOWLIST", "")
    domains = {d.strip().lower() for d in extra.split(",") if d.strip()}
    return set(DEFAULT_FETCH_ALLOWLIST) | domains


def model_for(provider: str) -> str:
    """Modello effettivo: override esplicito, altrimenti default del provider."""

    return MODEL or DEFAULT_MODELS.get(provider, DEFAULT_MODELS["echo"])


def ensure_dirs() -> None:
    """Crea le cartelle di stato se mancano (prima esecuzione, clone pulito)."""

    for directory in (STATE_DIR, MISSIONS_DIR, RUNS_DIR, OUTPUT_DIR):
        directory.mkdir(parents=True, exist_ok=True)
