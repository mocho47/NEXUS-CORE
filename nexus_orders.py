import datetime
import time
import nexus_db

class OrderManager:
    def __init__(self):
        self.orders = []
        self.load_orders()

    def load_orders(self):
        self.orders = nexus_db.db.get_pedidos()

    def get_all_orders(self):
        self.load_orders()
        return self.orders

    def update_order(self, order_id, new_deadline, new_status):
        self.load_orders()
        for order in self.orders:
            if order["id"] == order_id:
                order["deadline"] = new_deadline
                order["status"] = new_status
                nexus_db.db.upsert_pedido(order)
                return True
        return False

    def add_order(self, cliente, producto, hora_entrega_str):
        now = datetime.datetime.now()
        text = str(hora_entrega_str).strip()
        deadline = None
        
        # Lógica de parsing de fecha (Mantenida igual)
        if "mañana" in text.lower():
            target_date = now.date() + datetime.timedelta(days=1)
            try:
                import re
                hora_match = re.search(r"(\d{1,2})[:\s](\d{2})", text)
                if hora_match:
                    target_time = datetime.time(int(hora_match.group(1)), int(hora_match.group(2)))
                else:
                    target_time = datetime.time(14, 0)
            except Exception:
                target_time = datetime.time(14, 0)
            deadline = datetime.datetime.combine(target_date, target_time)
        
        if deadline is None:
            try:
                deadline = datetime.datetime.strptime(text, "%d/%m %H:%M")
                year = now.year
                deadline = deadline.replace(year=year)
            except Exception:
                deadline = None
        
        if deadline is None:
            try:
                target_time = datetime.datetime.strptime(text, "%H:%M").time()
                deadline = datetime.datetime.combine(now.date(), target_time)
                if deadline < now:
                    deadline = deadline + datetime.timedelta(days=1)
            except Exception:
                target_date = now.date() + datetime.timedelta(days=1)
                deadline = datetime.datetime.combine(target_date, datetime.time(14, 0))
                
        new_order = {
            "id": int(time.time()),
            "cliente": cliente,
            "producto": producto,
            "deadline": deadline.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "PENDIENTE",
            "area": "GENERAL",
            "notified_1h": False,
            "notified_15m": False,
            "insistent_level": 0,
            "last_nag_time": 0.0,
        }
        
        # Auto-detectar área
        prod_lower = producto.lower()
        if "taza" in prod_lower or "playera" in prod_lower or "gorra" in prod_lower or "termo" in prod_lower:
            new_order["area"] = "SUBLIMACION"
        elif "corte" in prod_lower or "grabado" in prod_lower or "sello" in prod_lower or "mdf" in prod_lower or "caja" in prod_lower:
            new_order["area"] = "LASER"
            
        nexus_db.db.upsert_pedido(new_order)
        self.load_orders()
        
        dia_str = "mañana" if deadline.date() > now.date() else "hoy"
        return f"Agendado. {producto} para {cliente}, entrega {dia_str} a las {deadline.strftime('%H:%M')}."

    def get_pending(self):
        self.load_orders()
        pending = [o for o in self.orders if o["status"] == "PENDIENTE"]
        pending.sort(key=lambda x: x["deadline"])
        return pending

    def check_deadlines(self):
        self.load_orders()
        alerts = []
        now = datetime.datetime.now()
        
        for order in self.orders:
            if order["status"] != "PENDIENTE": continue
            
            try:
                deadline = datetime.datetime.strptime(order["deadline"], "%Y-%m-%d %H:%M:%S")
            except: continue

            time_left = (deadline - now).total_seconds() / 60 
            updated = False
            
            if 55 <= time_left <= 65 and not order.get("notified_1h"):
                alerts.append(f"Atención: El pedido de {order['cliente']} ({order['producto']}) se entrega en 1 hora.")
                order["notified_1h"] = True
                updated = True
            
            elif 10 <= time_left <= 20 and not order.get("notified_15m"):
                alerts.append(f"Urgente: Pedido de {order['cliente']} vence en 15 minutos.")
                order["notified_15m"] = True
                updated = True
                
            elif time_left < 0:
                insistent_gap = 5 
                last_nag = float(order.get("last_nag_time", 0))
                
                if time.time() - last_nag > (insistent_gap * 60):
                    order["insistent_level"] = int(order.get("insistent_level", 0)) + 1
                    msg = f"Alerta crítica: El pedido de {order['cliente']} ya venció."
                    alerts.append(msg)
                    order["last_nag_time"] = time.time()
                    updated = True

            if updated:
                nexus_db.db.upsert_pedido(order)
            
        return alerts

    def mark_ready(self, cliente_o_id):
        self.load_orders()
        for order in self.orders:
            if str(cliente_o_id).lower() in order["cliente"].lower() and order["status"] == "PENDIENTE":
                order["status"] = "LISTO"
                nexus_db.db.upsert_pedido(order)
                return f"Pedido de {order['cliente']} marcado como LISTO."
        return "No encontré ese pedido pendiente."

manager = OrderManager()
