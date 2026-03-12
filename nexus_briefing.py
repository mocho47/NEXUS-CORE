# -*- coding: utf-8 -*-
"""
NEXUS BRIEFING — Analisis inteligente del estado del negocio
Cada vez que abres NEXUS, te saluda con lo que REALMENTE importa hoy.

No es un saludo generico — es un director de operaciones que te da
el panorama completo en 3 oraciones: pendientes, oportunidades, alertas.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger("nexus_briefing")

CONFIG_DIR = Path("C:/nexus/CONFIG")
PEDIDOS_PATH = CONFIG_DIR / "pedidos_backup.json"
CLIENTES_PATH = CONFIG_DIR / "clientes_backup.json"
AUTOVENTAS_PATH = CONFIG_DIR / "autoventas.json"
MEMORIA_PATH = CONFIG_DIR / "nexus_memoria.json"


def _cargar_json(path: Path, default=None):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except:
            pass
    return default if default is not None else {}


def _hora_saludo() -> str:
    h = datetime.now().hour
    if h < 12:
        return "Buenos días"
    elif h < 19:
        return "Buenas tardes"
    else:
        return "Buenas noches"


def analizar_negocio() -> dict:
    """
    Analiza el estado actual del negocio via los managers internos de NEXUS.
    Sin inventar. Sin suavizar. Solo la verdad del estado del negocio.
    """
    ahora = datetime.now()
    hoy = ahora.strftime("%Y-%m-%d")
    manana = (ahora + timedelta(days=1)).strftime("%Y-%m-%d")

    # ── Pedidos via nexus_orders ───────────────────────────────────────────
    pedidos = []
    try:
        from nexus_orders import orders_manager
        orders_manager.load_orders()
        pedidos = orders_manager.orders or []
    except Exception:
        pass

    if not isinstance(pedidos, list):
        pedidos = []

    pendientes = [p for p in pedidos if isinstance(p, dict) and p.get("status") in ("pendiente", "en proceso", "listo")]
    vencen_hoy   = []
    vencen_manana = []
    for p in pendientes:
        dl = p.get("deadline", "") or p.get("entrega", "")
        if dl:
            dl_date = str(dl)[:10]
            if dl_date <= hoy:
                vencen_hoy.append(p)
            elif dl_date == manana:
                vencen_manana.append(p)

    listos = [p for p in pedidos if isinstance(p, dict) and p.get("status") == "listo"]

    # ── Prospectos via CONFIG ─────────────────────────────────────────────
    seguimiento_pendiente = []
    try:
        av_paths = [
            CONFIG_DIR / "autoventas.json",
            Path("C:/nexus/autoventas_data.json"),
        ]
        for ap in av_paths:
            if ap.exists():
                av = _cargar_json(ap, {})
                prosp_raw = av.get("prospectos", []) if isinstance(av, dict) else []
                for p in prosp_raw:
                    if isinstance(p, dict) and p.get("stage") not in ("ganado", "perdido") and p.get("nombre"):
                        seguimiento_pendiente.append(p)
                break
    except Exception:
        pass

    # ── Clientes ─────────────────────────────────────────────────────────
    total_clientes = 0
    try:
        from nexus_crm import crm_manager
        total_clientes = len(crm_manager.clientes or [])
    except Exception:
        pass

    # ── Memoria ───────────────────────────────────────────────────────────
    memoria = _cargar_json(MEMORIA_PATH, {})
    aprendizajes_recientes = memoria.get("aprendizajes", [])[-3:]

    return {
        "saludo": _hora_saludo(),
        "fecha": ahora.strftime("%A %d de %B"),
        "pedidos_pendientes": len(pendientes),
        "pedidos_vencen_hoy": len(vencen_hoy),
        "pedidos_listos_entregar": len(listos),
        "pedidos_vencen_manana": len(vencen_manana),
        "detalle_urgentes": [f"{p.get('cliente','?')} — {p.get('producto','?')[:40]}" for p in vencen_hoy[:3]],
        "prospectos_activos": len(seguimiento_pendiente),
        "detalle_prospectos": [f"{p.get('nombre','?')} ({p.get('servicio','?')})" for p in seguimiento_pendiente[:2]],
        "total_clientes": total_clientes,
        "aprendizajes_recientes": aprendizajes_recientes,
    }


def generar_briefing(datos: dict | None = None) -> str:
    """
    Genera el mensaje de briefing basado en datos reales.
    Directo, sin relleno, sin "excelente pregunta".
    """
    if datos is None:
        datos = analizar_negocio()

    partes = []
    saludo = datos["saludo"]
    partes.append(f"{saludo}.")

    # Urgencias primero
    if datos["pedidos_vencen_hoy"] > 0:
        nombres = ", ".join(datos["detalle_urgentes"])
        partes.append(
            f"URGENTE: {datos['pedidos_vencen_hoy']} pedido{'s' if datos['pedidos_vencen_hoy']>1 else ''} "
            f"con entrega hoy — {nombres}."
        )
    elif datos["pedidos_listos_entregar"] > 0:
        partes.append(
            f"Tienes {datos['pedidos_listos_entregar']} pedido{'s' if datos['pedidos_listos_entregar']>1 else ''} "
            f"listo{'s' if datos['pedidos_listos_entregar']>1 else ''} para entregar."
        )
    elif datos["pedidos_pendientes"] > 0:
        partes.append(
            f"{datos['pedidos_pendientes']} pedido{'s' if datos['pedidos_pendientes']>1 else ''} en proceso."
        )
    else:
        partes.append("Sin pedidos activos.")

    # Prospectos
    if datos["prospectos_activos"] > 0:
        nombres_p = ", ".join(datos["detalle_prospectos"])
        partes.append(
            f"{datos['prospectos_activos']} prospecto{'s' if datos['prospectos_activos']>1 else ''} "
            f"en seguimiento: {nombres_p}."
        )

    # Vencen mañana
    if datos["pedidos_vencen_manana"] > 0:
        partes.append(
            f"Mañana vencen {datos['pedidos_vencen_manana']} más — prepáralos hoy."
        )

    return " ".join(partes)


async def generar_briefing_audio(texto: str | None = None) -> dict:
    """
    Genera el briefing completo con audio TTS (Edge TTS Jorge Neural).
    Retorna: {texto, audio_b64, datos}
    """
    import base64
    import tempfile
    import os

    datos = analizar_negocio()
    if texto is None:
        texto = generar_briefing(datos)

    audio_b64 = None
    try:
        import edge_tts
        voz = "es-MX-JorgeNeural"
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name

        communicate = edge_tts.Communicate(texto, voz)
        await communicate.save(tmp_path)

        with open(tmp_path, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode()
        os.unlink(tmp_path)
    except Exception as e:
        logger.warning(f"TTS briefing error: {e}")

    return {
        "ok": True,
        "texto": texto,
        "audio_b64": audio_b64,
        "datos": datos
    }
