"""Strumenti degli agenti: fetch, scrittura e lettura file.

Principio di progetto: un tool non e' una comodita' per l'agente, e' il modo in
cui una missione finisce in un artefatto vero. Senza tool l'agenzia produce
testo in chat; con i tool produce file versionati nel repo, che restano li'
anche quando nessuno se li ricorda.

Protocollo testuale invece della tool-use nativa: funziona identico su
Anthropic, su OpenRouter e con il provider offline, quindi il motore resta uno
solo e i test girano senza rete.

Confini, applicati qui e non nel prompt (un prompt non e' un controllo di
sicurezza):
  - fetch      -> solo HTTPS, solo domini in allowlist, mai indirizzi privati,
                  tetto su dimensione e tempo;
  - write_file -> solo dentro agency/output/<mission_id>/, niente traversal;
  - read_file  -> solo dentro il repo, niente .git ne' file di segreti.
"""

from __future__ import annotations

import ipaddress
import json
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from . import config

# Il modello chiede un tool con due righe: nome e argomenti JSON.
TOOL_CALL_RE = re.compile(
    r"^[ \t]*TOOL[ \t]*:[ \t]*([a-z_]+)[ \t]*\r?\n[ \t]*(\{.*?\})[ \t]*$",
    re.MULTILINE | re.DOTALL,
)


class ToolError(RuntimeError):
    """Errore d'uso di un tool: torna all'agente come messaggio, non esplode."""


@dataclass
class ToolResult:
    """Esito di una chiamata, sia per l'agente sia per il transcript."""

    tool: str
    args: Dict[str, object]
    ok: bool
    output: str
    detail: str = ""

    def as_message(self) -> str:
        head = f"RISULTATO TOOL {self.tool} ({'ok' if self.ok else 'errore'})"
        return f"{head}\n{self.output}"


# --------------------------------------------------------------- fetch

