"""
motors/motor_reportes.py — NEXUS v3 by Simplex
Motor de reportes y análisis con IA — puerto 8008
Generado por Z.ai | AI via lib/ai_client.py (punto único)
"""
import os
import time
import aiosqlite
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.ai_client import AIClient

app = FastAPI(title="NEXUS Reportes Motor", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(os.path.dirname(__file__)), "output", "nexus_v3.db"))

# Cliente IA — instancia singleton del motor de reportes
_ai_client: Optional[AIClient] = None


def get_ai_client() -> AIClient:
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient({
            "GROQ_API_KEY": os.getenv("GROQ_API_KEY", ""),
            "ZAI_API_KEY": os.getenv("ZAI_API_KEY", ""),
            "OLLAMA_URL": os.getenv("OLLAMA_URL", "http://localhost:11434"),
            "default_personality": "nexus"
        })
    return _ai_client


# ─── Helpers DB ───────────────────────────────────────────────────────────────

async def _query(sql: str, params: tuple = ()) -> list[dict]:
    """Ejecuta una consulta y retorna lista de dicts."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(sql, params)
            rows = await cur.fetchall()
            return [dict(r) for r in rows]
    except Exception:
        return []


async def _scalar(sql: str, params: tuple = (), default=0):
    """Ejecuta consulta y retorna un valor escalar."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute(sql, params)
            row = await cur.fetchone()
            return row[0] if row and row[0] is not None else default
    except Exception:
        return default


# ─── Models ───────────────────────────────────────────────────────────────────

class AnalisisRequest(BaseModel):
    pregunta: str
    contexto: Optional[str] = None
    task_type: str = "analysis"  # fast | analysis | complex


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/reportes/resumen-diario")
async def resumen_diario():
    """Resumen del día: pagos, citas, misiones, pedidos."""
    hoy = time.time() - (time.time() % 86400)

    # Pagos del día
    pagos_hoy = await _scalar(
        "SELECT COALESCE(SUM(monto),0) FROM pagos WHERE creado > ?", (hoy,)
    )
    n_pagos = await _scalar(
        "SELECT COUNT(*) FROM pagos WHERE creado > ?", (hoy,)
    )

    # Citas ATF del día
    fecha_hoy = time.strftime("%Y-%m-%d")
    citas = await _query(
        "SELECT cliente, kit, hora, estado FROM atf_agenda WHERE fecha=?",
        (fecha_hoy,)
    )

    # Misiones completadas hoy (tabla motor_teens)
    misiones_completadas = await _scalar(
        "SELECT COUNT(*) FROM misiones WHERE completado > ? AND estado IN ('completada','aprobada')",
        (hoy,)
    )

    # Prospectos nuevos hoy
    prospectos_hoy = await _scalar(
        "SELECT COUNT(*) FROM atf_pipeline WHERE creado > ?", (hoy,)
    )

    return {
        "ok": True,
        "fecha": fecha_hoy,
        "pagos": {
            "total_mxn": round(pagos_hoy, 2),
            "cantidad": n_pagos
        },
        "atf": {
            "citas_hoy": len(citas),
            "detalle": citas
        },
        "teens": {
            "misiones_completadas": misiones_completadas
        },
        "pipeline": {
            "prospectos_nuevos": prospectos_hoy
        }
    }


@app.get("/reportes/resumen-semana")
async def resumen_semana():
    """Resumen de los últimos 7 días."""
    hace_7_dias = time.time() - (7 * 86400)

    ingresos = await _scalar(
        "SELECT COALESCE(SUM(monto),0) FROM pagos WHERE creado > ?", (hace_7_dias,)
    )
    n_pagos = await _scalar(
        "SELECT COUNT(*) FROM pagos WHERE creado > ?", (hace_7_dias,)
    )
    citas_realizadas = await _scalar(
        "SELECT COUNT(*) FROM atf_agenda WHERE creado > ? AND estado='realizada'",
        (hace_7_dias,)
    )
    prospectos = await _scalar(
        "SELECT COUNT(*) FROM atf_pipeline WHERE creado > ?", (hace_7_dias,)
    )
    instalados = await _scalar(
        "SELECT COUNT(*) FROM atf_pipeline WHERE actualizado > ? AND estado='instalado'",
        (hace_7_dias,)
    )

    tasa_conversion = round((instalados / prospectos * 100), 1) if prospectos > 0 else 0

    return {
        "ok": True,
        "periodo": "7 días",
        "ingresos_total": round(ingresos, 2),
        "pagos_count": n_pagos,
        "atf": {
            "citas_realizadas": citas_realizadas,
            "prospectos_nuevos": prospectos,
            "instalaciones": instalados,
            "tasa_conversion_pct": tasa_conversion
        }
    }


