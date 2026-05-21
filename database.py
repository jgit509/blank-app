"""
database.py — SQLite database layer for Land Tracker
Handles all CRUD operations for properties, subtasks, team members, and conversation logs.
"""

import sqlite3
import os
from datetime import datetime, date
from typing import Optional

DB_PATH = "land_tracker.db"


def get_connection():
    """Get a database connection with row_factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initialize all database tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # ── Properties (Parent Tasks) ──────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address TEXT NOT NULL,
            url TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            action_item TEXT DEFAULT '',
            status TEXT DEFAULT 'New Lead',
            priority TEXT DEFAULT 'Warm',
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed INTEGER DEFAULT 0,
            completed_date TIMESTAMP NULL,
            archived INTEGER DEFAULT 0
        )
    """)

    # ── Subtasks (Nested under Properties) ─────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subtasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            assigned_to TEXT DEFAULT '',
            priority TEXT DEFAULT 'Medium',
            due_date DATE NULL,
            done INTEGER DEFAULT 0,
            completed_date TIMESTAMP NULL,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by TEXT DEFAULT 'Owner',
            notes TEXT DEFAULT '',
            FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
        )
    """)

    # ── Team Members ───────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS team (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            email TEXT DEFAULT '',
            role TEXT DEFAULT 'Team Member'
        )
    """)

    # ── Conversation Log ───────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            author TEXT DEFAULT 'Owner',
            message TEXT NOT NULL,
            FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


# ================================================================
# PROPERTIES (Parent Tasks)
# ================================================================

