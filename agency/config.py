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
# Il vault: la memoria che sopravvive alla singola missione.
# Punta qui il tuo vault Obsidian vero e l'agenzia ci lavora dentro.
VAULT_DIR = Path(os.environ.get("AGENCY_VAULT_DIR", REPO_ROOT / "vault"))
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
JINA_API_KEY = os.environ.get("JINA_API_KEY", "").strip()
TYPESAFE_API_KEY = os.environ.get("TYPESAFE_API_KEY", "").strip()
# Jev: decisioni tipizzate, non generazione. Serve a togliere il parsing di
# testo dai punti dove le alternative sono note in anticipo.
JEV_MODEL = os.environ.get("AGENCY_JEV_MODEL", "jev-latest").strip()
JEV_MIN_CONFIDENCE = float(os.environ.get("AGENCY_JEV_MIN_CONFIDENCE", "0.55"))
JEV_MAX_STATE = int(os.environ.get("AGENCY_JEV_MAX_STATE", "24000"))
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
# Ogni voce e' stata provata davvero. Non sono in elenco le fonti che
# rispondono con una pagina di verifica anti-bot: metterle significherebbe solo
# collezionare fallimenti. Il dettaglio sta in vault/wiki/entita-fonti-dati.md.
DEFAULT_FETCH_ALLOWLIST = (
    "wikipedia.org",
    "wikidata.org",
    "github.com",
    "raw.githubusercontent.com",
    "api.github.com",
    "api.football-data.org",
    "openfootball.github.io",
    "understat.com",
    "football-data.co.uk",
    "fifa.com",
    "uefa.com",
)

# Domini che vogliono un'intestazione di autenticazione. Chi e' qui dentro
# viene sempre scaricato in modo diretto: passando da Jina l'intestazione non
# arriverebbe al bersaglio, e la richiesta tornerebbe non autorizzata.
def auth_headers(hostname: str) -> dict:
    """Intestazioni di autenticazione per un dominio, se configurate."""

    host = (hostname or "").lower()
    chiave = os.environ.get("FOOTBALL_DATA_API_KEY", "").strip()
    if chiave and (host == "api.football-data.org" or host.endswith(".api.football-data.org")):
        return {"X-Auth-Token": chiave}
    return {}
FETCH_TIMEOUT = int(os.environ.get("AGENCY_FETCH_TIMEOUT", "25"))
FETCH_MAX_BYTES = int(os.environ.get("AGENCY_FETCH_MAX_BYTES", "200000"))
FETCH_RETRY_WAIT = int(os.environ.get("AGENCY_FETCH_RETRY_WAIT", "4"))

# Come si scarica una pagina: "auto" usa Jina Reader se c'e' la chiave,
# altrimenti va diretto. "jina" e "direct" forzano la scelta.
FETCH_VIA = os.environ.get("AGENCY_FETCH_VIA", "auto").strip().lower()
# Elementi da togliere prima della conversione. Sul README di un repo GitHub
# questa riga porta la pagina da 14.800 a 2.350 caratteri: sei volte meno
# token per la stessa informazione.
JINA_REMOVE_SELECTOR = os.environ.get(
    "AGENCY_JINA_REMOVE",
    "header, nav, footer, aside, .Header, .header, #comments, .cookie, .banner",
)

# write_file / read_file
WRITE_MAX_BYTES = int(os.environ.get("AGENCY_WRITE_MAX_BYTES", "400000"))
READ_MAX_BYTES = int(os.environ.get("AGENCY_READ_MAX_BYTES", "80000"))
MAX_ARTIFACTS = int(os.environ.get("AGENCY_MAX_ARTIFACTS", "12"))
VAULT_MAX_BYTES = int(os.environ.get("AGENCY_VAULT_MAX_BYTES", "120000"))
VAULT_MAX_LIST = int(os.environ.get("AGENCY_VAULT_MAX_LIST", "300"))
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
