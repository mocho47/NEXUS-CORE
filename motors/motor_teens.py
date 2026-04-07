"""
motors/motor_teens.py — NEXUS v3 by Simplex
Motor NEXUS Teens — misiones familiares — puerto 8005
Generado por Z.ai
"""
import os
import time
import uuid
import aiosqlite
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.notificaciones import notificar, event_generator, subscribe_sse

app = FastAPI(title="NEXUS Teens Motor", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(os.path.dirname(__file__)), "output", "nexus_v3.db"))


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS misiones (
                id TEXT PRIMARY KEY,
                familia_id TEXT NOT NULL,
                titulo TEXT NOT NULL,
                descripcion TEXT,
                puntos INTEGER DEFAULT 10,
                asignado_a TEXT,
                estado TEXT DEFAULT 'pendiente',
                evidencia_url TEXT,
                aprobado_por TEXT,
                creado REAL,
                completado REAL,
                aprobado REAL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS familias (
                id TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                codigo_beta TEXT UNIQUE,
                creado REAL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS miembros (
                id TEXT PRIMARY KEY,
                familia_id TEXT NOT NULL,
                nombre TEXT NOT NULL,
                rol TEXT NOT NULL,
                pin_hash TEXT,
                puntos_total INTEGER DEFAULT 0,
                activo INTEGER DEFAULT 1,
                creado REAL
            )
        """)
        await db.commit()


@app.on_event("startup")
async def startup():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    await init_db()


# ─── Models ───────────────────────────────────────────────────────────────────

class MisionCreate(BaseModel):
    familia_id: str
    titulo: str
    descripcion: Optional[str] = None
    puntos: int = 10
    asignado_a: Optional[str] = None


class CompletarMision(BaseModel):
    evidencia_url: Optional[str] = None
    comentario: Optional[str] = None


class AprobarMision(BaseModel):
    aprobado_por: str
    pin_padre: str
    familia_id: str


# ─── Endpoints misiones ───────────────────────────────────────────────────────

@app.post("/teens/misiones")
async def crear_mision(req: MisionCreate):
    """Crea una nueva misión familiar."""
    mid = str(uuid.uuid4())[:8]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO misiones VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (mid, req.familia_id, req.titulo, req.descripcion, req.puntos,
             req.asignado_a, "pendiente", None, None, time.time(), None, None)
        )
        await db.commit()

    await notificar("mision_creada", {
        "id": mid,
        "titulo": req.titulo,
        "puntos": req.puntos
    }, canal=f"familia_{req.familia_id}")

    return {"ok": True, "id": mid, "mensaje": f"Misión '{req.titulo}' creada ({req.puntos} pts)"}


@app.get("/teens/misiones/{familia_id}")
async def listar_misiones(familia_id: str, estado: str = None):
    """Lista misiones de una familia."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if estado:
            cur = await db.execute(
                "SELECT * FROM misiones WHERE familia_id=? AND estado=? ORDER BY creado DESC",
                (familia_id, estado)
            )
        else:
            cur = await db.execute(
                "SELECT * FROM misiones WHERE familia_id=? ORDER BY creado DESC",
                (familia_id,)
            )
        rows = await cur.fetchall()

    return {"ok": True, "misiones": [dict(r) for r in rows], "total": len(rows)}


@app.put("/teens/misiones/{mid}/completar")
async def completar_mision(mid: str, req: CompletarMision):
    """Teen marca misión como completada (requiere aprobación padre)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM misiones WHERE id=?", (mid,))
        mision = await cur.fetchone()
        if not mision:
            raise HTTPException(status_code=404, detail="Misión no encontrada")
        if dict(mision)["estado"] != "pendiente":
            raise HTTPException(status_code=400, detail="La misión no está pendiente")

        await db.execute(
            "UPDATE misiones SET estado='completada', evidencia_url=?, completado=? WHERE id=?",
            (req.evidencia_url, time.time(), mid)
        )
        await db.commit()

    # Notificar al padre
    familia_id = dict(mision)["familia_id"]
    await notificar("mision_completada", {
        "id": mid,
        "titulo": dict(mision)["titulo"],
        "por": dict(mision)["asignado_a"]
    }, canal=f"familia_{familia_id}")

    return {"ok": True, "mensaje": "Misión completada, esperando aprobación del padre"}


@app.put("/teens/misiones/{mid}/aprobar")
async def aprobar_mision(mid: str, req: AprobarMision):
    """Padre aprueba misión y asigna puntos."""
    import hashlib
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM misiones WHERE id=?", (mid,))
        mision = await cur.fetchone()
        if not mision:
            raise HTTPException(status_code=404, detail="Misión no encontrada")
        if dict(mision)["estado"] != "completada":
            raise HTTPException(status_code=400, detail="La misión no ha sido completada aún")

        # Verificar PIN padre (simple hash)
        pin_hash = hashlib.sha256(req.pin_padre.encode()).hexdigest()
        cur2 = await db.execute(
            "SELECT * FROM miembros WHERE familia_id=? AND rol IN ('padre','mama') AND pin_hash=?",
            (req.familia_id, pin_hash)
        )
        padre = await cur2.fetchone()
        if not padre:
            raise HTTPException(status_code=401, detail="PIN del padre incorrecto")

        # Aprobar y dar puntos
        await db.execute(
            "UPDATE misiones SET estado='aprobada', aprobado_por=?, aprobado=? WHERE id=?",
            (req.aprobado_por, time.time(), mid)
        )
        # Sumar puntos al teen
        teen_id = dict(mision)["asignado_a"]
        puntos = dict(mision)["puntos"]
        if teen_id:
            await db.execute(
                "UPDATE miembros SET puntos_total=puntos_total+? WHERE id=?",
                (puntos, teen_id)
            )
        await db.commit()

    await notificar("mision_aprobada", {
        "id": mid,
        "puntos_ganados": dict(mision)["puntos"]
    }, canal=f"familia_{req.familia_id}")

    return {"ok": True, "puntos_asignados": dict(mision)["puntos"], "mensaje": "Misión aprobada"}


@app.get("/teens/eventos/{familia_id}")
async def eventos_sse(familia_id: str):
    """Stream SSE de eventos para una familia."""
    cliente_id = f"familia_{familia_id}_{str(uuid.uuid4())[:4]}"
    return StreamingResponse(
        event_generator(cliente_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/health")
async def health():
    return {"status": "ok", "motor": "teens", "version": "3.0"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("TEENS_PORT", 8005))
    uvicorn.run("motor_teens:app", host="0.0.0.0", port=port, reload=True)
