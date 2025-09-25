"""Command-line interface for the Personal Operations Assistant."""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from .assistant import PersonalOpsAssistant


def _render(data: Dict[str, Any]) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="poa",
        description="Personal Operations Assistant – zero pleasantries, pure execution.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("morning", help="Deliver the brutal morning brief")

    evaluate_parser = subparsers.add_parser("evaluate", help="Score a task against your brain chemistry")
    evaluate_parser.add_argument("description", help="Task description to evaluate")

    subparsers.add_parser("focus", help="Trigger the focus protector rituals")

    decide_parser = subparsers.add_parser("decide", help="Make a low-stakes decision without emotion")
    decide_parser.add_argument("question", help="Decision prompt")

    subparsers.add_parser("energy", help="Check current energy and recommended usage")
    subparsers.add_parser("weekly", help="Run the weekly reality check")
    subparsers.add_parser("ob1", help="Get the OB1 focus briefing")
    subparsers.add_parser("load", help="Engage the cognitive load manager")

    args = parser.parse_args(argv)

    assistant = PersonalOpsAssistant()
    if args.command == "morning":
        result = assistant.morning_brief()
    elif args.command == "evaluate":
        result = assistant.evaluate_task(args.description)
    elif args.command == "focus":
        result = assistant.focus_protector()
    elif args.command == "decide":
        result = assistant.decide(args.question)
    elif args.command == "energy":
        result = assistant.energy_tracker()
    elif args.command == "weekly":
        result = assistant.weekly_reality_check()
    elif args.command == "ob1":
        result = assistant.ob1_focus()
    elif args.command == "load":
        result = assistant.cognitive_load_manager()
    else:
        parser.error("Unknown command")
        return 1

    print(_render(result))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
