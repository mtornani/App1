"""Orchestratore: tre topologie, stesso motore.

  solo   -> un agente, un turno. Il baseline con cui confrontare tutto il resto.
  team   -> il PM scompone la missione, gli specialisti eseguono in sequenza
            vedendo il lavoro di chi li precede. Organigramma d'azienda.
  swarm  -> nessun centro: ogni agente decide se chiudere o passare la palla
            a un altro con "HANDOFF: <id>". Scala bene, costa di piu'.

Vincoli comuni: tetto sui passi, transcript integrale, nessuno stato implicito.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from . import config, roster, store
from .providers import ProviderError, build_provider

# Un agente chiude la catena scrivendo DONE; oppure delega con HANDOFF: <id>.
HANDOFF_RE = re.compile(r"^\s*HANDOFF\s*:\s*([a-z_]+)", re.IGNORECASE | re.MULTILINE)
DONE_RE = re.compile(r"^\s*DONE\b", re.IGNORECASE | re.MULTILINE)


class Orchestrator:
    """Esegue una missione e restituisce il run completo (piano + transcript)."""

    def __init__(self, provider=None) -> None:
        self.provider = provider or build_provider()
        self.roster = roster.load_roster()

    # ------------------------------------------------------------ utilita'

    def _ask(self, agent: roster.Agent, prompt: str) -> str:
        """Un turno di un agente. Stateless: tutto il contesto sta nel prompt."""

        return self.provider.complete(
            system=agent.system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=config.MAX_TOKENS_PER_CALL,
        )

    @staticmethod
    def _brief(mission: Dict[str, Any]) -> str:
        """Intestazione comune a ogni prompt: obiettivo e contesto della missione."""

        lines = [f"OBIETTIVO DELLA MISSIONE:\n{mission['objective']}"]
        if mission.get("context"):
            lines.append(f"\nCONTESTO FORNITO:\n{mission['context']}")
        return "\n".join(lines)

    @staticmethod
    def _transcript_text(transcript: List[Dict[str, Any]], limit: int = 4) -> str:
        """Ultimi turni in chiaro: e' la memoria condivisa del team.

        Limitare la finestra e' voluto: e' la saturazione della context window
        il motivo per cui un agente solo degrada sui compiti lunghi.
        """

        if not transcript:
            return "(nessun lavoro precedente)"
        chunks = [
            f"--- {turn['agent']} ---\n{turn['output']}"
            for turn in transcript[-limit:]
        ]
        return "\n\n".join(chunks)

    @staticmethod
    def _extract_json(text: str) -> Optional[Dict[str, Any]]:
        """Recupera il primo oggetto JSON dal testo, anche dentro ```json ... ```.

        I modelli aggiungono spesso una frase di cortesia attorno al JSON:
        un parse rigido farebbe fallire il piano per un motivo cosmetico.
        """

        fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        candidates = [fenced.group(1)] if fenced else []
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            candidates.append(text[start : end + 1])
        for candidate in candidates:
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed
        return None

    def _record(
        self,
        transcript: List[Dict[str, Any]],
        agent: roster.Agent,
        task: str,
        output: str,
    ) -> None:
        transcript.append(
            {
                "step": len(transcript) + 1,
                "agent": agent.id,
                "label": agent.label,
                "task": task,
                "output": output,
                "at": store.utc_now(),
            }
        )

    # ----------------------------------------------------------- topologie

    def run_solo(self, mission: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Un solo agente: il primo indicato nella missione, default writer."""

        agent_id = (mission.get("agents") or ["writer"])[0]
        agent = roster.get_agent(agent_id)
        transcript: List[Dict[str, Any]] = []
        output = self._ask(agent, self._brief(mission))
        self._record(transcript, agent, mission["objective"], output)
        return transcript

    def plan(self, mission: Dict[str, Any]) -> List[Dict[str, str]]:
        """Il PM produce il piano. Se non e' parsabile, si degrada a un piano fisso."""

        pm = roster.get_agent("pm")
        prompt = (
            f"{self._brief(mission)}\n\n"
            f"ROSTER DISPONIBILE:\n"
            + "\n".join(
                f"- {self.roster[a].id}: {self.roster[a].title}"
                for a in roster.worker_ids()
            )
            + "\n\nProduci il piano in JSON."
        )
        raw = self._ask(pm, prompt)
        parsed = self._extract_json(raw) or {}
        steps = [
            {"agent": step["agent"], "task": str(step.get("task", "")).strip()}
            for step in parsed.get("plan", [])
            if isinstance(step, dict) and step.get("agent") in self.roster
        ]
        if not steps:
            # Fallback esplicito: meglio un piano prevedibile che una missione morta.
            steps = [
                {"agent": "researcher", "task": "Raccogli i fatti necessari all'obiettivo."},
                {"agent": "writer", "task": "Componi il deliverable finale."},
            ]
        return steps[: config.MAX_STEPS]

    def run_team(self, mission: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Pipeline pianificata dal PM: ogni specialista vede chi lo precede."""

        transcript: List[Dict[str, Any]] = []
        steps = self.plan(mission)
        mission["plan"] = steps
        for step in steps:
            agent = roster.get_agent(step["agent"])
            prompt = (
                f"{self._brief(mission)}\n\n"
                f"LAVORO GIA' SVOLTO DAL TEAM:\n{self._transcript_text(transcript)}\n\n"
                f"IL TUO COMPITO ORA:\n{step['task']}"
            )
            self._record(transcript, agent, step["task"], self._ask(agent, prompt))
        return transcript

    def run_swarm(self, mission: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Sciame: nessun orchestratore, gli agenti si passano il lavoro da soli."""

        transcript: List[Dict[str, Any]] = []
        current = (mission.get("agents") or ["researcher"])[0]
        seen_done = False
        for _ in range(config.MAX_STEPS):
            agent = roster.get_agent(current)
            allowed = [a for a in agent.can_handoff if a in self.roster]
            prompt = (
                f"{self._brief(mission)}\n\n"
                f"LAVORO GIA' SVOLTO:\n{self._transcript_text(transcript)}\n\n"
                "Svolgi la tua parte. Poi chiudi il messaggio con UNA di queste righe:\n"
                f"  HANDOFF: <{' | '.join(allowed) or 'nessuno'}>   (se serve un altro ruolo)\n"
                "  DONE                                             (se la missione e' completa)"
            )
            output = self._ask(agent, prompt)
            self._record(transcript, agent, "turno swarm", output)

            match = HANDOFF_RE.search(output)
            nxt = match.group(1).lower() if match else ""
            if DONE_RE.search(output) and not match:
                seen_done = True
                break
            if not nxt or nxt not in allowed:
                # Nessun passaggio valido: lo sciame ha esaurito la spinta.
                seen_done = True
                break
            current = nxt
        if not seen_done:
            transcript.append(
                {
                    "step": len(transcript) + 1,
                    "agent": "system",
                    "label": "system",
                    "task": "limite",
                    "output": f"[STOP] Raggiunto il tetto di {config.MAX_STEPS} passi senza DONE.",
                    "at": store.utc_now(),
                }
            )
        return transcript

    # ------------------------------------------------------------- ingresso

    def run(self, mission: Dict[str, Any]) -> Dict[str, Any]:
        """Esegue la missione secondo la sua topologia e restituisce il run."""

        topology = mission.get("topology", "team")
        runner = {
            "solo": self.run_solo,
            "team": self.run_team,
            "swarm": self.run_swarm,
        }.get(topology)
        if runner is None:
            raise ValueError(f"Topologia sconosciuta: '{topology}'. Usa solo, team o swarm.")

        started = store.utc_now()
        transcript = runner(mission)
        return {
            "mission_id": mission["id"],
            "objective": mission["objective"],
            "topology": topology,
            "provider": getattr(self.provider, "name", "?"),
            "model": getattr(self.provider, "model", "?"),
            "plan": mission.get("plan", []),
            "started_at": started,
            "finished_at": store.utc_now(),
            "steps": len(transcript),
            "transcript": transcript,
            "deliverable": transcript[-1]["output"] if transcript else "",
        }


def execute_mission(mission_id: str, provider=None) -> Dict[str, Any]:
    """Ciclo completo su una missione: running -> done/failed, con stato salvato.

    Lo stato viene scritto a ogni transizione: se il runner muore a meta',
    la missione resta marcata `running` e si vede subito quale si e' piantata.
    """

    mission = store.load_mission(mission_id)
    mission["status"] = "running"
    mission["started_at"] = store.utc_now()
    mission["error"] = None
    store.save_mission(mission)

    try:
        run = Orchestrator(provider).run(mission)
    except (ProviderError, ValueError, KeyError) as error:
        mission["status"] = "failed"
        mission["finished_at"] = store.utc_now()
        mission["error"] = f"{type(error).__name__}: {error}"
        store.save_mission(mission)
        store.rebuild_index()
        raise

    store.save_run(mission_id, run)
    mission["status"] = "done"
    mission["finished_at"] = run["finished_at"]
    mission["deliverable"] = run["deliverable"]
    mission["plan"] = run.get("plan", [])
    store.save_mission(mission)
    store.rebuild_index()
    return run
