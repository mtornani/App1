"""Accesso agli LLM via stdlib (urllib): nessun SDK, nessuna dipendenza.

Quattro provider:
  - anthropic  : Messages API
  - openrouter : Chat Completions (utile per modelli misti/fallback)
  - zai        : modelli GLM, endpoint compatibile OpenAI
  - echo       : offline e deterministico, per test e dry-run senza chiavi
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Dict, List, Optional

from . import config


class ProviderError(RuntimeError):
    """Errore non recuperabile nella chiamata al modello."""


def _post_json(url: str, headers: Dict[str, str], payload: Dict, retries: int = 3) -> Dict:
    """POST JSON con backoff esponenziale su errori transitori (429/5xx/rete)."""

    body = json.dumps(payload).encode("utf-8")
    last_error = ""
    for attempt in range(retries):
        request = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=config.HTTP_TIMEOUT) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", "replace")[:500]
            last_error = f"HTTP {error.code}: {detail}"
            # 4xx diversi da 429 sono errori nostri: inutile ritentare.
            if error.code != 429 and error.code < 500:
                raise ProviderError(last_error) from error
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            last_error = f"{type(error).__name__}: {error}"
        if attempt < retries - 1:
            time.sleep(2 ** attempt)
    raise ProviderError(f"Chiamata fallita dopo {retries} tentativi. {last_error}")


class AnthropicProvider:
    """Anthropic Messages API."""

    name = "anthropic"

    def __init__(self, model: str, api_key: str) -> None:
        if not api_key:
            raise ProviderError("ANTHROPIC_API_KEY mancante.")
        self.model = model
        self.api_key = api_key

    def complete(self, system: str, messages: List[Dict[str, str]], max_tokens: int) -> str:
        data = _post_json(
            "https://api.anthropic.com/v1/messages",
            {
                "content-type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            {
                "model": self.model,
                "max_tokens": max_tokens,
                "system": system,
                "messages": messages,
            },
        )
        parts = [block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"]
        return "\n".join(part for part in parts if part).strip()


class OpenAICompatibleProvider:
    """Endpoint in formato chat completions (system come primo messaggio).

    Lo parlano in molti: OpenRouter, Z.ai e chiunque esponga /chat/completions.
    Cambiano solo URL, chiave e nome del modello, quindi una classe sola basta.
    """

    def __init__(self, name: str, url: str, model: str, api_key: str, key_env: str,
                 extra_body: Optional[Dict[str, object]] = None) -> None:
        if not api_key:
            raise ProviderError(f"{key_env} mancante.")
        self.name = name
        self.url = url
        self.model = model
        self.api_key = api_key
        self.extra_body = dict(extra_body or {})

    def complete(self, system: str, messages: List[Dict[str, str]], max_tokens: int) -> str:
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": system}] + messages,
        }
        payload.update(self.extra_body)
        data = _post_json(
            self.url,
            {
                "content-type": "application/json",
                "authorization": f"Bearer {self.api_key}",
            },
            payload,
        )
        choices = data.get("choices") or []
        if not choices:
            raise ProviderError(f"Risposta senza choices: {json.dumps(data)[:300]}")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, list):
            # Alcuni endpoint restituiscono il contenuto a blocchi invece che
            # come stringa: si concatenano le parti testuali.
            content = "".join(
                part.get("text", "") for part in content if isinstance(part, dict)
            )
        if not (content or "").strip():
            # Un modello che ragiona puo' spendere tutto il budget nel reasoning
            # e restituire un contenuto vuoto: meglio dirlo che passare "" a valle.
            raise ProviderError(
                f"Risposta vuota da {self.name}. "
                "Alza AGENCY_MAX_TOKENS o abbassa lo sforzo di reasoning."
            )
        return content.strip()


def OpenRouterProvider(model: str, api_key: str) -> OpenAICompatibleProvider:
    """OpenRouter."""

    return OpenAICompatibleProvider(
        "openrouter", "https://openrouter.ai/api/v1/chat/completions",
        model, api_key, "OPENROUTER_API_KEY",
    )


def ZaiProvider(model: str, api_key: str) -> OpenAICompatibleProvider:
    """Z.ai (modelli GLM), endpoint compatibile OpenAI.

    GLM-5.3 ragiona sempre: lo sforzo si regola con reasoning_effort, e per il
    lavoro dell'agenzia "low" e' il default sensato, perche' i turni sono corti
    e il budget di token e' condiviso fra sei ruoli.
    """

    return OpenAICompatibleProvider(
        "zai", "https://api.z.ai/api/paas/v4/chat/completions",
        model, api_key, "ZAI_API_KEY",
        extra_body={"reasoning_effort": config.ZAI_REASONING_EFFORT},
    )


class EchoProvider:
    """Provider offline: non chiama nulla, risponde in modo deterministico.

    Serve a tre cose concrete:
      - far girare i test senza chiavi ne' rete;
      - provare una topologia e vedere chi parla e in che ordine (dry-run);
      - non lasciare mai l'agenzia bloccata se una chiave scade.
    """

    name = "echo"

    def __init__(self, model: str = "echo-local", **_: object) -> None:
        self.model = model

    def complete(self, system: str, messages: List[Dict[str, str]], max_tokens: int) -> str:
        role = system.strip().splitlines()[0][:70] if system.strip() else "agente"
        last = messages[-1]["content"] if messages else ""
        # Il PM deve comunque restituire un piano valido, altrimenti il dry-run
        # della topologia "team" non arriverebbe mai agli altri agenti.
        if "Project Manager" in role:
            return json.dumps(
                {"plan": [{"agent": "researcher", "task": last[:200]},
                          {"agent": "writer", "task": "Componi il deliverable finale."}]},
                ensure_ascii=False,
            )
        return f"[DRY-RUN {self.model}] {role}\nInput ricevuto ({len(last)} caratteri):\n{last[:400]}"


def build_provider(provider_name: str = "", model: str = ""):
    """Istanzia il provider da configurazione o da override espliciti."""

    name = (provider_name or config.PROVIDER).strip().lower()
    chosen_model = model or config.model_for(name)
    if name == "anthropic":
        return AnthropicProvider(chosen_model, config.ANTHROPIC_API_KEY)
    if name == "openrouter":
        return OpenRouterProvider(chosen_model, config.OPENROUTER_API_KEY)
    if name == "zai":
        return ZaiProvider(chosen_model, config.ZAI_API_KEY)
    if name == "echo":
        return EchoProvider(chosen_model)
    raise ProviderError(
        f"Provider sconosciuto: '{name}'. Usa anthropic, openrouter, zai o echo."
    )
