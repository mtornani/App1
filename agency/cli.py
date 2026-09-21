"""CLI dell'agenzia: `python -m agency <comando>`.

E' la stessa interfaccia che usa GitHub Actions, quindi cio' che provi in
locale e' esattamente cio' che gira nel cloud.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List

from . import brief as brief_mod
from . import config, roster, store
from .orchestrator import execute_mission
from .providers import ProviderError, build_provider


def _print(payload: Any) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _cmd_roster(_: argparse.Namespace) -> int:
    _print(
        [
            {"id": a.id, "name": a.name, "title": a.title,
             "tools": a.tools, "handoff": a.can_handoff}
            for a in roster.load_roster().values()
        ]
    )
    return 0


def _cmd_new(args: argparse.Namespace) -> int:
    agents = [a.strip() for a in (args.agents or "").split(",") if a.strip()]
    for agent_id in agents:
        roster.get_agent(agent_id)  # validazione immediata: fallisce qui, non a meta' run
    mission = store.create_mission(
        objective=args.objective,
        topology=args.topology,
        agents=agents,
        context=args.context or "",
        source=args.source,
    )
    store.rebuild_index()
    if args.run:
        return _run_one(mission["id"], args)
    _print(mission)
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    missions = store.list_missions(args.status)
    _print(
        [
            {
                "id": m["id"],
                "status": m["status"],
                "topology": m.get("topology"),
                "objective": m["objective"][:80],
                "created_at": m.get("created_at"),
            }
            for m in missions
        ]
    )
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    mission = store.load_mission(args.mission_id)
    run = store.load_run(args.mission_id)
    if args.deliverable:
        print(mission.get("deliverable") or "(nessun deliverable)")
        return 0
    _print({"mission": mission, "run": run})
    return 0


def _build(args: argparse.Namespace):
    return build_provider(args.provider or "", args.model or "")


def _run_one(mission_id: str, args: argparse.Namespace) -> int:
    try:
        run = execute_mission(mission_id, _build(args))
    except ProviderError as error:
        print(f"[errore provider] {error}", file=sys.stderr)
        return 2
    except (ValueError, KeyError, FileNotFoundError) as error:
        print(f"[errore missione] {error}", file=sys.stderr)
        return 2
    if args.quiet:
        print(f"{mission_id}: {run['steps']} passi, provider {run['provider']}")
    else:
        _print(run)
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    return _run_one(args.mission_id, args)


def _cmd_work(args: argparse.Namespace) -> int:
    """Svuota la coda: e' il comando che chiama GitHub Actions a ogni giro.

    Una missione fallita non ferma le altre: l'errore resta sulla missione e
    il giro prosegue, altrimenti una chiave scaduta bloccherebbe tutta l'agenzia.
    """

    queue = store.pending_missions(limit=args.limit)
    if not queue:
        store.rebuild_index()
        print("Nessuna missione pending.")
        return 0

    results: List[Dict[str, Any]] = []
    failures = 0
    for mission in queue:
        mission_id = mission["id"]
        print(f"-> {mission_id}: {mission['objective'][:70]}", flush=True)
        try:
            run = execute_mission(mission_id, _build(args))
            results.append({"id": mission_id, "status": "done", "steps": run["steps"]})
        except Exception as error:  # noqa: BLE001 - un fallimento non deve fermare la coda
            failures += 1
            results.append({"id": mission_id, "status": "failed", "error": str(error)[:200]})
            print(f"   fallita: {error}", file=sys.stderr, flush=True)
    store.rebuild_index()
    _print({"processed": len(results), "failed": failures, "results": results})
    # Uscita 0 anche con fallimenti parziali: il workflow deve comunque committare
    # lo stato aggiornato, altrimenti l'errore resterebbe invisibile dal telefono.
    return 0


def _cmd_brief(args: argparse.Namespace) -> int:
    """Il sistema parla per primo. Nessuna chiamata al modello, costo zero."""

    dati = brief_mod.componi()
    if args.json:
        _print(dati)
    else:
        print(brief_mod.formatta(dati))
    return 0


def _cmd_index(_: argparse.Namespace) -> int:
    _print(store.rebuild_index())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agency",
        description="Agenzia autonoma: missioni eseguite da un team di agenti.",
    )
    parser.add_argument("--provider", help="anthropic | openrouter | echo")
    parser.add_argument("--model", help="Override del modello")
    parser.add_argument("--quiet", action="store_true", help="Output sintetico")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("roster", help="Elenca gli agenti disponibili")

    new = sub.add_parser("new", help="Crea una missione")
    new.add_argument("objective", help="Obiettivo della missione")
    new.add_argument("--topology", default="team", choices=["solo", "team", "swarm"])
    new.add_argument("--agents", help="Id agenti separati da virgola (solo/swarm: il primo parte)")
    new.add_argument("--context", help="Contesto aggiuntivo")
    new.add_argument("--source", default="cli", help="Origine della missione")
    new.add_argument("--run", action="store_true", help="Esegui subito dopo la creazione")

    listing = sub.add_parser("list", help="Elenca le missioni")
    listing.add_argument("--status", choices=list(config.STATUSES))

    show = sub.add_parser("show", help="Mostra missione e transcript")
    show.add_argument("mission_id")
    show.add_argument("--deliverable", action="store_true", help="Solo il testo finale")

    run = sub.add_parser("run", help="Esegui una missione")
    run.add_argument("mission_id")

    work = sub.add_parser("work", help="Esegui le missioni pending (usato dalla CI)")
    work.add_argument("--limit", type=int, default=config.MAX_MISSIONS_PER_RUN)

    brief_parser = sub.add_parser(
        "brief", help="Cosa fare adesso, letto dal vault. Nessun modello, costo zero")
    brief_parser.add_argument("--json", action="store_true", help="Output grezzo")

    sub.add_parser("index", help="Rigenera state/index.json per la PWA")
    return parser


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handlers = {
        "roster": _cmd_roster,
        "new": _cmd_new,
        "list": _cmd_list,
        "show": _cmd_show,
        "run": _cmd_run,
        "work": _cmd_work,
        "brief": _cmd_brief,
        "index": _cmd_index,
    }
    try:
        return handlers[args.command](args)
    except (KeyError, FileNotFoundError, ValueError) as error:
        print(f"[errore] {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
