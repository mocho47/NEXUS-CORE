"""
nexus_fingerprint.py — Huella de hardware única por máquina.

Combina identificadores de CPU, MAC y disco para generar
un hash hexadecimal de 16 caracteres que identifica únicamente
la instalación. Este hash es el "seed" de la licencia.

No requiere dependencias externas — solo módulos estándar de Python.
En Windows usa WMI vía subprocess para mayor precisión.
En otros sistemas usa uuid y platform como fallback.
"""

import os
import uuid
import platform
import hashlib
import subprocess
import json
import datetime

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "CONFIG")


def _wmic(query: str) -> str:
    """Ejecuta un comando WMIC y devuelve el primer valor encontrado."""
    try:
        result = subprocess.run(
            ["wmic"] + query.split(),
            capture_output=True, text=True, timeout=5
        )
        lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
        # El formato WMIC devuelve encabezado en primera línea, valor en segunda
        for line in lines[1:]:
            if line and line.upper() not in ("", "OK", "NONE"):
                return line.strip()
    except Exception:
        pass
    return ""


def _get_cpu_id() -> str:
    """ID del procesador (Windows WMI / fallback platform)."""
    if platform.system() == "Windows":
        val = _wmic("cpu get ProcessorId")
        if val:
            return val
    return platform.processor() or platform.machine()


def _get_mac() -> str:
    """Dirección MAC del primer adaptador de red no-loopback."""
    try:
        mac_int = uuid.getnode()
        # Verificar que no sea generado (bit de multicast)
        if (mac_int >> 40) % 2:
            return ""
        return ":".join(f"{(mac_int >> (8*i)) & 0xff:02x}" for i in reversed(range(6)))
    except Exception:
        return ""


def _get_disk_serial() -> str:
    """Número de serie del disco principal (Windows WMI / fallback)."""
    if platform.system() == "Windows":
        val = _wmic("diskdrive get SerialNumber")
        if val:
            return val
    return ""


def _get_bios_uuid() -> str:
    """UUID del BIOS (Windows WMI / fallback)."""
    if platform.system() == "Windows":
        val = _wmic("csproduct get UUID")
        if val and val.upper() != "FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF":
            return val
    return ""


def generar_huella() -> str:
    """
    Genera la huella de hardware: string hex de 16 caracteres.
    Combina CPU + MAC + disco + BIOS con SHA-256.
    """
    partes = [
        _get_cpu_id(),
        _get_mac(),
        _get_disk_serial(),
        _get_bios_uuid(),
        platform.node(),        # nombre del host
    ]
    combinado = "|".join(p for p in partes if p)
    if not combinado:
        combinado = str(uuid.getnode())  # último fallback

    digest = hashlib.sha256(combinado.encode("utf-8")).hexdigest()
    return digest[:16].upper()


def obtener_info_hardware() -> dict:
    """Retorna información del hardware sin datos sensibles."""
    return {
        "huella":    generar_huella(),
        "cpu":       platform.processor()[:40] if platform.processor() else "N/A",
        "sistema":   f"{platform.system()} {platform.release()}",
        "hostname":  platform.node(),
        "bits":      platform.architecture()[0],
        "timestamp": datetime.datetime.now().isoformat(),
    }
