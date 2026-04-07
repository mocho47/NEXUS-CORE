"""
NEXUS v3 - Utilidades de base de datos SQLite
Desarrollado por Simplex
"""

import logging
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

import aiosqlite

# Configuracion del logger
logger = logging.getLogger("nexus.database")

# Ruta activa — se fija en init_db() y la usan todas las funciones
_DB_PATH = "nexus.db"


def _db() -> str:
    return _DB_PATH


# --- Definiciones de tablas SQL ---

SQL_CREATE_SESSIONS = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    personality TEXT NOT NULL DEFAULT 'nexus',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

SQL_CREATE_MESSAGES = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);
"""

SQL_CREATE_USER_MEMORY = """
CREATE TABLE IF NOT EXISTS user_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'preference' CHECK(category IN ('personal', 'business', 'preference', 'habit')),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

SQL_CREATE_CLIENTS = """
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    business TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

SQL_CREATE_PRODUCTS = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business TEXT NOT NULL CHECK(business IN ('atf', 'milens', 'canbusfix')),
    name TEXT NOT NULL,
    price REAL DEFAULT 0.0,
    description TEXT,
    stock INTEGER DEFAULT 0
);
"""

SQL_CREATE_ORDERS = """
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    business TEXT NOT NULL,
    items_json TEXT NOT NULL,
    total REAL NOT NULL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);
"""

