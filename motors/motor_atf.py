"""
motors/motor_atf.py — NEXUS v3 by Simplex
Motor ATF (Actualiza Tus Faros) — cotizaciones, agenda, pipeline — puerto 8004
Generado por Z.ai
"""
import os
import time
import uuid
import aiosqlite
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.notificaciones import notificar

app = FastAPI(title="NEXUS ATF Motor", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(os.path.dirname(__file__)), "output", "nexus_v3.db"))

# Catálogo de kits ATF con precios (dist / pub)
KITS_ATF = {
    "X1": {"nombre": "Aozoom X1 Bi-LED", "dist": 2350, "pub": 3149, "descripcion": "Bi-LED universal, excelente rendimiento"},
    "X2": {"nombre": "Aozoom X2 Bi-LED", "dist": 2050, "pub": 2799, "descripcion": "Bi-LED compacto, ideal faros pequeños"},
    "X3": {"nombre": "Aozoom X3 Bi-LED", "dist": 2350, "pub": 3149, "descripcion": "Bi-LED alta potencia"},
    "X4": {"nombre": "Aozoom X4 TOP Bi-LED", "dist": 1990, "pub": 2699, "descripcion": "El más vendido, relación precio-calidad"},
    "X5": {"nombre": "Aozoom X5 LED", "dist": 1199, "pub": 1599, "descripcion": "LED básico, buena entrada"},
    "X6": {"nombre": "Aozoom X6 LED", "dist": 1199, "pub": 1599, "descripcion": "LED económico"},
    "X7": {"nombre": "Aozoom X7 Bi-LED", "dist": 1550, "pub": 2069, "descripcion": "Bi-LED mid-range"},
}

COSTO_INSTALACION = 500  # Por defecto


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS atf_agenda (
                id TEXT PRIMARY KEY,
                cliente TEXT NOT NULL,
                telefono TEXT,
                vehiculo TEXT,
                kit TEXT,
                fecha TEXT NOT NULL,
                hora TEXT NOT NULL,
                estado TEXT DEFAULT 'pendiente',
                notas TEXT,
                precio_cotizado REAL,
                creado REAL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS atf_pipeline (
                id TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                telefono TEXT,
                vehiculo TEXT,
                kit_interes TEXT,
                estado TEXT DEFAULT 'prospecto',
                fuente TEXT,
                notas TEXT,
                creado REAL,
                actualizado REAL
            )
        """)
        await db.commit()


@app.on_event("startup")
async def startup():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    await init_db()


# ─── Models ───────────────────────────────────────────────────────────────────

class CotizarRequest(BaseModel):
    kit: str
    incluir_instalacion: bool = True
    descuento_pct: float = 0.0


class AgendarRequest(BaseModel):
    cliente: str
    telefono: Optional[str] = None
    vehiculo: str
    kit: str
    fecha: str  # YYYY-MM-DD
    hora: str   # HH:MM
    notas: Optional[str] = None


class PipelineRequest(BaseModel):
    nombre: str
    telefono: Optional[str] = None
    vehiculo: Optional[str] = None
    kit_interes: Optional[str] = None
    fuente: Optional[str] = "directo"
    notas: Optional[str] = None


class ActualizarPipelineRequest(BaseModel):
    estado: str
    notas: Optional[str] = None


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/atf/kits")
async def listar_kits():
    """Lista todos los kits disponibles con precios."""
    return {"ok": True, "kits": KITS_ATF}


@app.post("/atf/cotizar")
async def cotizar(req: CotizarRequest):
    """Genera cotización para un kit ATF."""
    kit = KITS_ATF.get(req.kit.upper())
    if not kit:
        raise HTTPException(status_code=404, detail=f"Kit '{req.kit}' no encontrado")

    precio_base = kit["pub"]
    if req.descuento_pct > 0:
        precio_base = precio_base * (1 - req.descuento_pct / 100)

    total = precio_base + (COSTO_INSTALACION if req.incluir_instalacion else 0)
    ganancia = precio_base - kit["dist"]

    return {
        "ok": True,
        "kit": req.kit.upper(),
        "nombre": kit["nombre"],
        "descripcion": kit["descripcion"],
        "precio_kit": round(precio_base, 2),
        "instalacion": COSTO_INSTALACION if req.incluir_instalacion else 0,
        "total": round(total, 2),
        "costo_dist": kit["dist"],
        "ganancia_neta": round(ganancia, 2),
        "margen_pct": round((ganancia / precio_base) * 100, 1),
        "whatsapp": f"Kit ATF {kit['nombre']}: ${round(precio_base):,}" +
                    (f" + Instalación: $500" if req.incluir_instalacion else "") +
                    f" = Total: ${round(total):,} MXN"
    }


@app.post("/atf/agendar")
async def agendar(req: AgendarRequest):
    """Agenda una cita de instalación ATF."""
    kit = KITS_ATF.get(req.kit.upper())
    if not kit:
        raise HTTPException(status_code=404, detail=f"Kit '{req.kit}' no existe")

    cita_id = str(uuid.uuid4())[:8]
    precio = kit["pub"] + COSTO_INSTALACION

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO atf_agenda VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (cita_id, req.cliente, req.telefono, req.vehiculo, req.kit.upper(),
             req.fecha, req.hora, "pendiente", req.notas, precio, time.time())
        )
        await db.commit()

    await notificar("cita_agendada", {
        "cliente": req.cliente,
        "vehiculo": req.vehiculo,
        "kit": req.kit.upper(),
        "fecha": req.fecha,
        "hora": req.hora
    }, canal="atf")

    return {
        "ok": True,
        "id": cita_id,
        "mensaje": f"Cita agendada para {req.cliente} el {req.fecha} a las {req.hora}",
        "precio_estimado": precio
    }


@app.get("/atf/agenda")
async def listar_agenda(dias: int = 7, estado: str = None):
    """Lista agenda ATF próxima."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if estado:
            cur = await db.execute(
                "SELECT * FROM atf_agenda WHERE estado=? ORDER BY fecha, hora",
                (estado,)
            )
        else:
            cur = await db.execute(
                "SELECT * FROM atf_agenda ORDER BY fecha, hora LIMIT 50"
            )
        rows = await cur.fetchall()

    return {"ok": True, "citas": [dict(r) for r in rows], "total": len(rows)}


@app.put("/atf/agenda/{cita_id}")
async def actualizar_cita(cita_id: str, estado: str, notas: str = None):
    """Actualiza estado de una cita."""
    async with aiosqlite.connect(DB_PATH) as db:
        if notas:
            await db.execute(
                "UPDATE atf_agenda SET estado=?, notas=? WHERE id=?",
                (estado, notas, cita_id)
            )
        else:
            await db.execute(
                "UPDATE atf_agenda SET estado=? WHERE id=?",
                (estado, cita_id)
            )
        await db.commit()

    return {"ok": True, "id": cita_id, "nuevo_estado": estado}


@app.post("/atf/pipeline")
async def agregar_prospecto(req: PipelineRequest):
    """Agrega prospecto al pipeline ATF."""
    pid = str(uuid.uuid4())[:8]
    now = time.time()

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO atf_pipeline VALUES (?,?,?,?,?,?,?,?,?,?)",
            (pid, req.nombre, req.telefono, req.vehiculo, req.kit_interes,
             "prospecto", req.fuente, req.notas, now, now)
        )
        await db.commit()

    return {"ok": True, "id": pid, "mensaje": f"Prospecto '{req.nombre}' agregado al pipeline"}


