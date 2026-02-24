import json
import os
import uuid
import nexus_db

class StockManager:
    def __init__(self):
        self.stock = []
        self.load_stock()

    def load_stock(self):
        self.stock = nexus_db.db.get_stock()

    def add_item(self, nombre, cantidad, precio, categoria="GENERAL"):
        """Agrega o actualiza un item en el inventario."""
        self.load_stock()
        nombre_clean = nombre.strip().upper()
        # Buscar si ya existe
        existing = self.get_item(nombre)
        if existing:
            existing["cantidad"] = int(cantidad)
            existing["precio"] = float(precio)
            existing["categoria"] = categoria.upper()
            nexus_db.db.upsert_stock_item(existing)
            self.load_stock()
            return existing
        # Crear nuevo
        item = {
            "id": str(uuid.uuid4()),
            "nombre": nombre_clean,
            "cantidad": int(cantidad),
            "precio": float(precio),
            "categoria": categoria.upper(),
            "updated_at": __import__('datetime').datetime.now().isoformat()
        }
        nexus_db.db.upsert_stock_item(item)
        self.load_stock()
        return item

    def get_item(self, nombre):
        self.load_stock()
        nombre_lower = nombre.lower().strip()
        for item in self.stock:
            if nombre_lower in item.get("nombre", "").lower():
                return item
        return None

    def get_stock_by_category(self, category):
        self.load_stock()
        return [item for item in self.stock if item.get("categoria", "").upper() == category.upper()]

    def update_cantidad(self, nombre, nueva_cantidad):
        """Actualiza solo la cantidad de un item."""
        item = self.get_item(nombre)
        if item:
            item["cantidad"] = int(nueva_cantidad)
            item["updated_at"] = __import__('datetime').datetime.now().isoformat()
            nexus_db.db.upsert_stock_item(item)
            self.load_stock()
            return True
        return False

    def restar_cantidad(self, nombre, cantidad_usada):
        """Resta cantidad al inventario (al vender/usar material)."""
        item = self.get_item(nombre)
        if item:
            nueva = max(0, item.get("cantidad", 0) - int(cantidad_usada))
            return self.update_cantidad(nombre, nueva)
        return False

    def list_bajo_stock(self, minimo=5):
        """Retorna items con cantidad menor al mínimo."""
        self.load_stock()
        return [i for i in self.stock if i.get("cantidad", 0) <= minimo]

manager = StockManager()
