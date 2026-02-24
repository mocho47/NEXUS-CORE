import json
import os
import uuid
import nexus_db

class CRMManager:
    def __init__(self):
        self.clientes = []
        self.load_clientes()

    def load_clientes(self):
        self.clientes = nexus_db.db.get_clientes()

    def add_cliente(self, nombre, telefono, email=""):
        """Agrega o actualiza un cliente por nombre."""
        self.load_clientes()
        # Normalizar teléfono: agregar +52 si es número mexicano sin prefijo
        tel = str(telefono).strip().replace(" ", "").replace("-", "")
        if tel.isdigit() and len(tel) == 10:
            tel = "+52" + tel
        # Buscar si ya existe
        existing = self.get_cliente(nombre)
        if existing:
            existing["telefono"] = tel
            if email:
                existing["email"] = email
            nexus_db.db.upsert_cliente(existing)
            self.load_clientes()
            return existing
        # Crear nuevo
        cliente = {
            "id": str(uuid.uuid4()),
            "nombre": nombre.strip().title(),
            "telefono": tel,
            "email": email.strip().lower(),
            "created_at": __import__('datetime').datetime.now().isoformat()
        }
        nexus_db.db.upsert_cliente(cliente)
        self.load_clientes()
        return cliente

    def get_cliente(self, nombre):
        self.load_clientes()
        nombre_lower = nombre.lower().strip()
        for c in self.clientes:
            if nombre_lower in c.get("nombre", "").lower():
                return c
        return None

    def list_clientes(self):
        self.load_clientes()
        return self.clientes

    def delete_cliente(self, nombre):
        """Elimina un cliente por nombre (solo local por ahora)."""
        self.load_clientes()
        original = len(self.clientes)
        self.clientes = [c for c in self.clientes if nombre.lower() not in c.get("nombre", "").lower()]
        if len(self.clientes) < original:
            nexus_db.db._save_json_backup("clientes_backup.json", self.clientes)
            return True
        return False

manager = CRMManager()