@app.get("/atf/pipeline")
async def ver_pipeline(estado: str = None):
    """Ver pipeline ATF."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if estado:
            cur = await db.execute(
                "SELECT * FROM atf_pipeline WHERE estado=? ORDER BY creado DESC",
                (estado,)
            )
        else:
            cur = await db.execute(
                "SELECT * FROM atf_pipeline ORDER BY actualizado DESC LIMIT 100"
            )
        rows = await cur.fetchall()

    return {"ok": True, "prospectos": [dict(r) for r in rows], "total": len(rows)}


@app.put("/atf/pipeline/{pid}")
async def mover_pipeline(pid: str, req: ActualizarPipelineRequest):
    """Mueve prospecto de estado en el pipeline."""
    estados_validos = ["prospecto", "contactado", "cotizado", "agendado", "instalado", "perdido"]
    if req.estado not in estados_validos:
        raise HTTPException(status_code=400, detail=f"Estado debe ser uno de: {estados_validos}")

    async with aiosqlite.connect(DB_PATH) as db:
        if req.notas:
            await db.execute(
                "UPDATE atf_pipeline SET estado=?, notas=?, actualizado=? WHERE id=?",
                (req.estado, req.notas, time.time(), pid)
            )
        else:
            await db.execute(
                "UPDATE atf_pipeline SET estado=?, actualizado=? WHERE id=?",
                (req.estado, time.time(), pid)
            )
        await db.commit()

    return {"ok": True, "id": pid, "nuevo_estado": req.estado}


@app.get("/health")
async def health():
    return {"status": "ok", "motor": "atf", "version": "3.0"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("ATF_PORT", 8004))
    uvicorn.run("motor_atf:app", host="0.0.0.0", port=port, reload=True)
