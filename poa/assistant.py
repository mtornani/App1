"""Core logic for the Personal Operations Assistant."""

from __future__ import annotations

import random
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from . import storage
from .config import PROJECTS


@dataclass
class Task:
    """A lightweight representation of a stored task."""

    id: int
    description: str
    category: str
    stimulation: int
    system_building: int
    automation_potential: int
    human_interaction: int
    repetitive: bool
    status: str

    @property
    def priority(self) -> int:
        """Compute the priority using the brutalist algorithm."""

        return (
            self.stimulation * 3
            + self.system_building * 2
            + self.automation_potential * 2
            - self.human_interaction * 5
        )


def _row_to_task(row) -> Task:
    return Task(
        id=row["id"],
        description=row["description"],
        category=row["category"],
        stimulation=row["stimulation"],
        system_building=row["system_building"],
        automation_potential=row["automation_potential"],
        human_interaction=row["human_interaction"],
        repetitive=bool(row["repetitive"]),
        status=row["status"],
    )


class PersonalOpsAssistant:
    """Brain-dead honest assistant tuned for antisocial creatives."""

    def __init__(self) -> None:
        storage.setup_database()
        storage.seed_defaults()

    # ------------------------------------------------------------------
    # Morning brief
    # ------------------------------------------------------------------
    def morning_brief(self) -> Dict[str, object]:
        tasks = [_row_to_task(row) for row in storage.fetch_tasks()]
        complex_task = next((task for task in tasks if task.priority >= 10), None)
        if complex_task is None and tasks:
            complex_task = tasks[0]

        boring_task = next(
            (task for task in tasks if task.category in {"boring", "maintenance"}),
            None,
        )
        ignore_tasks = [
            task
            for task in tasks
            if task.human_interaction >= 2 or task.priority <= 0
        ][:3]

        return {
            "energy_focus": complex_task.description if complex_task else "Build anything worthwhile",
            "boring": boring_task.description if boring_task else "None worth your time",
            "ignore": [task.description for task in ignore_tasks] or ["Everything screaming for attention"],
        }

    # ------------------------------------------------------------------
    # Task evaluation
    # ------------------------------------------------------------------
    def evaluate_task(self, description: str) -> Dict[str, object]:
        metrics = self._score_description(description)
        score = (
            metrics["intellectual_stimulation"] * 3
            + metrics["system_building"] * 2
            + metrics["automation_potential"] * 2
            - metrics["human_interaction"] * 5
        )

        reason_parts = []
        if metrics["human_interaction"]:
            reason_parts.append("High human interaction")
        if not metrics["intellectual_stimulation"]:
            reason_parts.append("Zero intellectual stimulation")
        if metrics["repetition"]:
            reason_parts.append("Repetitive nonsense")
        if not reason_parts:
            reason_parts.append("Finally something worthy")

        alternative = self._suggest_alternative(description, metrics)

        return {
            "score": score,
            "reason": ", ".join(reason_parts),
            "alternative": alternative,
        }

    def _score_description(self, description: str) -> Dict[str, int]:
        lowered = description.lower()
        def flag(*keywords: str) -> int:
            return 1 if any(word in lowered for word in keywords) else 0

        metrics = {
            "intellectual_stimulation": 0,
            "system_building": 0,
            "automation_potential": 0,
            "human_interaction": 0,
            "repetition": 0,
        }

        if flag("build", "design", "architect", "engine", "model", "algorithm"):
            metrics["intellectual_stimulation"] = 2
        if flag("research", "experiment", "novel"):
            metrics["intellectual_stimulation"] = max(metrics["intellectual_stimulation"], 3)
        if flag("optimize", "refactor", "system", "pipeline", "automation", "framework"):
            metrics["system_building"] = 2
        if flag("automate", "automation", "script", "template", "bot"):
            metrics["automation_potential"] = 3
        elif flag("repeat", "daily", "weekly", "boring", "manual"):
            metrics["automation_potential"] = 2
        if flag("email", "call", "meeting", "customer", "client", "interview", "conference"):
            metrics["human_interaction"] = 3
        elif flag("review", "feedback", "sync"):
            metrics["human_interaction"] = 2
        if flag("again", "follow up", "respond", "update", "report"):
            metrics["repetition"] = 1

        if metrics["intellectual_stimulation"] == 0 and flag("debug", "fix", "maintain"):
            metrics["intellectual_stimulation"] = 1

        if metrics["system_building"] == 0 and flag("build"):
            metrics["system_building"] = 1

        if metrics["automation_potential"] == 0 and metrics["repetition"]:
            metrics["automation_potential"] = 2

        return metrics

    def _suggest_alternative(self, description: str, metrics: Dict[str, int]) -> str:
        lowered = description.lower()
        if metrics["human_interaction"] >= 2:
            return "Automate the interaction – design a template or a bot and stop talking to humans"
        if "document" in lowered or "doc" in lowered:
            return "Record a loom, auto-transcribe, and ship docs without typing"
        if metrics["repetition"]:
            return "Spend 90 minutes scripting it once, save yourself forever"
        return "Enhance the system – add a feedback loop or monitoring"

    # ------------------------------------------------------------------
    # Focus protector
    # ------------------------------------------------------------------
    def focus_protector(self) -> Dict[str, object]:
        storage.add_focus_session(90, "Deep work initiated by focus protector")
        storage.record_activity("focus_mode", {"duration": 90})
        return {
            "notifications": "All notifications muted (pretend they never existed)",
            "status": "Slack/Discord set to 'Building. Response time: 48h'",
            "timer": "90-minute deep work timer started",
            "log": "Focus session logged for future bragging rights",
        }

    # ------------------------------------------------------------------
    # Decision maker
    # ------------------------------------------------------------------
    def decide(self, question: str) -> Dict[str, object]:
        lowered = question.lower()
        networking = any(word in lowered for word in ["conference", "meet", "network", "event", "call"])
        knowledge_gain = any(word in lowered for word in ["learn", "workshop", "course", "deep dive", "technical"])
        logistics = any(word in lowered for word in ["travel", "flight", "hotel", "schedule"])
        verdict = "Skip. Watch recordings at 2x speed instead."
        if knowledge_gain and not networking:
            verdict = "Attend only if recordings aren't available. Otherwise stream at 2x."
        elif not networking and "buy" in lowered:
            verdict = "Purchase if it accelerates automation. Otherwise pass."
        friction = "HIGH" if networking else ("MEDIUM" if logistics else "LOW")
        return {
            "analysis": {
                "networking_required": "HIGH" if networking else "LOW",
                "new_knowledge": "HIGH" if knowledge_gain else "LOW",
                "logistical_drag": friction,
            },
            "verdict": verdict,
        }

    # ------------------------------------------------------------------
    # Energy tracker
    # ------------------------------------------------------------------
    def energy_tracker(self) -> Dict[str, object]:
        now = datetime.now()
        base = 80 if 8 <= now.hour <= 12 else 60
        if now.hour >= 20 or now.hour <= 6:
            base = 35
        recent_sessions = storage.last_focus_session(within_hours=8)
        if recent_sessions:
            base -= 10
        recent_energy = storage.fetch_recent_energy()
        if recent_energy:
            base = int((base + sum(row["level"] for row in recent_energy) / len(recent_energy)) / 2)
        base = max(0, min(100, base))

        if base < 30:
            suggestion = "Stop pretending to work. Go walk."
        elif base > 70:
            suggestion = "Perfect time for a complex system build"
        else:
            suggestion = "Handle medium-intensity automation tasks"

        storage.log_energy(base, suggestion)
        return {
            "level": base,
            "suggestion": suggestion,
        }

    # ------------------------------------------------------------------
    # Weekly reality check
    # ------------------------------------------------------------------
    def weekly_reality_check(self) -> Dict[str, object]:
        planned = [_row_to_task(row) for row in storage.fetch_planned_tasks()]
        planned_descriptions = [task.description for task in planned] or ["You planned nothing, congrats"]
        actual = self._git_activity_last_week()
        accuracy = self._calculate_accuracy(planned_descriptions, actual)
        recommendation = (
            "Stop planning, start building"
            if accuracy < 50
            else "Planning aligned with execution. Keep momentum"
        )
        return {
            "planned": planned_descriptions,
            "actual": actual,
            "accuracy": accuracy,
            "recommendation": recommendation,
        }

    def _git_activity_last_week(self) -> List[str]:
        try:
            output = subprocess.check_output(
                [
                    "git",
                    "log",
                    "--since=7.days",
                    "--pretty=format:%h %s",
                ],
                cwd=Path.cwd(),
                text=True,
            )
        except subprocess.CalledProcessError:
            return ["No git history accessible"]
        commits = [line.strip() for line in output.splitlines() if line.strip()]
        return commits or ["No commits in the last 7 days"]

    def _calculate_accuracy(self, planned: List[str], actual: List[str]) -> int:
        if not planned:
            return 0
        matches = sum(1 for task in planned if any(task.lower() in entry.lower() for entry in actual))
        return int((matches / len(planned)) * 100)

    # ------------------------------------------------------------------
    # OB1 integration
    # ------------------------------------------------------------------
    def ob1_focus(self) -> Dict[str, object]:
        ob1_config = PROJECTS["ob1"]
        priority_mode = ob1_config["priority_algorithm"]()
        stimulating = list(ob1_config["stimulating_tasks"])
        random.shuffle(stimulating)
        return {
            "mode": priority_mode,
            "build": f"Automated {stimulating[0]} tracker (3h)",
            "automate": "User onboarding so you never touch it again",
            "ignore": "Feature requests from users with <€1000 MRR",
            "reminder": "You're building a truth machine, not a friend maker.",
        }

    # ------------------------------------------------------------------
    # Cognitive load manager
    # ------------------------------------------------------------------
    def cognitive_load_manager(self) -> Dict[str, object]:
        loops = storage.fetch_open_loops()
        auto_closed: List[str] = []
        remaining: List[str] = []
        for loop in loops:
            description = loop["description"].lower()
            if "follow up" in description:
                storage.delete_open_loop(loop["id"])
                auto_closed.append(f"{loop['description']} → Deleted (they'll chase you if it's real)")
            elif any(keyword in description for keyword in ["maybe", "should", "consider"]):
                storage.close_open_loop(loop["id"], "Moved to /dev/null")
                auto_closed.append(f"{loop['description']} → Moved to /dev/null")
            elif "network" in description:
                storage.close_open_loop(loop["id"], "Number blocked")
                auto_closed.append(f"{loop['description']} → Blocked number")
            else:
                remaining.append(loop["description"])

        focus = remaining[0] if remaining else "OB1 prediction engine"
        return {
            "load": min(100, 20 + len(loops) * 5),
            "open_loops": len(loops),
            "auto_closed": auto_closed or ["Nothing disposable left"],
            "remaining_focus": focus,
            "mode": "Cave dwelling (no inputs, pure building)",
        }

