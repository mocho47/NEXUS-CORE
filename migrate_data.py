import json
import nexus_db

def migrate():
    print(">>> MIGRANDO DATOS A SUPABASE <<<")
    nexus_db.db.connect()
    
    # 1. CLIENTES
    print("Migrando Clientes...")
    # Forzamos lectura local
    if os.path.exists(nexus_db.CLIENTES_FILE):
        with open(nexus_db.CLIENTES_FILE, "r", encoding="utf-8") as f:
            local_clientes = json.load(f)
        for nombre, data in local_clientes.items():
            print(f"Subiendo {nombre}...")
            nexus_db.db.upsert_cliente(nombre, data)

    # 2. PEDIDOS
    print("\nMigrando Pedidos...")
    if os.path.exists(nexus_db.PEDIDOS_FILE):
        with open(nexus_db.PEDIDOS_FILE, "r", encoding="utf-8") as f:
            local_pedidos = json.load(f)
        for p in local_pedidos:
            print(f"Subiendo Pedido {p['id']}...")
            nexus_db.db.upsert_pedido(p)

    # 3. INVENTARIO (CONOCIMIENTO)
    print("\nMigrando Conocimiento...")
    if os.path.exists(nexus_db.MATERIALES_FILE):
        with open(nexus_db.MATERIALES_FILE, "r", encoding="utf-8") as f:
            local_mat = json.load(f)
        for key, val in local_mat.items():
            print(f"Subiendo {key}...")
            row = {
                "id": key,
                "nombre": val.get("nombre", "Sin Nombre"),
                "costo_base": val.get("costo_base", 0),
                "precio_sugerido": val.get("precio_sugerido", 0),
                "data": val 
            }
            try:
                nexus_db.db.client.table("inventario").upsert(row).execute()
            except Exception as e:
                print(f"Error en {key}: {e}")

    # 4. STOCK (CANTIDADES)
    print("\nMigrando Stock...")
    if os.path.exists(nexus_db.STOCK_FILE):
        with open(nexus_db.STOCK_FILE, "r", encoding="utf-8") as f:
            local_stock = json.load(f)
        for item, data in local_stock.items():
            print(f"Subiendo {item}...")
            nexus_db.db.upsert_stock_item(item, data)

    print("\n>>> MIGRACIÓN COMPLETADA <<<")

if __name__ == "__main__":
    import os
    migrate()