def add_property(address: str, url: str = "", notes: str = "",
                 action_item: str = "", status: str = "New Lead",
                 priority: str = "Warm") -> int:
    """Add a new property and return its ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO properties (address, url, notes, action_item, status, priority)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (address, url, notes, action_item, status, priority))
    prop_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return prop_id


def update_property(prop_id: int, **kwargs):
    """Update any property fields by keyword arguments."""
    conn = get_connection()
    cursor = conn.cursor()
    allowed = ["address", "url", "notes", "action_item", "status",
               "priority", "completed", "completed_date", "archived"]
    sets = []
    vals = []
    for key, val in kwargs.items():
        if key in allowed:
            sets.append(f"{key} = ?")
            vals.append(val)
    if sets:
        vals.append(prop_id)
        cursor.execute(
            f"UPDATE properties SET {', '.join(sets)} WHERE id = ?", vals
        )
        conn.commit()
    conn.close()


def delete_property(prop_id: int):
    """Delete a property and all its subtasks/logs (cascade)."""
    conn = get_connection()
    conn.execute("DELETE FROM properties WHERE id = ?", (prop_id,))
    conn.commit()
    conn.close()


def get_all_properties(include_archived: bool = False) -> list:
    """Get all properties as list of dicts."""
    conn = get_connection()
    if include_archived:
        rows = conn.execute(
            "SELECT * FROM properties ORDER BY date_added DESC"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM properties WHERE archived = 0 ORDER BY date_added DESC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_property(prop_id: int) -> Optional[dict]:
    """Get a single property by ID."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM properties WHERE id = ?", (prop_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def toggle_property_complete(prop_id: int):
    """Toggle the completed status of a property."""
    prop = get_property(prop_id)
    if prop:
        new_status = 0 if prop["completed"] else 1
        completed_date = datetime.now().isoformat() if new_status else None
        update_property(
            prop_id,
            completed=new_status,
            completed_date=completed_date
        )


# ================================================================
# SUBTASKS (Nested under Properties)
# ================================================================

def add_subtask(property_id: int, description: str,
                assigned_to: str = "", priority: str = "Medium",
                due_date: Optional[str] = None, created_by: str = "Owner",
                notes: str = "") -> int:
    """Add a subtask under a property."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO subtasks
            (property_id, description, assigned_to, priority,
             due_date, created_by, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (property_id, description, assigned_to, priority,
          due_date, created_by, notes))
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return task_id


def update_subtask(task_id: int, **kwargs):
    """Update any subtask fields."""
    conn = get_connection()
    cursor = conn.cursor()
    allowed = ["description", "assigned_to", "priority", "due_date",
               "done", "completed_date", "notes"]
    sets = []
    vals = []
    for key, val in kwargs.items():
        if key in allowed:
            sets.append(f"{key} = ?")
            vals.append(val)
    if sets:
        vals.append(task_id)
        cursor.execute(
            f"UPDATE subtasks SET {', '.join(sets)} WHERE id = ?", vals
        )
        conn.commit()
    conn.close()


def delete_subtask(task_id: int):
    """Delete a subtask."""
    conn = get_connection()
    conn.execute("DELETE FROM subtasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def get_subtasks(property_id: int) -> list:
    """Get all subtasks for a property."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM subtasks
        WHERE property_id = ?
        ORDER BY done ASC, priority DESC, created_date DESC
    """, (property_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_subtasks() -> list:
    """Get all subtasks across all properties."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT s.*, p.address as property_address
        FROM subtasks s
        JOIN properties p ON s.property_id = p.id
        WHERE p.archived = 0
        ORDER BY s.done ASC, s.due_date ASC NULLS LAST, s.priority DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def toggle_subtask(task_id: int):
    """Toggle a subtask's done status."""
    conn = get_connection()
    row = conn.execute(
        "SELECT done FROM subtasks WHERE id = ?", (task_id,)
    ).fetchone()
    if row:
        new_done = 0 if row["done"] else 1
        completed_date = datetime.now().isoformat() if new_done else None
        conn.execute("""
            UPDATE subtasks SET done = ?, completed_date = ? WHERE id = ?
        """, (new_done, completed_date, task_id))
        conn.commit()
    conn.close()


def get_upcoming_tasks(days: int = 7) -> list:
    """Get subtasks due within the next N days."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT s.*, p.address as property_address
        FROM subtasks s
        JOIN properties p ON s.property_id = p.id
        WHERE s.done = 0
          AND s.due_date IS NOT NULL
          AND s.due_date != ''
          AND s.due_date <= date('now', '+' || ? || ' days')
          AND p.archived = 0
        ORDER BY s.due_date ASC
    """, (days,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_completed_tasks(limit: int = 50) -> list:
    """Get recently completed subtasks."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT s.*, p.address as property_address
        FROM subtasks s
        JOIN properties p ON s.property_id = p.id
        WHERE s.done = 1
        ORDER BY s.completed_date DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ================================================================
# TEAM MEMBERS
# ================================================================

def add_team_member(name: str, email: str = "", role: str = "Team Member"):
    """Add a team member."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO team (name, email, role) VALUES (?, ?, ?)",
            (name, email, role)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Name already exists
    conn.close()


def get_team_members() -> list:
    """Get all team members."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM team ORDER BY role, name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_team_member(member_id: int):
    """Delete a team member."""
    conn = get_connection()
    conn.execute("DELETE FROM team WHERE id = ?", (member_id,))
    conn.commit()
    conn.close()


def get_team_names() -> list:
    """Get just the names for dropdowns."""
    members = get_team_members()
    return [m["name"] for m in members]


# ================================================================
# CONVERSATION LOG
# ================================================================

def add_log_entry(property_id: int, message: str, author: str = "Owner"):
    """Add a conversation log entry."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO conversation_log (property_id, message, author)
        VALUES (?, ?, ?)
    """, (property_id, message, author))
    conn.commit()
    conn.close()


def get_log_entries(property_id: int) -> list:
    """Get all log entries for a property, newest first."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM conversation_log
        WHERE property_id = ?
        ORDER BY timestamp DESC
    """, (property_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ================================================================
# STATS
# ================================================================

def get_stats() -> dict:
    """Get summary statistics."""
    conn = get_connection()

    total = conn.execute(
        "SELECT COUNT(*) as c FROM properties WHERE archived = 0"
    ).fetchone()["c"]

    by_status = conn.execute("""
        SELECT status, COUNT(*) as count
        FROM properties WHERE archived = 0
        GROUP BY status ORDER BY count DESC
    """).fetchall()

    open_tasks = conn.execute(
        "SELECT COUNT(*) as c FROM subtasks s "
        "JOIN properties p ON s.property_id = p.id "
        "WHERE s.done = 0 AND p.archived = 0"
    ).fetchone()["c"]

    done_tasks = conn.execute(
        "SELECT COUNT(*) as c FROM subtasks s "
        "JOIN properties p ON s.property_id = p.id "
        "WHERE s.done = 1 AND p.archived = 0"
    ).fetchone()["c"]

    by_priority = conn.execute("""
        SELECT priority, COUNT(*) as count
        FROM properties WHERE archived = 0
        GROUP BY priority
    """).fetchall()

    overdue = conn.execute("""
        SELECT COUNT(*) as c FROM subtasks s
        JOIN properties p ON s.property_id = p.id
        WHERE s.done = 0
          AND s.due_date IS NOT NULL
          AND s.due_date != ''
          AND s.due_date < date('now')
          AND p.archived = 0
    """).fetchone()["c"]

    by_assignee = conn.execute("""
        SELECT assigned_to, COUNT(*) as count
        FROM subtasks s
        JOIN properties p ON s.property_id = p.id
        WHERE s.done = 0 AND s.assigned_to != '' AND p.archived = 0
        GROUP BY assigned_to ORDER BY count DESC
    """).fetchall()

    conn.close()

    return {
        "total_properties": total,
        "by_status": [dict(r) for r in by_status],
        "open_tasks": open_tasks,
        "done_tasks": done_tasks,
        "by_priority": [dict(r) for r in by_priority],
        "overdue_tasks": overdue,
        "by_assignee": [dict(r) for r in by_assignee],
    }
