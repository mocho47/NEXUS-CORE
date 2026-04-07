"""
motors/motor_pagos.py — NEXUS v3 by Simplex
Motor de pagos y cotizaciones — puerto 8007
Generado por Z.ai (indentación corregida)
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

app = FastAPI(title="NEXUS Pagos Motor", version="3.0")

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
            CREATE TABLE IF NOT EXISTS cotizaciones (
                id TEXT PRIMARY KEY,
                cliente TEXT NOT NULL,
                concepto TEXT NOT NULL,
                desglose TEXT,
                total REAL NOT NULL,
                estado TEXT DEFAULT 'enviada',
                creado REAL,
                expira REAL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS pagos (
                id TEXT PRIMARY KEY,
                cliente TEXT NOT NULL,
                concepto TEXT NOT NULL,
                monto REAL NOT NULL,
                metodo TEXT DEFAULT 'efectivo',
                referencia TEXT,
                cotizacion_id TEXT,
                estado TEXT DEFAULT 'recibido',
                creado REAL
            )
        """)
        await db.commit()


@app.on_event("startup")
async def startup():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    await init_db()


# ─── Models ───────────────────────────────────────────────────────────────────

class Cotizacion(BaseModel):
    cliente: str
    concepto: str
    desglose: Optional[str] = None
    total: float
    dias_vigencia: int = 7


class Pago(BaseModel):
    cliente: str
    concepto: str
    monto: float
    metodo: Optional[str] = "efectivo"
    referencia: Optional[str] = None
    cotizacion_id: Optional[str] = None


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.post("/pagos/cotizacion")
async def crear_cotizacion(req: Cotizacion):
    """Genera una cotización."""
    cid = str(uuid.uuid4())[:8]
    now = time.time()
    expira = now + (req.dias_vigencia * 86400)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO cotizaciones VALUES (?,?,?,?,?,?,?,?)",
            (cid, req.cliente, req.concepto, req.desglose, req.total,
             "enviada", now, expira)
        )
        await db.commit()

    return {
        "ok": True,
        "id": cid,
        "cliente": req.cliente,
        "total": req.total,
        "valida_hasta": time.strftime("%Y-%m-%d", time.localtime(expira)),
        "whatsapp": f"Cotización NEXUS #{cid}\n{req.concepto}\nTotal: ${req.total:,.0f} MXN\nVálida {req.dias_vigencia} días"
    }


@app.get("/pagos/cotizaciones")
async def listar_cotizaciones(cliente: str = None, estado: str = None):
    """Lista cotizaciones."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if cliente:
            cur = await db.execute(
                "SELECT * FROM cotizaciones WHERE cliente LIKE ? ORDER BY creado DESC",
                (f"%{cliente}%",)
            )
        elif estado:
            cur = await db.execute(
                "SELECT * FROM cotizaciones WHERE estado=? ORDER BY creado DESC",
                (estado,)
            )
        else:
            cur = await db.execute(
                "SELECT * FROM cotizaciones ORDER BY creado DESC LIMIT 50"
            )
        rows = await cur.fetchall()

    return {"ok": True, "cotizaciones": [dict(r) for r in rows], "total": len(rows)}


@app.post("/pagos/registrar")
async def registrar_pago(req: Pago):
    """Registra un pago recibido."""
    pid = str(uuid.uuid4())[:8]

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO pagos VALUES (?,?,?,?,?,?,?,?,?)",
            (pid, req.cliente, req.concepto, req.monto, req.metodo,
             req.referencia, req.cotizacion_id, "recibido", time.time())
        )
        # Si viene de cotización, marcarla como pagada
        if req.cotizacion_id:
            await db.execute(
                "UPDATE cotizaciones SET estado='pagada' WHERE id=?",
                (req.cotizacion_id,)
            )
        await db.commit()

    await notificar("pago_registrado", {
        "cliente": req.cliente,
        "monto": req.monto,
        "metodo": req.metodo,
        "concepto": req.concepto
    }, canal="global")

    return {
        "ok": True,
        "id": pid,
        "mensaje": f"Pago de ${req.monto:,.0f} registrado para {req.cliente}"
    }


@app.get("/pagos/listar")
async def listar_pagos(cliente: str = None, dias: int = 30):
    """Lista pagos recientes."""
    desde = time.time() - (dias * 86400)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if cliente:
            cur = await db.execute(
                "SELECT * FROM pagos WHERE cliente LIKE ? AND creado > ? ORDER BY creado DESC",
                (f"%{cliente}%", desde)
            )
        else:
            cur = await db.execute(
                "SELECT * FROM pagos WHERE creado > ? ORDER BY creado DESC",
                (desde,)
            )
        rows = await cur.fetchall()

    total_monto = sum(dict(r)["monto"] for r in rows)
    return {
        "ok": True,
        "pagos": [dict(r) for r in rows],
        "total_registros": len(rows),
        "total_monto": total_monto,
        "periodo_dias": dias
    }


@app.get("/pagos/resumen")
async def resumen_pagos():
    """Resumen financiero rápido."""
    hoy_inicio = time.time() - (time.time() % 86400)
    mes_inicio = time.time() - (30 * 86400)

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT SUM(monto) FROM pagos WHERE creado > ?", (hoy_inicio,))
        hoy = (await cur.fetchone())[0] or 0

        cur = await db.execute("SELECT SUM(monto) FROM pagos WHERE creado > ?", (mes_inicio,))
        mes = (await cur.fetchone())[0] or 0

        cur = await db.execute("SELECT COUNT(*) FROM cotizaciones WHERE estado='enviada'")
        cotizaciones_pendientes = (await cur.fetchone())[0] or 0

    return {
        "ok": True,
        "ingresos_hoy": round(hoy, 2),
        "ingresos_mes": round(mes, 2),
        "cotizaciones_pendientes": cotizaciones_pendientes
    }


@app.get("/health")
async def health():
    return {"status": "ok", "motor": "pagos", "version": "3.0"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PAGOS_PORT", 8007))
    uvicorn.run("motor_pagos:app", host="0.0.0.0", port=port, reload=True)
