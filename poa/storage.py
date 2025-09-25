"""SQLite-backed storage for the Personal Operations Assistant."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterator, List, Optional

from .config import DB_PATH, DEFAULT_OPEN_LOOPS, DEFAULT_TASKS, ensure_data_dir


@contextmanager
def get_connection(db_path: Path = DB_PATH) -> Iterator[sqlite3.Connection]:
    """Yield a SQLite connection with foreign keys enabled."""

    ensure_data_dir()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()


def setup_database(db_path: Path = DB_PATH) -> None:
    """Initialize the database schema."""

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                stimulation INTEGER NOT NULL,
                system_building INTEGER NOT NULL,
                automation_potential INTEGER NOT NULL,
                human_interaction INTEGER NOT NULL,
                repetitive INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'pending',
                planned_for_week INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS tasks_updated_at
            AFTER UPDATE ON tasks
            FOR EACH ROW
            BEGIN
                UPDATE tasks SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
            END;
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event TEXT NOT NULL,
                details TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS focus_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                summary TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS energy_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level INTEGER NOT NULL,
                note TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS open_loops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def seed_defaults(db_path: Path = DB_PATH) -> None:
    """Seed the database with defaults if empty."""

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tasks")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                """
                INSERT INTO tasks (
                    description,
                    category,
                    stimulation,
                    system_building,
                    automation_potential,
                    human_interaction,
                    repetitive,
                    planned_for_week
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        task.description,
                        task.category,
                        task.stimulation,
                        task.system_building,
                        task.automation_potential,
                        task.human_interaction,
                        1 if task.repetitive else 0,
                        1 if task.planned_for_week else 0,
                    )
                    for task in DEFAULT_TASKS
                ],
            )
        cursor.execute("SELECT COUNT(*) FROM open_loops")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO open_loops (description) VALUES (?)",
                [(loop,) for loop in DEFAULT_OPEN_LOOPS],
            )


def record_activity(event: str, details: Optional[Dict[str, object]] = None) -> None:
    """Record an activity log entry."""

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO activity_log (event, details) VALUES (?, ?)",
            (event, json.dumps(details or {})),
        )


def add_focus_session(duration_minutes: int, summary: str) -> None:
    """Store a focus session record."""

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO focus_sessions (started_at, duration_minutes, summary) VALUES (?, ?, ?)",
            (datetime.utcnow().isoformat(), duration_minutes, summary),
        )


def last_focus_session(within_hours: int = 24) -> Optional[sqlite3.Row]:
    """Return the most recent focus session within the provided window."""

    cutoff = datetime.utcnow() - timedelta(hours=within_hours)
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM focus_sessions WHERE started_at >= ? ORDER BY started_at DESC LIMIT 1",
            (cutoff.isoformat(),),
        )
        return cursor.fetchone()


def log_energy(level: int, note: str) -> None:
    """Insert an energy log entry."""

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO energy_events (level, note) VALUES (?, ?)",
            (level, note),
        )


def fetch_recent_energy(hours: int = 6) -> List[sqlite3.Row]:
    """Return recent energy events."""

    cutoff = datetime.utcnow() - timedelta(hours=hours)
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM energy_events WHERE created_at >= ? ORDER BY created_at DESC",
            (cutoff.isoformat(),),
        )
        return list(cursor.fetchall())


def fetch_tasks(order_by_priority: bool = True) -> List[sqlite3.Row]:
    """Fetch tasks, optionally ordered by the priority algorithm."""

    with get_connection() as conn:
        cursor = conn.cursor()
        if order_by_priority:
            cursor.execute(
                """
                SELECT *, (
                    stimulation * 3 +
                    system_building * 2 +
                    automation_potential * 2 -
                    human_interaction * 5
                ) AS priority
                FROM tasks
                ORDER BY priority DESC
                """
            )
        else:
            cursor.execute("SELECT * FROM tasks")
        return list(cursor.fetchall())


def fetch_planned_tasks() -> List[sqlite3.Row]:
    """Return tasks flagged as planned for the week."""

    with get_connection() as conn:
        cursor = conn.execute("SELECT * FROM tasks WHERE planned_for_week = 1")
        return list(cursor.fetchall())


def fetch_open_loops() -> List[sqlite3.Row]:
    """Return open loops that are still active."""

    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM open_loops WHERE status = 'open' ORDER BY created_at DESC"
        )
        return list(cursor.fetchall())


def close_open_loop(loop_id: int, reason: str) -> None:
    """Close an open loop with a blunt reason."""

    with get_connection() as conn:
        conn.execute(
            "UPDATE open_loops SET status = ?, description = description || ' → ' || ? WHERE id = ?",
            ("closed", reason, loop_id),
        )


def delete_open_loop(loop_id: int) -> None:
    """Delete an open loop entirely."""

    with get_connection() as conn:
        conn.execute("DELETE FROM open_loops WHERE id = ?", (loop_id,))


def reopen_open_loop(loop_id: int) -> None:
    """Reopen a previously closed loop."""

    with get_connection() as conn:
        conn.execute("UPDATE open_loops SET status = 'open' WHERE id = ?", (loop_id,))


def update_task_status(task_id: int, status: str) -> None:
    """Update the status for a task."""

    with get_connection() as conn:
        conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))


__all__ = [
    "add_focus_session",
    "close_open_loop",
    "delete_open_loop",
    "fetch_open_loops",
    "fetch_planned_tasks",
    "fetch_recent_energy",
    "fetch_tasks",
    "get_connection",
    "last_focus_session",
    "log_energy",
    "record_activity",
    "reopen_open_loop",
    "seed_defaults",
    "setup_database",
    "update_task_status",
]