SQL_CREATE_MISSIONS = """
CREATE TABLE IF NOT EXISTS missions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    points INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',
    assigned_to TEXT,
    created_by TEXT,
    due_date TIMESTAMP,
    evidence TEXT,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

SQL_CREATE_MOTOR_STATUS = """
CREATE TABLE IF NOT EXISTS motor_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    motor_name TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'detenido',
    last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uptime_seconds INTEGER DEFAULT 0,
    tasks_completed INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0
);
"""

SQL_CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, timestamp);",
    "CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);",
    "CREATE INDEX IF NOT EXISTS idx_user_memory_category ON user_memory(category);",
    "CREATE INDEX IF NOT EXISTS idx_clients_business ON clients(business);",
    "CREATE INDEX IF NOT EXISTS idx_products_business ON products(business);",
    "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);",
    "CREATE INDEX IF NOT EXISTS idx_orders_client ON orders(client_id);",
    "CREATE INDEX IF NOT EXISTS idx_missions_status ON missions(status);",
    "CREATE INDEX IF NOT EXISTS idx_motor_status_name ON motor_status(motor_name);",
]

TODAS_LAS_TABLAS = [
    SQL_CREATE_SESSIONS,
    SQL_CREATE_MESSAGES,
    SQL_CREATE_USER_MEMORY,
    SQL_CREATE_CLIENTS,
    SQL_CREATE_PRODUCTS,
    SQL_CREATE_ORDERS,
    SQL_CREATE_MISSIONS,
    SQL_CREATE_MOTOR_STATUS,
]


async def init_db(db_path: str = "nexus.db") -> bool:
    """Inicializa la base de datos y guarda la ruta globalmente."""
    global _DB_PATH
    _DB_PATH = db_path
    logger.info("Iniciando base de datos en: %s", db_path)
    try:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA foreign_keys=ON;")
            await db.execute("PRAGMA busy_timeout=5000;")
            for sql in TODAS_LAS_TABLAS:
                await db.execute(sql)
            for sql in SQL_CREATE_INDEXES:
                await db.execute(sql)
            await db.commit()
        logger.info("Base de datos inicializada correctamente con %d tablas.", len(TODAS_LAS_TABLAS))
        return True
    except Exception as e:
        logger.error("Error inicializando DB: %s", e)
        return False


async def get_session_messages(session_id: int, limit: int = 30) -> list[dict]:
    try:
        async with aiosqlite.connect(_db()) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp ASC LIMIT ?",
                (session_id, limit)
            )
            return [dict(row) for row in await cursor.fetchall()]
    except Exception as e:
        logger.error("Error obteniendo mensajes: %s", e)
        return []


async def save_message(session_id: int, role: str, content: str) -> Optional[int]:
    try:
        async with aiosqlite.connect(_db()) as db:
            cursor = await db.execute(
                "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
                (session_id, role, content)
            )
            await db.commit()
            return cursor.lastrowid
    except Exception as e:
        logger.error("Error guardando mensaje: %s", e)
        return None


async def update_motor_status(motor_name: str, status: str, **kwargs) -> bool:
    try:
        async with aiosqlite.connect(_db()) as db:
            await db.execute(
                "INSERT INTO motor_status (motor_name, status, uptime_seconds, tasks_completed, errors_count) "
                "VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT(motor_name) DO UPDATE SET "
                "status = excluded.status, "
                "last_check = CURRENT_TIMESTAMP, "
                "uptime_seconds = excluded.uptime_seconds, "
                "tasks_completed = excluded.tasks_completed, "
                "errors_count = excluded.errors_count",
                (
                    motor_name,
                    status,
                    kwargs.get("uptime_seconds", 0),
                    kwargs.get("tasks_completed", 0),
                    kwargs.get("errors_count", 0),
                )
            )
            await db.commit()
            return True
    except Exception as e:
        logger.error("Error actualizando estado motor %s: %s", motor_name, e)
        return False


async def get_motor_status(motor_name: str) -> Optional[dict]:
    try:
        async with aiosqlite.connect(_db()) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM motor_status WHERE motor_name = ?", (motor_name,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    except Exception:
        return None


async def get_user_memory(key: Optional[str] = None, category: Optional[str] = None) -> list[dict]:
    try:
        async with aiosqlite.connect(_db()) as db:
            db.row_factory = aiosqlite.Row
            if key:
                cursor = await db.execute("SELECT * FROM user_memory WHERE key = ?", (key,))
            elif category:
                cursor = await db.execute("SELECT * FROM user_memory WHERE category = ?", (category,))
            else:
                cursor = await db.execute("SELECT * FROM user_memory ORDER BY updated_at DESC")
            return [dict(row) for row in await cursor.fetchall()]
    except Exception as e:
        logger.error("Error obteniendo memoria: %s", e)
        return []


async def save_user_memory(key: str, value: str, category: str = "preference") -> bool:
    try:
        async with aiosqlite.connect(_db()) as db:
            await db.execute(
                "INSERT INTO user_memory (key, value, category) VALUES (?, ?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value, "
                "category = excluded.category, updated_at = CURRENT_TIMESTAMP",
                (key, value, category)
            )
            await db.commit()
            return True
    except Exception as e:
        logger.error("Error guardando memoria: %s", e)
        return False


async def get_all_clients(business: Optional[str] = None) -> list[dict]:
    try:
        async with aiosqlite.connect(_db()) as db:
            db.row_factory = aiosqlite.Row
            if business:
                cursor = await db.execute("SELECT * FROM clients WHERE business = ? ORDER BY name", (business,))
            else:
                cursor = await db.execute("SELECT * FROM clients ORDER BY name")
            return [dict(row) for row in await cursor.fetchall()]
    except Exception as e:
        logger.error("Error obteniendo clientes: %s", e)
        return []


async def save_client(data: dict) -> Optional[int]:
    try:
        async with aiosqlite.connect(_db()) as db:
            cursor = await db.execute(
                "INSERT INTO clients (name, phone, email, business, notes) VALUES (?, ?, ?, ?, ?)",
                (data.get("name", ""), data.get("phone"), data.get("email"),
                 data.get("business"), data.get("notes"))
            )
            await db.commit()
            return cursor.lastrowid
    except Exception as e:
        logger.error("Error guardando cliente: %s", e)
        return None


async def get_products(business: Optional[str] = None) -> list[dict]:
    try:
        async with aiosqlite.connect(_db()) as db:
            db.row_factory = aiosqlite.Row
            if business:
                cursor = await db.execute("SELECT * FROM products WHERE business = ?", (business,))
            else:
                cursor = await db.execute("SELECT * FROM products")
            return [dict(row) for row in await cursor.fetchall()]
    except Exception as e:
        logger.error("Error obteniendo productos: %s", e)
        return []


async def get_orders(status: Optional[str] = None, limit: int = 50) -> list[dict]:
    try:
        async with aiosqlite.connect(_db()) as db:
            db.row_factory = aiosqlite.Row
            if status:
                cursor = await db.execute(
                    "SELECT * FROM orders WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                    (status, limit)
                )
            else:
                cursor = await db.execute(
                    "SELECT * FROM orders ORDER BY created_at DESC LIMIT ?", (limit,)
                )
            return [dict(row) for row in await cursor.fetchall()]
    except Exception as e:
        logger.error("Error obteniendo pedidos: %s", e)
        return []


async def search_user_memory(query: str) -> list[dict]:
    """Busca en user_memory por coincidencia en key o value."""
    try:
        async with aiosqlite.connect(_db()) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM user_memory WHERE key LIKE ? OR value LIKE ? ORDER BY updated_at DESC",
                (f"%{query}%", f"%{query}%")
            )
            return [dict(row) for row in await cursor.fetchall()]
    except Exception as e:
        logger.error("Error buscando memoria: %s", e)
        return []


def backup_db(db_path: str, backup_dir: str) -> dict:
    try:
        Path(backup_dir).mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = Path(backup_dir) / f"nexus_backup_{ts}.db"
        shutil.copy2(db_path, dest)
        return {"ok": True, "backup": str(dest)}
    except Exception as e:
        return {"ok": False, "error": str(e)}
