"""
nexus_notifier.py — Sistema de notificaciones de Nexus.

Canales disponibles:
  - WhatsApp: abre wa.me en browser (sin API, gratuito)
  - Telegram: envía mensaje via bot API (requiere TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID en .env)
  - Desktop: notificación de Windows (sin dependencias extra)

Uso:
    notifier.pedido_listo("Juan García", "Tazas sublimadas x12", "14:30")
    notifier.pedido_vencido("María López", "Sello laser")
    notifier.resumen_diario(pendientes=3, listos=1)
"""
import os
import json
import time
import urllib.parse
import webbrowser
from typing import Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_NEGOCIO_PATH = os.path.join(BASE_DIR, "CONFIG", "negocio.json")


def _negocio() -> dict:
    try:
        if os.path.exists(_NEGOCIO_PATH):
            with open(_NEGOCIO_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _log(msg: str):
    ts = time.strftime("[%H:%M:%S]")
    print(f"[NOTIF] {ts} {msg}")


def _desktop_notify(title: str, message: str):
    """Notificación de escritorio en Windows (sin dependencias extra)."""
    try:
        import subprocess
        ps_cmd = (
            f"Add-Type -AssemblyName System.Windows.Forms; "
            f"$n = New-Object System.Windows.Forms.NotifyIcon; "
            f"$n.Icon = [System.Drawing.SystemIcons]::Information; "
            f"$n.Visible = $true; "
            f"$n.ShowBalloonTip(5000, '{title}', '{message}', "
            f"[System.Windows.Forms.ToolTipIcon]::Info); "
            f"Start-Sleep -s 6; $n.Dispose()"
        )
        subprocess.Popen(
            ["powershell", "-WindowStyle", "Hidden", "-Command", ps_cmd],
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )
    except Exception as e:
        _log(f"Desktop notify error: {e}")


def _telegram_send(message: str) -> bool:
    """Envía mensaje via Telegram Bot API."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return False
    try:
        import urllib.request
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = json.dumps({"chat_id": chat_id, "text": message, "parse_mode": "HTML"}).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.status == 200
    except Exception as e:
        _log(f"Telegram error: {e}")
        return False


def _whatsapp_open(telefono: str, mensaje: str):
    """Abre WhatsApp Web con el número y mensaje pre-rellenado."""
    num = str(telefono).strip().replace(" ", "").replace("-", "").lstrip("+")
    if len(num) == 10 and num.isdigit():
        num = "52" + num
    encoded = urllib.parse.quote(mensaje)
    if num:
        url = f"https://wa.me/{num}?text={encoded}"
    else:
        url = f"https://wa.me/?text={encoded}"
    try:
        webbrowser.open(url)
        _log(f"WhatsApp abierto para {num}")
    except Exception as e:
        _log(f"WhatsApp open error: {e}")


class Notifier:
    def __init__(self):
        negocio = _negocio()
        self.negocio_nombre = negocio.get("nombre", "Nexus Taller")
        self._telegram_ok = bool(
            os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID")
        )

    def pedido_listo(self, cliente: str, producto: str, hora: str = "", cliente_tel: str = ""):
        """Avisa que un pedido está listo. Notifica desktop + opcionalmente Telegram."""
        msg_corto = f"✅ LISTO: {producto[:40]} — {cliente}"
        msg_largo = (
            f"<b>✅ Pedido listo para entrega</b>\n"
            f"👤 {cliente}\n"
            f"📦 {producto}\n"
            f"🕐 {hora or 'Ahora'}"
        )
        _desktop_notify("Pedido Listo ✅", f"{cliente} — {producto[:30]}")
        if self._telegram_ok:
            _telegram_send(msg_largo)
        if cliente_tel:
            wa_msg = (
                f"Hola {cliente} 👋\n"
                f"Tu pedido está listo para recoger:\n"
                f"📦 {producto}\n\n"
                f"¿A qué hora pasas? — {self.negocio_nombre}"
            )
            _whatsapp_open(cliente_tel, wa_msg)
        _log(msg_corto)

    def pedido_vencido(self, cliente: str, producto: str):
        """Alerta de pedido que ya venció."""
        msg = f"⚠️ VENCIDO: {producto[:40]} — {cliente}"
        _desktop_notify("⚠️ Pedido Vencido", f"{cliente} — {producto[:30]}")
        if self._telegram_ok:
            _telegram_send(f"<b>⚠️ Pedido VENCIDO</b>\n👤 {cliente}\n📦 {producto}")
        _log(msg)

    def resumen_diario(self, pendientes: int = 0, listos: int = 0, bajo_stock: int = 0):
        """Envía resumen del día por Telegram."""
        partes = [f"<b>📊 Resumen Nexus</b>"]
        if pendientes:
            partes.append(f"📋 {pendientes} pedidos pendientes")
        if listos:
            partes.append(f"✅ {listos} listos para entregar")
        if bajo_stock:
            partes.append(f"⚠️ {bajo_stock} ítems con stock bajo")
        if not pendientes and not listos:
            partes.append("✓ Todo en orden")
        msg = "\n".join(partes)
        if self._telegram_ok:
            _telegram_send(msg)
        _log(f"Resumen diario enviado: pend={pendientes} listos={listos}")

    def nueva_cotizacion(self, cliente: str, servicio: str, precio: float):
        """Notifica nueva cotización generada."""
        msg = f"💲 Cotización: {servicio} — {cliente} — ${precio:.0f}"
        _desktop_notify("Nueva Cotización 💲", msg[:60])
        if self._telegram_ok:
            _telegram_send(f"<b>💲 Nueva cotización</b>\n👤 {cliente}\n🔧 {servicio}\n💰 ${precio:.2f}")
        _log(msg)


notifier = Notifier()
