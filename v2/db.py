# -*- coding: utf-8 -*-
"""
NEXUS v2 — Capa de datos
SQLite local. Simple, sin magia, sin ORM pesado.
"""
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("C:/nexus/nexus_v2.db")

def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    return c

def init_db():
    with _conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS clientes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre      TEXT NOT NULL,
            telefono    TEXT,
            email       TEXT,
            empresa     TEXT,
            notas       TEXT,
            created_at  TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS pedidos (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id      INTEGER REFERENCES clientes(id),
            cliente_nombre  TEXT,
            descripcion     TEXT NOT NULL,
            servicio        TEXT,
            precio          REAL,
            estado          TEXT DEFAULT 'pendiente',
            fecha_entrega   TEXT,
            notas           TEXT,
            created_at      TEXT DEFAULT (datetime('now','localtime')),
            updated_at      TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS agenda_atf (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente     TEXT NOT NULL,
            telefono    TEXT,
            modelo_kit  TEXT,
            carro       TEXT,
            fecha       TEXT,
            hora        TEXT,
            estado      TEXT DEFAULT 'agendado',
            notas       TEXT,
            created_at  TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS pipeline (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente     TEXT NOT NULL,
            telefono    TEXT,
            servicio    TEXT,
            valor       REAL,
            estado      TEXT DEFAULT 'prospecto',
            notas       TEXT,
            updated_at  TEXT DEFAULT (datetime('now','localtime')),
            created_at  TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS instaladores_canbusfix (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre          TEXT NOT NULL,
            ciudad          TEXT,
            telefono        TEXT,
            especialidades  TEXT,
            activo          INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS proveedores (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre          TEXT NOT NULL,
            empresa         TEXT,
            telefono        TEXT,
            categoria       TEXT,
            productos       TEXT,
            precio_notas    TEXT,
            tiempo_entrega  TEXT,
            condiciones     TEXT,
            activo          INTEGER DEFAULT 1,
            created_at      TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS usuarios (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre      TEXT NOT NULL,
            rol         TEXT DEFAULT 'operadora',
            pin         TEXT NOT NULL,
            activo      INTEGER DEFAULT 1,
            created_at  TEXT DEFAULT (datetime('now','localtime'))
        );
        """)
    # Migrar tablas existentes si les falta creado_por
    try:
        c.execute("ALTER TABLE pedidos ADD COLUMN creado_por TEXT DEFAULT ''")
    except Exception: pass
    try:
        c.execute("ALTER TABLE agenda_atf ADD COLUMN creado_por TEXT DEFAULT ''")
    except Exception: pass
    # Usuarios iniciales si no existen
    with _conn() as c:
        if not c.execute("SELECT 1 FROM usuarios LIMIT 1").fetchone():
            c.executemany(
                "INSERT INTO usuarios (nombre, rol, pin) VALUES (?,?,?)",
                [("Anuar", "admin", "1111"), ("Rocio Hermosa", "operadora", "2222")]
            )
    return True

# ── Helpers ────────────────────────────────────────────────────────────────────
def row_to_dict(row) -> dict:
    return dict(row) if row else {}

def rows_to_list(rows) -> list:
    return [dict(r) for r in rows]

def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")

init_db()