@app.post("/reportes/analisis-ia")
async def analisis_ia(req: AnalisisRequest):
    """
    Análisis inteligente con IA.
    Recopila datos del negocio y responde la pregunta con contexto real.
    """
    ai = get_ai_client()

    # Recopilar contexto del negocio
    hace_30 = time.time() - (30 * 86400)

    ingresos_mes = await _scalar(
        "SELECT COALESCE(SUM(monto),0) FROM pagos WHERE creado > ?", (hace_30,)
    )
    prospectos_mes = await _scalar(
        "SELECT COUNT(*) FROM atf_pipeline WHERE creado > ?", (hace_30,)
    )
    instalaciones_mes = await _scalar(
        "SELECT COUNT(*) FROM atf_pipeline WHERE estado='instalado' AND actualizado > ?",
        (hace_30,)
    )
    citas_pendientes = await _scalar(
        "SELECT COUNT(*) FROM atf_agenda WHERE estado='pendiente'", ()
    )
    cotizaciones_pendientes = await _scalar(
        "SELECT COUNT(*) FROM cotizaciones WHERE estado='enviada'", ()
    )

    contexto_negocio = f"""
DATOS REALES NEXUS (últimos 30 días):
- Ingresos: ${ingresos_mes:,.0f} MXN
- Prospectos ATF nuevos: {prospectos_mes}
- Instalaciones completadas: {instalaciones_mes}
- Citas pendientes: {citas_pendientes}
- Cotizaciones sin cerrar: {cotizaciones_pendientes}
"""

    if req.contexto:
        contexto_negocio += f"\nContexto adicional:\n{req.contexto}"

    messages = [
        {
            "role": "system",
            "content": (
                "Eres el motor de análisis de NEXUS v3 by Simplex. "
                "Analizas datos reales del negocio y das recomendaciones concretas y accionables. "
                "Responde en español, sé directo y específico."
            )
        },
        {
            "role": "user",
            "content": f"Contexto del negocio:\n{contexto_negocio}\n\nPregunta: {req.pregunta}"
        }
    ]

    respuesta = await ai.chat(
        messages=messages,
        personality="nexus",
        task_type=req.task_type
    )

    return {
        "ok": True,
        "pregunta": req.pregunta,
        "analisis": respuesta,
        "datos_usados": {
            "ingresos_mes": ingresos_mes,
            "prospectos_mes": prospectos_mes,
            "instalaciones_mes": instalaciones_mes
        }
    }


@app.get("/reportes/estado-proveedores-ia")
async def estado_proveedores():
    """Verifica qué proveedores de IA están disponibles en este momento."""
    ai = get_ai_client()
    proveedores = await ai.get_available_providers()
    health = await ai.health_check()
    return {
        "ok": True,
        "estado_general": health["estado_general"],
        "total_disponibles": health["total_disponibles"],
        "proveedores": proveedores
    }


@app.get("/reportes/pipeline-analytics")
async def pipeline_analytics():
    """Análisis del funnel de ventas ATF."""
    estados = ["prospecto", "contactado", "cotizado", "agendado", "instalado", "perdido"]
    funnel = {}

    for estado in estados:
        n = await _scalar(
            "SELECT COUNT(*) FROM atf_pipeline WHERE estado=?", (estado,)
        )
        funnel[estado] = n

    total = sum(funnel.values())
    tasa_cierre = round(funnel["instalado"] / total * 100, 1) if total > 0 else 0

    return {
        "ok": True,
        "funnel": funnel,
        "total_prospectos": total,
        "tasa_cierre_pct": tasa_cierre,
        "perdidos_pct": round(funnel["perdido"] / total * 100, 1) if total > 0 else 0
    }


@app.get("/health")
async def health():
    return {"status": "ok", "motor": "reportes", "version": "3.0"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("REPORTES_PORT", 8008))
    uvicorn.run("motor_reportes:app", host="0.0.0.0", port=port, reload=True)