class _TextExtractor(HTMLParser):
    """HTML -> testo leggibile, senza dipendenze.

    Non e' un parser completo e non deve esserlo: serve a dare al modello il
    contenuto senza bruciare meta' della context window in markup.
    """

    SKIP = {"script", "style", "noscript", "svg", "head", "nav", "footer"}
    BREAK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "section"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: List[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in self.SKIP:
            self._skip_depth += 1
        elif tag in self.BREAK:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP and self._skip_depth:
            self._skip_depth -= 1
        elif tag in self.BREAK:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth and data.strip():
            self.parts.append(data.strip())

    def text(self) -> str:
        joined = " ".join(self.parts)
        joined = re.sub(r"[ \t]+", " ", joined)
        return re.sub(r"(\s*\n\s*)+", "\n", joined).strip()


def _host_is_public(hostname: str) -> bool:
    """Blocca localhost e reti private: in CI il runner vede servizi interni.

    E' la difesa contro una SSRF indotta da una pagina che dice all'agente di
    chiamare un indirizzo interno.
    """

    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return False
    for info in infos:
        address = ipaddress.ip_address(info[4][0])
        if (address.is_private or address.is_loopback or address.is_link_local
                or address.is_reserved or address.is_multicast):
            return False
    return True


def _domain_allowed(hostname: str) -> bool:
    """Allowlist per dominio, con i sottodomini inclusi."""

    host = hostname.lower()
    return any(host == d or host.endswith("." + d) for d in config.fetch_allowlist())


WIKI_ARTICLE_RE = re.compile(r"^(https://([a-z-]+)\.wikipedia\.org)/wiki/([^?#]+)")
JINA_READER = "https://r.jina.ai/"


def _usa_jina() -> bool:
    """Se passare da Jina Reader invece di scaricare direttamente.

    Jina scarica dalla propria infrastruttura, quindi arriva dove il fetch
    diretto viene bloccato per reputazione dell'IP, gestisce i PDF e le pagine
    renderizzate in JavaScript, e restituisce markdown con i link intatti.
    Senza chiave esiste un piano gratuito, ma di default non ci si appoggia:
    mandare l'URL a un terzo e' una scelta, non un dettaglio.
    """

    if config.FETCH_VIA == "jina":
        return True
    if config.FETCH_VIA == "direct":
        return False
    return bool(config.JINA_API_KEY)


def _wikipedia_plaintext(url: str) -> Optional[str]:
    """Riscrive un articolo Wikipedia nella sua API di estrazione testo.

    La pagina HTML di Wikipedia e' meta' menu di navigazione e lista lingue:
    passarla cosi' al modello brucia contesto senza aggiungere informazione.
    L'API restituisce lo stesso articolo in testo piano.
    """

    match = WIKI_ARTICLE_RE.match(url)
    if not match:
        return None
    base, _lang, title = match.groups()
    query = urllib.parse.urlencode({
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "explaintext": "1",
        "redirects": "1",
        "titles": urllib.parse.unquote(title).replace("_", " "),
    })
    return f"{base}/w/api.php?{query}"


def _unwrap_wikipedia(body: str) -> Optional[str]:
    """Estrae il testo dell'articolo dalla risposta dell'API."""

    try:
        pages = json.loads(body)["query"]["pages"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return None
    extracts = [page.get("extract", "") for page in pages.values() if page.get("extract")]
    return "\n\n".join(extracts) if extracts else None


def tool_fetch(args: Dict[str, object], _ctx: "ToolContext") -> str:
    """Scarica una pagina e restituisce il testo. Argomenti: {"url": "https://..."}"""

    url = str(args.get("url", "")).strip()
    if not url:
        raise ToolError("Manca 'url'.")

    # L'URL citato all'agente resta quello dell'articolo, non quello dell'API:
    # la fonte da mettere nel report e' la pagina leggibile da un umano.
    source_url, wiki = url, _wikipedia_plaintext(url)
    if wiki:
        url = wiki

    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https":
        raise ToolError("Solo URL https.")
    if not parsed.hostname:
        raise ToolError("URL senza host.")
    if not _domain_allowed(parsed.hostname):
        raise ToolError(
            f"Dominio '{parsed.hostname}' non in allowlist. "
            f"Consentiti: {', '.join(sorted(config.fetch_allowlist()))}. "
            "Si estende con la variabile AGENCY_FETCH_ALLOWLIST."
        )
    if not _host_is_public(parsed.hostname):
        raise ToolError("Host non risolvibile o su rete privata.")

    # L'allowlist e il controllo sugli indirizzi privati sono gia' stati
    # applicati QUI SOPRA, sull'URL di destinazione. Devono restare prima di
    # questo punto: passare da Jina non deve poter aggirare i confini.
    via_jina = _usa_jina() and not wiki
    if via_jina:
        intestazioni = {
            "Accept": "text/plain",
            "X-Remove-Selector": config.JINA_REMOVE_SELECTOR,
            "X-Retain-Images": "none",
        }
        if config.JINA_API_KEY:
            intestazioni["Authorization"] = f"Bearer {config.JINA_API_KEY}"
        request = urllib.request.Request(JINA_READER + url, headers=intestazioni)
    else:
        request = urllib.request.Request(url, headers={
            "User-Agent": "agency-bot/1.0 (+https://github.com/mtornani/App1)",
            "Accept": "text/html,application/json,text/plain;q=0.9",
        })
    # Un 429 o un 503 in CI non ha nessuno che rilanci a mano: si ritenta una
    # volta sola, quanto basta a superare un rate limit momentaneo.
    raw, content_type, last_error = b"", "", ""
    for attempt in range(2):
        try:
            with urllib.request.urlopen(request, timeout=config.FETCH_TIMEOUT) as response:
                # Il redirect e' gia' stato seguito da urllib: ricontrolla dove siamo
                # finiti. In modo Jina l'host finale e' r.jina.ai, che e' atteso.
                if not via_jina:
                    final_host = urllib.parse.urlparse(response.geturl()).hostname or ""
                    if not _domain_allowed(final_host):
                        raise ToolError(f"Redirect fuori allowlist: {final_host}")
                raw = response.read(config.FETCH_MAX_BYTES + 1)
                content_type = response.headers.get("Content-Type", "")
            break
        except urllib.error.HTTPError as error:
            origine = "r.jina.ai" if via_jina else parsed.hostname
            last_error = f"HTTP {error.code} da {origine}"
            if error.code not in (429, 502, 503, 504) or attempt == 1:
                raise ToolError(last_error) from error
            time.sleep(config.FETCH_RETRY_WAIT)
        except (urllib.error.URLError, TimeoutError, socket.timeout) as error:
            last_error = f"Rete: {error}"
            if attempt == 1:
                raise ToolError(last_error) from error
            time.sleep(config.FETCH_RETRY_WAIT)
    else:  # pragma: no cover - il ciclo esce sempre con break o con raise
        raise ToolError(last_error or "Fetch fallito.")

    truncated = len(raw) > config.FETCH_MAX_BYTES
    body = raw[: config.FETCH_MAX_BYTES].decode("utf-8", "replace")

    if wiki:
        text = _unwrap_wikipedia(body) or body
    elif via_jina:
        # Jina restituisce gia' markdown pulito: passarlo dall'estrattore HTML
        # lo rovinerebbe.
        text = body
    elif "json" in content_type:
        text = body
    elif "html" in content_type or body.lstrip().startswith("<"):
        parser = _TextExtractor()
        parser.feed(body)
        text = parser.text()
    else:
        text = body

    header = f"FONTE: {source_url}"
    if via_jina:
        header += " [via Jina Reader]"
    if truncated:
        header += f" [TRONCATO a {config.FETCH_MAX_BYTES} byte]"
    return f"{header}\n\n{text[: config.FETCH_MAX_BYTES]}"


# ------------------------------------------------------- scrittura e lettura

SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9._/-]+$")


def _safe_relative(path_text: str) -> Path:
    """Valida un percorso relativo: niente assoluti, niente '..', niente trucchi.

    Un percorso assoluto viene rifiutato invece che riscritto in silenzio:
    l'agente deve sapere che "/tmp/x.md" non e' dove crede di stare scrivendo.
    """

    candidate = path_text.strip()
    if not candidate:
        raise ToolError("Manca 'path'.")
    if candidate.startswith("/") or candidate.startswith("~"):
        raise ToolError("Usa un percorso relativo: i file stanno nella cartella della missione.")
    if not SAFE_NAME_RE.match(candidate):
        raise ToolError("Percorso con caratteri non ammessi.")
    path = Path(candidate)
    if path.is_absolute() or ".." in path.parts:
        raise ToolError("Percorso non consentito.")
    return path


def tool_write_file(args: Dict[str, object], ctx: "ToolContext") -> str:
    """Scrive un file negli artefatti della missione.

    Argomenti: {"path": "report.md", "content": "..."}
    """

    relative = _safe_relative(str(args.get("path", "")))
    content = args.get("content")
    if not isinstance(content, str):
        raise ToolError("'content' deve essere una stringa.")
    if len(content.encode("utf-8")) > config.WRITE_MAX_BYTES:
        raise ToolError(f"File oltre il tetto di {config.WRITE_MAX_BYTES} byte.")
    if len(ctx.artifacts) >= config.MAX_ARTIFACTS:
        raise ToolError(f"Raggiunto il tetto di {config.MAX_ARTIFACTS} file per missione.")

    target = ctx.output_dir / relative
    # Difesa in profondita': anche se la validazione sopra cambiasse, il file
    # deve comunque restare dentro la cartella della missione.
    try:
        target.resolve().relative_to(ctx.output_dir.resolve())
    except ValueError as error:
        raise ToolError("Percorso fuori dalla cartella della missione.") from error

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

    artifact = str(relative)
    if artifact not in ctx.artifacts:
        ctx.artifacts.append(artifact)
    return f"Scritto {artifact} ({len(content)} caratteri)."


def tool_read_file(args: Dict[str, object], ctx: "ToolContext") -> str:
    """Legge un file del repo. Argomenti: {"path": "openscout/src/metrics.js"}"""

    relative = _safe_relative(str(args.get("path", "")))
    parts = set(relative.parts)
    if parts & {".git", "node_modules", "__pycache__"} or relative.name.startswith("."):
        raise ToolError("File non leggibile.")
    if relative.suffix.lower() not in config.READABLE_SUFFIXES:
        raise ToolError(
            f"Estensione non ammessa. Consentite: {', '.join(sorted(config.READABLE_SUFFIXES))}"
        )

    target = ctx.repo_root / relative
    try:
        target.resolve().relative_to(ctx.repo_root.resolve())
    except ValueError as error:
        raise ToolError("Percorso fuori dal repository.") from error
    if not target.is_file():
        raise ToolError(f"File inesistente: {relative}")

    data = target.read_bytes()[: config.READ_MAX_BYTES]
    suffix = " [TRONCATO]" if target.stat().st_size > config.READ_MAX_BYTES else ""
    return f"FILE: {relative}{suffix}\n\n{data.decode('utf-8', 'replace')}"


# ------------------------------------------------------------------- vault

# Il vault e' la memoria che sopravvive alla missione. Due regole dure:
#   - raw/ non si tocca mai, e' la fonte di verita' dell'umano;
#   - si scrive solo dentro wiki/, piu' index.md e log.md alla radice.

VAULT_WRITABLE_ROOT = "wiki"
VAULT_WRITABLE_FILES = {"index.md", "log.md"}


def _vault_path(path_text: str, for_writing: bool) -> Path:
    """Valida un percorso dentro il vault e applica le zone di scrittura."""

    relative = _safe_relative(path_text)
    if relative.suffix.lower() not in {".md", ".txt", ".json", ".csv", ".yaml", ".yml"}:
        raise ToolError("Nel vault si lavora su file di testo: md, txt, json, csv, yaml.")

    if for_writing:
        name = str(relative)
        if relative.parts[0] == "raw":
            raise ToolError(
                "raw/ e' immutabile: e' la fonte di verita' dell'umano. "
                "Scrivi in wiki/ quello che hai capito dalla fonte."
            )
        if relative.parts[0] != VAULT_WRITABLE_ROOT and name not in VAULT_WRITABLE_FILES:
            raise ToolError(
                "Si scrive solo in wiki/, oppure su index.md e log.md alla radice."
            )

    target = config.VAULT_DIR / relative
    try:
        target.resolve().relative_to(config.VAULT_DIR.resolve())
    except ValueError as error:
        raise ToolError("Percorso fuori dal vault.") from error
    return target


def tool_vault_read(args: Dict[str, object], _ctx: "ToolContext") -> str:
    """Legge una pagina del vault. Argomenti: {"path": "wiki/decisione-x.md"}"""

    target = _vault_path(str(args.get("path", "")), for_writing=False)
    if not target.is_file():
        raise ToolError(f"Pagina inesistente: {args.get('path')}. Usa vault_list per vedere cosa c'e'.")
    data = target.read_bytes()[: config.VAULT_MAX_BYTES]
    suffix = " [TRONCATA]" if target.stat().st_size > config.VAULT_MAX_BYTES else ""
    return f"VAULT: {args.get('path')}{suffix}\n\n{data.decode('utf-8', 'replace')}"


def tool_vault_write(args: Dict[str, object], ctx: "ToolContext") -> str:
    """Scrive o riscrive una pagina della wiki.

    Argomenti: {"path": "wiki/decisione-x.md", "content": "..."}
    Con {"append": true} aggiunge in fondo invece di sostituire: serve per log.md,
    che e' append-only per contratto.
    """

    path_text = str(args.get("path", ""))
    target = _vault_path(path_text, for_writing=True)
    content = args.get("content")
    if not isinstance(content, str):
        raise ToolError("'content' deve essere una stringa.")
    if len(content.encode("utf-8")) > config.VAULT_MAX_BYTES:
        raise ToolError(f"Pagina oltre il tetto di {config.VAULT_MAX_BYTES} byte. Spezzala in piu' pagine.")

    target.parent.mkdir(parents=True, exist_ok=True)
    append = bool(args.get("append"))
    if append and target.exists():
        existing = target.read_text(encoding="utf-8")
        separator = "" if existing.endswith("\n") else "\n"
        target.write_text(existing + separator + content.rstrip() + "\n", encoding="utf-8")
        verb = "Aggiunto a"
    else:
        target.write_text(content.rstrip() + "\n", encoding="utf-8")
        verb = "Scritto"

    page = str(Path(path_text.strip().lstrip("/")))
    if page not in ctx.vault_pages:
        ctx.vault_pages.append(page)
    return f"{verb} {page} ({len(content)} caratteri)."


def tool_vault_list(args: Dict[str, object], _ctx: "ToolContext") -> str:
    """Elenca le pagine del vault. Argomenti: {"prefix": "wiki"} (opzionale)."""

    prefix = str(args.get("prefix", "")).strip().strip("/")
    if prefix:
        _safe_relative(prefix + "/x.md")  # stessa validazione dei percorsi
    base = config.VAULT_DIR / prefix if prefix else config.VAULT_DIR
    if not base.is_dir():
        raise ToolError(f"Cartella inesistente nel vault: {prefix or '.'}")

    rows = []
    for path in sorted(base.rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        rows.append(f"{path.relative_to(config.VAULT_DIR)}  ({path.stat().st_size} byte)")
        if len(rows) >= config.VAULT_MAX_LIST:
            rows.append(f"[...] elenco troncato a {config.VAULT_MAX_LIST} voci")
            break
    return "PAGINE NEL VAULT:\n" + ("\n".join(rows) if rows else "(vuoto)")


# ------------------------------------------------------------------ registro

ToolFn = Callable[[Dict[str, object], "ToolContext"], str]

REGISTRY: Dict[str, Tuple[ToolFn, str]] = {
    "fetch": (tool_fetch, 'TOOL: fetch\n{"url": "https://esempio.org/pagina"}\n  Scarica una pagina o una API pubblica e ne restituisce il testo.'),
    "write_file": (tool_write_file, 'TOOL: write_file\n{"path": "report.md", "content": "..."}\n  Salva un file tra gli artefatti della missione. E\' cosi\' che il lavoro resta.'),
    "read_file": (tool_read_file, 'TOOL: read_file\n{"path": "openscout/src/metrics.js"}\n  Legge un file gia\' presente nel repository.'),
    "vault_list": (tool_vault_list, 'TOOL: vault_list\n{"prefix": "wiki"}\n  Elenca le pagine del vault. Comincia sempre da qui.'),
    "vault_read": (tool_vault_read, 'TOOL: vault_read\n{"path": "wiki/nome-pagina.md"}\n  Legge una pagina del vault o una fonte in raw/.'),
    "vault_write": (tool_vault_write, 'TOOL: vault_write\n{"path": "wiki/nome-pagina.md", "content": "...", "append": false}\n  Scrive una pagina della wiki. raw/ e\' immutabile. Usa append per log.md.'),
}


@dataclass
class ToolContext:
    """Stato condiviso di una missione: dove scrivere, cosa e' stato prodotto."""

    mission_id: str
    output_dir: Path
    repo_root: Path
    artifacts: List[str]
    vault_pages: List[str]
    calls: List[Dict[str, object]]


def build_context(mission_id: str) -> ToolContext:
    output_dir = config.OUTPUT_DIR / mission_id
    output_dir.mkdir(parents=True, exist_ok=True)
    return ToolContext(
        mission_id=mission_id,
        output_dir=output_dir,
        repo_root=config.REPO_ROOT,
        artifacts=[],
        vault_pages=[],
        calls=[],
    )


def protocol_prompt(tool_names: List[str]) -> str:
    """Istruzioni di protocollo, aggiunte solo agli agenti che hanno tool."""

    available = [name for name in tool_names if name in REGISTRY]
    if not available:
        return ""
    specs = "\n\n".join(REGISTRY[name][1] for name in available)
    return (
        "\n\n=== STRUMENTI ===\n"
        "Puoi usare strumenti reali. Per usarne uno termina il messaggio con "
        "esattamente due righe:\n"
        "la riga TOOL: <nome> e, sotto, gli argomenti come oggetto JSON su una riga.\n"
        "Una sola chiamata per messaggio. Riceverai il risultato e potrai continuare.\n"
        "Quando hai finito, scrivi la risposta senza alcuna riga TOOL.\n\n"
        f"Strumenti disponibili:\n\n{specs}\n\n"
        "Regole: non inventare il contenuto di una pagina che non hai scaricato, "
        "e non dichiarare di aver salvato un file se non hai usato write_file."
    )


def strip_calls(text: str) -> str:
    """Toglie le righe di protocollo dal testo.

    Serve sulla risposta finale: una riga TOOL rimasta li' e' rumore di
    protocollo, e senza questa pulizia finirebbe dritta nel deliverable.
    """

    return TOOL_CALL_RE.sub("", text).strip()


def parse_call(text: str) -> Optional[Tuple[str, Dict[str, object]]]:
    """Estrae l'ultima chiamata a tool dal messaggio, se c'e'."""

    matches = list(TOOL_CALL_RE.finditer(text))
    if not matches:
        return None
    name, raw_args = matches[-1].group(1).lower(), matches[-1].group(2)
    try:
        args = json.loads(raw_args)
    except json.JSONDecodeError:
        return name, {"__json_error__": raw_args[:200]}
    return name, args if isinstance(args, dict) else {"__json_error__": "atteso oggetto JSON"}


def execute(name: str, args: Dict[str, object], ctx: ToolContext, allowed: List[str]) -> ToolResult:
    """Esegue una chiamata applicando i permessi dell'agente.

    Un errore non interrompe la missione: torna all'agente come messaggio, cosi'
    puo' correggersi da solo invece di far fallire tutto il giro.
    """

    def finish(result: ToolResult) -> ToolResult:
        ctx.calls.append({
            "tool": result.tool,
            "args": {k: (v[:120] if isinstance(v, str) else v) for k, v in result.args.items()},
            "ok": result.ok,
            "detail": result.detail or result.output[:160],
        })
        return result

    if "__json_error__" in args:
        return finish(ToolResult(name, {}, False,
                                 "Argomenti non JSON validi. Riscrivi l'oggetto su una riga.",
                                 "json non valido"))
    if name not in REGISTRY:
        return finish(ToolResult(name, args, False,
                                 f"Strumento '{name}' inesistente. Disponibili: {', '.join(allowed)}.",
                                 "tool sconosciuto"))
    if name not in allowed:
        return finish(ToolResult(name, args, False,
                                 f"Non hai il permesso per '{name}'. Tuoi strumenti: {', '.join(allowed) or 'nessuno'}.",
                                 "permesso negato"))
    try:
        output = REGISTRY[name][0](args, ctx)
        return finish(ToolResult(name, args, True, output))
    except ToolError as error:
        return finish(ToolResult(name, args, False, f"Errore: {error}", str(error)))
    except Exception as error:  # noqa: BLE001 - un tool rotto non deve uccidere la missione
        return finish(ToolResult(name, args, False,
                                 f"Errore imprevisto: {type(error).__name__}: {error}",
                                 type(error).__name__))
