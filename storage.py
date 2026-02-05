import sqlite3
from contextlib import closing
from datetime import date, timedelta
from typing import List, Optional, Dict, Any

DB_NAME = "workHours.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_date TEXT NOT NULL,    -- YYYY-MM-DD
    start_time TEXT NOT NULL,   -- HH:MM
    end_time TEXT NOT NULL,     -- HH:MM
    lunch_minutes INTEGER NOT NULL, -- 0..?
    worked_minutes INTEGER NOT NULL -- computed and stored for performance
);
CREATE INDEX IF NOT EXISTS idx_entries_date ON entries(work_date);
"""

def _connect():
    return sqlite3.connect(DB_NAME)

def init_db():
    with closing(_connect()) as conn, conn:
        for stmt in SCHEMA.strip().split(";"):
            if stmt.strip():
                conn.execute(stmt)

def add_entry(work_date: str, start_time: str, end_time: str, lunch_minutes: int, worked_minutes: int) -> int:
    with closing(_connect()) as conn, conn:        
        cur = conn.execute(
            "INSERT INTO entries(work_date, start_time, end_time, lunch_minutes, worked_minutes) "
            "VALUES (?, ?, ?, ?, ?)",
            (work_date, start_time, end_time, lunch_minutes, worked_minutes)
        )
        return cur.lastrowid
    
def list_entries_by_date(work_date: str) -> List[Dict[str, Any]]:
    with closing(_connect()) as conn:
        cur = conn.execute(
            "SELECT id, work_date, start_time, end_time, lunch_minutes, worked_minutes "
            "FROM entries Where work_date = ? ORDER BY id ASC",
            (work_date,)
        )
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
        
def delete_entry(entry_id: int) -> int:
    with closing(_connect()) as conn, conn:
        cur = conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        return cur.rowcount
    
def edit_entry(entry_id: int, updates: Dict[str, Any]) -> int:
    # Updates can include start_time, end_time, lunch_minutes, worked_minutes
    if not updates:
        return 0
    sets = ", ".join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values()) + [entry_id]
    with closing(_connect()) as conn, conn:
        cur = conn.execute(f"UPDATE entries SET {sets} WHERE id = ?", values)
        return cur.rowcount    

def list_entries_between(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    with closing(_connect()) as conn:
        cur = conn.execute(
            "SELECT id, work_date, start_time, end_time, lunch_minutes, worked_minutes "
            "FROM entries WHERE work_date BETWEEN ? AND ? ORDER BY work_date ASC, id ASC",
            (start_date, end_date)
        )
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]