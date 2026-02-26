"""
nexus_telegram.py — Bot de Telegram para Nexus.

Permite controlar Nexus y recibir notificaciones desde Telegram.

Comandos disponibles:
  /start    — bienvenida
  /resumen  — estado del día (pedidos, stock)
  /pedidos  — lista los 5 pedidos pendientes más próximos
  /stock    — ítems con stock bajo (< 3 unidades)
  /listo <cliente> — marca pedido como LISTO desde Telegram

Requisitos en .env:
  TELEGRAM_BOT_TOKEN=xxx
  TELEGRAM_CHAT_ID=xxx  (solo responde a este chat ID por seguridad)

Instalar: pip install python-telegram-bot
"""
import os
import json
import time
import threading
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

log = logging.getLogger("NexusTelegram")


def _env(key: str) -> str:
    return os.environ.get(key, "").strip()


def _send_message(token: str, chat_id: str, text: str) -> bool:
    """Envía un mensaje de texto sin dependencias externas."""
    try:
        import urllib.request
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = json.dumps({
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        }).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status == 200
    except Exception as e:
        log.warning(f"[Telegram] send error: {e}")
        return False


def _get_updates(token: str, offset: int = 0, timeout: int = 20):
    """Long-poll para recibir updates."""
    try:
        import urllib.request, urllib.parse
        url = (
            f"https://api.telegram.org/bot{token}/getUpdates"
            f"?offset={offset}&timeout={timeout}&allowed_updates=[\"message\"]"
        )
        with urllib.request.urlopen(url, timeout=timeout + 5) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        log.debug(f"[Telegram] getUpdates error: {e}")
        return None


def _build_resumen() -> str:
    try:
        import nexus_orders
        import nexus_stock
        import datetime
        nexus_orders.manager.load_orders()
        nexus_stock.manager.load_stock()
        pend = nexus_orders.manager.get_pending()
        bajo = nexus_stock.manager.list_bajo_stock(minimo=3)
        hoy = str(datetime.date.today())
        hoy_pend = [p for p in pend if (p.get("deadline") or "").startswith(hoy)]
        partes = [
            f"<b>📊 Nexus — Resumen del día</b>",
            f"📋 Pedidos pendientes: {len(pend)}",
            f"⏰ Vencen hoy: {len(hoy_pend)}",
            f"⚠️ Stock bajo: {len(bajo)} ítems",
        ]
        if hoy_pend:
            partes.append("\n<b>Urgentes hoy:</b>")
            for p in hoy_pend[:3]:
                hora = (p.get("deadline") or "")[:16]
                partes.append(f"• {p['cliente']} — {p['producto'][:30]} ({hora})")
        return "\n".join(partes)
    except Exception as e:
        return f"Error al obtener resumen: {e}"


def _build_pedidos() -> str:
    try:
        import nexus_orders
        pend = nexus_orders.manager.get_pending()
        if not pend:
            return "✅ Sin pedidos pendientes."
        lines = ["<b>📋 Pedidos pendientes:</b>"]
        for p in pend[:5]:
            hora = (p.get("deadline") or "")[:16]
            lines.append(f"• <b>{p['cliente']}</b> — {p['producto'][:25]} | {hora}")
        if len(pend) > 5:
            lines.append(f"... y {len(pend)-5} más")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


def _build_stock() -> str:
    try:
        import nexus_stock
        nexus_stock.manager.load_stock()
        bajo = nexus_stock.manager.list_bajo_stock(minimo=3)
        if not bajo:
            return "✅ Todo el stock está bien."
        lines = ["<b>⚠️ Stock bajo:</b>"]
        for i in bajo[:8]:
            lines.append(f"• {i['nombre']} — {i.get('cantidad',0)} uds")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


def _cmd_listo(args: str) -> str:
    if not args.strip():
        return "Uso: /listo <nombre del cliente>"
    try:
        import nexus_orders
        result = nexus_orders.manager.mark_ready(args.strip())
        return f"✅ {result}"
    except Exception as e:
        return f"Error: {e}"


