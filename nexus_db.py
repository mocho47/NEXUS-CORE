import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv
import requests

# Cargar entorno si no está cargado
load_dotenv()

# Configuración de Supabase
# (Idealmente estas keys deberían estar en variables de entorno seguras)
SUPABASE_URL = (
    os.environ.get("SUPABASE_URL")
    or os.environ.get("SUPABASE_PROJECT_URL")
    or os.environ.get("SUPABASE_REST_URL")
    or ""
).strip()
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")  # Service Role o Anon Key según corresponda

PRIVACY_MODE = os.environ.get("NEXUS_PRIVACY_MODE", "supervised").strip().lower()
DISABLE_CLOUD = os.environ.get("NEXUS_DISABLE_CLOUD", "0").strip() in ("1", "true", "yes")

class NexusDB:
    def __init__(self):
        self.client = None
        self.connect()

    def connect(self):
        try:
            if PRIVACY_MODE == "offline" or DISABLE_CLOUD:
                print("[DB] Modo privado/offline: nube deshabilitada.")
                return
            if not SUPABASE_URL:
                print("[DB] ADVERTENCIA: No hay SUPABASE_URL en variables de entorno.")
                return
            if not SUPABASE_KEY:
                print("[DB] ADVERTENCIA: No hay SUPABASE_KEY en variables de entorno.")
                return
            self.client = create_client(SUPABASE_URL, SUPABASE_KEY)
            print("[DB] Conexión a Nube (Supabase) establecida.")
        except Exception as e:
            print(f"[DB ERROR] Fallo al conectar: {e}")

    # --- MARCAS E IDENTIDAD ---
    def get_brands(self):
        """Descarga la lista de marcas y sus activos digitales"""
        if not self.client: return {}
        try:
            response = self.client.table('brands').select("*").execute()
            # Convertir a formato diccionario {code: data} para acceso rápido
            brands_dict = {}
            for item in response.data:
                brands_dict[item['code']] = item
            return brands_dict
        except Exception as e:
            print(f"[DB] Error obteniendo marcas: {e}")
            return {}

    # --- MATERIALES Y PRECIOS ---
    def get_materials(self):
        """Descarga la lista de materiales actualizada"""
        if not self.client: return {}
        try:
            response = self.client.table('materials').select("*").execute()
            # Convertir a formato diccionario {name: data}
            mat_dict = {}
            for item in response.data:
                mat_dict[item['name']] = item
            return mat_dict
        except Exception as e:
            print(f"[DB] Error obteniendo materiales: {e}")
            return {}

    def keepalive_ping_http(self, timeout_sec: int = 8):
        """Ping liviano para evitar pausa automática por inactividad.

        Usa HTTP directo con timeout para evitar bloqueos.
        Retorna (ok:bool, message:str)
        """
        try:
            if PRIVACY_MODE == "offline" or DISABLE_CLOUD:
                return False, "cloud_disabled"
            if not SUPABASE_URL:
                return False, "missing_SUPABASE_URL"
            if not SUPABASE_KEY:
                return False, "missing_SUPABASE_KEY"

            # Intentar tablas conocidas (no destructivo, 1 fila máx)
            tables = ["materials", "orders", "brands", "products"]
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
            }

            last_exc: str | None = None

            for t in tables:
                url = f"{SUPABASE_URL}/rest/v1/{t}?select=id&limit=1"
                try:
                    r = requests.get(url, headers=headers, timeout=max(2, int(timeout_sec)))
                    if 200 <= r.status_code < 300:
                        return True, f"ok:{t}:{r.status_code}"
                    # 404/401/etc: probar siguiente
                except Exception as e:
                    last_exc = str(e)
                    continue

            if last_exc:
                return False, f"http_failed:{last_exc}"
            return False, "no_table_ok"
        except Exception as e:
            return False, str(e)

    # --- GESTIÓN DE NODOS (PCs) ---
    def register_node(self, node_name):
        """Registra o actualiza el estado de esta PC en la nube"""
        if not self.client: return
        try:
            import socket
            ip = socket.gethostbyname(socket.gethostname())
            
            data = {
                "node_name": node_name,
                "ip_address": ip,
                "status": "online",
                "last_seen": "now()"
            }
            # Upsert (Insertar o Actualizar)
            self.client.table('nexus_nodes').upsert(data, on_conflict="node_name").execute()
            print(f"[DB] Nodo '{node_name}' sincronizado.")
        except Exception as e:
            print(f"[DB] Error registrando nodo: {e}")

    # --- PEDIDOS Y VENTAS (HYBRID) ---
    def get_pedidos(self):
        """Obtiene pedidos pendientes (Nube con fallback Local)"""
        orders = []
        # 1. Intentar Nube
        if self.client:
            try:
                # Traer solo pendientes para no saturar
                response = self.client.table('orders').select("*").neq('status', 'ENTREGADO').execute()
                orders = response.data
                print(f"[DB] {len(orders)} pedidos descargados de la nube.")
                # Actualizar backup local
                self._save_local_backup(orders)
                return orders
            except Exception as e:
                print(f"[DB WARN] Fallo nube pedidos: {e}")
        
        # 2. Fallback Local
        return self._load_local_backup()

    def upsert_pedido(self, order_data):
        """Guarda o actualiza un pedido"""
        # 1. Nube
        if self.client:
            try:
                self.client.table('orders').upsert(order_data).execute()
                print(f"[DB] Pedido {order_data.get('cliente')} sincronizado.")
            except Exception as e:
                print(f"[DB ERROR] No se pudo subir pedido: {e}")
        
        # 2. Local (Siempre)
        # Cargar existentes, actualizar este, guardar
        current = self._load_local_backup()
        # Buscar y reemplazar o agregar
        found = False
        for i, o in enumerate(current):
            if o['id'] == order_data['id']:
                current[i] = order_data
                found = True
                break
        if not found:
            current.append(order_data)
        self._save_local_backup(current)

    # --- UTILIDADES LOCALES ---
    def _save_local_backup(self, orders):
        self._save_json_backup("pedidos_backup.json", orders)

    def _load_local_backup(self):
        return self._load_json_backup("pedidos_backup.json")

    # --- CLIENTES / CRM ---
    def get_clientes(self):
        """Obtiene lista de clientes (Nube con fallback local)"""
        if self.client:
            try:
                response = self.client.table('clientes').select("*").execute()
                clientes = response.data
                self._save_json_backup("clientes_backup.json", clientes)
                return clientes
            except Exception as e:
                print(f"[DB WARN] Fallo nube clientes: {e}")
        return self._load_json_backup("clientes_backup.json")

    def upsert_cliente(self, cliente_data):
        """Guarda o actualiza un cliente"""
        if self.client:
            try:
                self.client.table('clientes').upsert(cliente_data).execute()
            except Exception as e:
                print(f"[DB WARN] No se pudo sincronizar cliente en nube: {e}")
        current = self._load_json_backup("clientes_backup.json")
        found = False
        for i, c in enumerate(current):
            if c.get('id') == cliente_data.get('id'):
                current[i] = cliente_data
                found = True
                break
        if not found:
            current.append(cliente_data)
        self._save_json_backup("clientes_backup.json", current)

    # --- STOCK / INVENTARIO ---
    def get_stock(self):
        """Obtiene inventario actual (Nube con fallback local)"""
        if self.client:
            try:
                response = self.client.table('stock').select("*").execute()
                stock = response.data
                self._save_json_backup("stock_backup.json", stock)
                return stock
            except Exception as e:
                print(f"[DB WARN] Fallo nube stock: {e}")
        return self._load_json_backup("stock_backup.json")

    def upsert_stock_item(self, item_data):
        """Guarda o actualiza un item de inventario"""
        if self.client:
            try:
                self.client.table('stock').upsert(item_data).execute()
            except Exception as e:
                print(f"[DB WARN] No se pudo sincronizar stock en nube: {e}")
        current = self._load_json_backup("stock_backup.json")
        found = False
        for i, item in enumerate(current):
            if item.get('id') == item_data.get('id'):
                current[i] = item_data
                found = True
                break
        if not found:
            current.append(item_data)
        self._save_json_backup("stock_backup.json", current)

    # --- UTILIDADES JSON GENÉRICAS ---
    def _save_json_backup(self, filename, data):
        try:
            path = os.path.join(os.path.dirname(__file__), "CONFIG", filename)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[DB BACKUP ERROR] {filename}: {e}")

    def _load_json_backup(self, filename):
        try:
            path = os.path.join(os.path.dirname(__file__), "CONFIG", filename)
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except: pass
        return []

    # --- PRODUCTOS Y CATÁLOGO (AOZOOM/ILLUMA) ---
    def get_products(self, category=None):
        """Obtiene el catálogo de productos"""
        if not self.client: return []
        try:
            query = self.client.table('products').select("*")
            if category:
                query = query.eq('category', category)
            
            response = query.execute()
            return response.data
        except Exception as e:
            print(f"[DB ERROR] Error obteniendo productos: {e}")
            return []

    def get_product_price(self, product_name, price_type='public_price'):
        """Busca precio de un producto específico"""
        # price_type puede ser: 'public_price', 'installer_price', 'installed_price'
        if not self.client: return 0
        try:
            # Búsqueda flexible (ilike)
            response = self.client.table('products').select(price_type).ilike('name', f'%{product_name}%').limit(1).execute()
            if response.data:
                return response.data[0].get(price_type, 0)
        except: pass
        return 0

# Instancia Global
db = NexusDB()
