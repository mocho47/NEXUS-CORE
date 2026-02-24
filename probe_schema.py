
from nexus_db import db
import json

def probe():
    db.connect() # Force connection
    if not db.connected:
        print("Not connected.")
        return

    print("--- Probing 'pedidos' ---")
    try:
        res = db.supabase.table("pedidos").select("*").limit(1).execute()
        if res.data:
            print("Columns:", list(res.data[0].keys()))
        else:
            print("Table exists but is empty.")
    except Exception as e:
        print(f"Error: {e}")

    print("\n--- Probing 'inventario' ---")
    try:
        res = db.supabase.table("inventario").select("*").limit(1).execute()
        if res.data:
            print("Columns:", list(res.data[0].keys()))
        else:
            print("Table exists but is empty.")
    except Exception as e:
        print(f"Error: {e}")

    print("\n--- Probing 'clientes' ---")
    try:
        res = db.supabase.table("clientes").select("*").limit(1).execute()
        if res.data:
            print("Columns:", list(res.data[0].keys()))
        else:
            print("Table exists but is empty.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    probe()