def _process_message(token: str, chat_id_allowed: str, msg: dict):
    """Procesa un mensaje entrante y responde si corresponde."""
    chat_id = str(msg.get("chat", {}).get("id", ""))
    text = (msg.get("text") or "").strip()

    if not text:
        return

    # Seguridad: solo responde al chat autorizado
    if chat_id_allowed and chat_id != chat_id_allowed:
        _send_message(token, chat_id,
                      "⛔ No autorizado. Este bot es privado.")
        return

    text_lower = text.lower()

    if text_lower in ("/start", "/help"):
        reply = (
            "<b>⚡ Nexus Bot</b>\n\n"
            "/resumen — Estado del día\n"
            "/pedidos — Pedidos pendientes\n"
            "/stock — Items con stock bajo\n"
            "/listo &lt;cliente&gt; — Marcar pedido como listo"
        )
    elif text_lower == "/health" or text_lower == "/estado":
        try:
            from nexus_health import reporte_completo
            r = reporte_completo()
            estado = r.get("estado", "?")
            alertas = r.get("alertas", [])
            disco = r.get("disco", {})
            apps = r.get("apps", {})
            emoji = "🟢" if estado == "OK" else "🟡" if estado == "ALERTA" else "🔴"
            txt = f"{emoji} <b>NEXUS Health: {estado}</b>\n\n"
            if alertas:
                txt += "⚠️ <b>Alertas:</b>\n" + "\n".join(f"  • {a}" for a in alertas) + "\n\n"
            txt += f"💾 Disco: {disco.get('libre_gb','?')}GB libres\n"
            txt += f"📂 Carpeta out: {disco.get('out_archivos','?')} archivos\n\n"
            for nombre, info in apps.items():
                ok = info.get("ok", False) if isinstance(info, dict) else info
                txt += f"{'✅' if ok else '❌'} {nombre}\n"
            _send_message(token, chat_id, txt)
        except Exception as e:
            _send_message(token, chat_id, f"❌ Error en health check: {e}")
    elif text_lower == "/resumen":
        reply = _build_resumen()
    elif text_lower == "/pedidos":
        reply = _build_pedidos()
    elif text_lower == "/stock":
        reply = _build_stock()
    elif text_lower.startswith("/listo"):
        args = text[6:].strip()
        reply = _cmd_listo(args)
    else:
        reply = "Comando no reconocido. Usa /help para ver los comandos disponibles."

    _send_message(token, chat_id, reply)


class TelegramBot:
    def __init__(self):
        self.token = _env("TELEGRAM_BOT_TOKEN")
        self.chat_id = _env("TELEGRAM_CHAT_ID")
        self._running = False
        self._thread = None

    @property
    def configured(self) -> bool:
        return bool(self.token)

    def send(self, text: str) -> bool:
        if not self.token:
            return False
        target = self.chat_id or ""
        if not target:
            log.warning("[Telegram] TELEGRAM_CHAT_ID no configurado, no se puede enviar.")
            return False
        return _send_message(self.token, target, text)

    def start(self):
        if not self.configured:
            log.info("[Telegram] Bot no configurado (falta TELEGRAM_BOT_TOKEN). Salteando.")
            return
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="NexusTelegramBot")
        self._thread.start()
        log.info("[Telegram] Bot iniciado.")

    def stop(self):
        self._running = False

    def _loop(self):
        offset = 0
        while self._running:
            try:
                resp = _get_updates(self.token, offset=offset, timeout=20)
                if resp and resp.get("ok"):
                    for update in resp.get("result", []):
                        offset = update["update_id"] + 1
                        msg = update.get("message")
                        if msg:
                            try:
                                _process_message(self.token, self.chat_id, msg)
                            except Exception as e:
                                log.error(f"[Telegram] process error: {e}")
            except Exception as e:
                log.debug(f"[Telegram] loop error: {e}")
                time.sleep(5)


bot = TelegramBot()


if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()
    logging.basicConfig(level=logging.INFO)
    b = TelegramBot()
    if not b.configured:
        print("Configura TELEGRAM_BOT_TOKEN en .env para usar el bot.")
    else:
        print(f"Bot iniciado. Chat ID autorizado: {b.chat_id or '(cualquiera)'}")
        b.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            b.stop()
            print("Bot detenido.")
