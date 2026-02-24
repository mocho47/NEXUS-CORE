import os
import re
import sqlite3
import time
from typing import Any, Dict, List, Optional, Tuple


def _now() -> float:
    return time.time()


def _norm(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


class NexusMemory:
    """Memoria local (privada) basada en SQLite.

    Guarda:
    - notas (lo que el usuario quiere que Nexus recuerde)
    - tareas (pendientes / hechas)
    - interacciones (resumen para contexto; no imprime secretos)

    Todo se queda en el disco local, dentro de CONFIG/.
    """

    def __init__(self, config_dir: str, db_name: str = "nexus_memory.db"):
        self.config_dir = os.path.abspath(config_dir)
        os.makedirs(self.config_dir, exist_ok=True)
        self.db_path = os.path.join(self.config_dir, db_name)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path)
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute("PRAGMA synchronous=NORMAL;")
        return con

    def _init_db(self) -> None:
        con = self._connect()
        try:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    kind TEXT NOT NULL,
                    text TEXT NOT NULL,
                    tags TEXT
                );
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_ts REAL NOT NULL,
                    title TEXT NOT NULL,
                    details TEXT,
                    status TEXT NOT NULL,
                    due_ts REAL
                );
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL
                );
                """
            )
            con.commit()
        finally:
            con.close()

    # ---------------- Notes ----------------
    def add_note(self, text: str, kind: str = "note", tags: Optional[str] = None) -> int:
        text = (text or "").strip()
        if not text:
            return 0
        con = self._connect()
        try:
            cur = con.execute(
                "INSERT INTO notes(ts, kind, text, tags) VALUES(?, ?, ?, ?)",
                (_now(), str(kind), text, tags),
            )
            con.commit()
            return int(cur.lastrowid or 0)
        finally:
            con.close()

    def search_notes(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        q = _norm(query)
        if not q:
            return []
        con = self._connect()
        try:
            cur = con.execute(
                "SELECT id, ts, kind, text, tags FROM notes WHERE lower(text) LIKE ? ORDER BY ts DESC LIMIT ?",
                (f"%{q}%", int(limit)),
            )
            out = []
            for row in cur.fetchall():
                out.append({"id": row[0], "ts": row[1], "kind": row[2], "text": row[3], "tags": row[4]})
            return out
        finally:
            con.close()

    def recent_notes(self, limit: int = 5) -> List[Dict[str, Any]]:
        con = self._connect()
        try:
            cur = con.execute(
                "SELECT id, ts, kind, text, tags FROM notes ORDER BY ts DESC LIMIT ?",
                (int(limit),),
            )
            return [
                {"id": r[0], "ts": r[1], "kind": r[2], "text": r[3], "tags": r[4]}
                for r in cur.fetchall()
            ]
        finally:
            con.close()

    # ---------------- Tasks ----------------
    def add_task(self, title: str, details: str = "", due_ts: Optional[float] = None) -> int:
        title = (title or "").strip()
        if not title:
            return 0
        con = self._connect()
        try:
            cur = con.execute(
                "INSERT INTO tasks(created_ts, title, details, status, due_ts) VALUES(?, ?, ?, ?, ?)",
                (_now(), title, details, "todo", due_ts),
            )
            con.commit()
            return int(cur.lastrowid or 0)
        finally:
            con.close()

    def list_tasks(self, status: str = "todo", limit: int = 10) -> List[Dict[str, Any]]:
        con = self._connect()
        try:
            cur = con.execute(
                "SELECT id, created_ts, title, details, status, due_ts FROM tasks WHERE status=? ORDER BY created_ts DESC LIMIT ?",
                (status, int(limit)),
            )
            out = []
            for r in cur.fetchall():
                out.append({"id": r[0], "created_ts": r[1], "title": r[2], "details": r[3], "status": r[4], "due_ts": r[5]})
            return out
        finally:
            con.close()

    def set_task_status(self, task_id: int, status: str) -> bool:
        con = self._connect()
        try:
            con.execute("UPDATE tasks SET status=? WHERE id=?", (status, int(task_id)))
            con.commit()
            return True
        except Exception:
            return False
        finally:
            con.close()

    # ---------------- Interactions ----------------
    def log_interaction(self, role: str, content: str, max_len: int = 1200) -> None:
        role = str(role or "").strip() or "user"
        content = (content or "").strip()
        if not content:
            return
        if len(content) > max_len:
            content = content[:max_len] + "…"
        con = self._connect()
        try:
            con.execute("INSERT INTO interactions(ts, role, content) VALUES(?, ?, ?)", (_now(), role, content))
            # Mantener tabla acotada
            con.execute(
                "DELETE FROM interactions WHERE id NOT IN (SELECT id FROM interactions ORDER BY ts DESC LIMIT 400)"
            )
            con.commit()
        finally:
            con.close()

    def recent_interactions(self, limit: int = 12) -> List[Tuple[str, str]]:
        con = self._connect()
        try:
            cur = con.execute(
                "SELECT role, content FROM interactions ORDER BY ts DESC LIMIT ?",
                (int(limit),),
            )
            rows = cur.fetchall()
            rows.reverse()
            return [(r[0], r[1]) for r in rows]
        finally:
            con.close()

    # ---------------- Sleep / Consolidation ----------------
    def dream(self) -> Dict[str, Any]:
        """Consolidación simple (offline). No usa IA nube.

        Devuelve un resumen con:
        - tareas pendientes
        - últimas notas
        """
        todos = self.list_tasks(status="todo", limit=10)
        last_notes = self.recent_notes(limit=5)
        return {"todos": todos, "notes": last_notes, "ts": _now()}
