"""Configuration and defaults for the Personal Operations Assistant."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from random import random
from typing import Callable, Dict, List


DATA_DIR = Path(__file__).resolve().parent / "data"
DB_PATH = DATA_DIR / "poa.db"


@dataclass
class TaskTemplate:
    """Default task template used to seed the database."""

    description: str
    category: str
    stimulation: int
    system_building: int
    automation_potential: int
    human_interaction: int
    repetitive: bool = False
    planned_for_week: bool = False


DEFAULT_TASKS: List[TaskTemplate] = [
    TaskTemplate(
        description="Architect autonomous prediction engine",
        category="build",
        stimulation=3,
        system_building=3,
        automation_potential=2,
        human_interaction=0,
        planned_for_week=True,
    ),
    TaskTemplate(
        description="Design experiment for controversy generator",
        category="build",
        stimulation=3,
        system_building=2,
        automation_potential=2,
        human_interaction=0,
        planned_for_week=True,
    ),
    TaskTemplate(
        description="Implement durable deployment pipeline",
        category="build",
        stimulation=2,
        system_building=3,
        automation_potential=3,
        human_interaction=0,
    ),
    TaskTemplate(
        description="Answer legacy support tickets",
        category="boring",
        stimulation=0,
        system_building=0,
        automation_potential=1,
        human_interaction=3,
        repetitive=True,
    ),
    TaskTemplate(
        description="Refactor knowledge base automation",
        category="automation",
        stimulation=2,
        system_building=2,
        automation_potential=3,
        human_interaction=0,
        planned_for_week=True,
    ),
    TaskTemplate(
        description="Document internal API",
        category="maintenance",
        stimulation=1,
        system_building=1,
        automation_potential=1,
        human_interaction=1,
        repetitive=True,
    ),
    TaskTemplate(
        description="Prototype load shedding daemon",
        category="build",
        stimulation=3,
        system_building=3,
        automation_potential=2,
        human_interaction=0,
    ),
    TaskTemplate(
        description="Evaluate user feature requests",
        category="boring",
        stimulation=0,
        system_building=0,
        automation_potential=1,
        human_interaction=2,
        repetitive=True,
    ),
]


DEFAULT_OPEN_LOOPS = [
    "Follow up with X about partnership",
    "Maybe implement Y experimental widget",
    "Should network with Z next month",
    "Ping investor about vague idea",
]


PROJECTS: Dict[str, Dict[str, object]] = {
    "ob1": {
        "repo": "github.com/tuouser/ob1",
        "priority_algorithm": lambda: "breakthrough" if random() > 0.7 else "maintain",
        "boring_tasks": ["update docs", "respond to users", "fix UI"],
        "stimulating_tasks": [
            "new algorithm",
            "prediction engine",
            "controversy generator",
        ],
    }
}


def ensure_data_dir() -> None:
    """Create the data directory if it does not exist."""

    DATA_DIR.mkdir(parents=True, exist_ok=True)


__all__ = [
    "DATA_DIR",
    "DB_PATH",
    "DEFAULT_OPEN_LOOPS",
    "DEFAULT_TASKS",
    "PROJECTS",
    "TaskTemplate",
    "ensure_data_dir",
]
