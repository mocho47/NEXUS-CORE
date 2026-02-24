
import sys
try:
    import supabase
    print("Supabase library is installed.")
except ImportError:
    print("Supabase library is NOT installed.")
    sys.exit(1)

from nexus_db import db
if db.connected:
    print("Connection to Supabase SUCCESSFUL.")
    try:
        # Try to fetch from 'pedidos' to see if table exists
        db.supabase.table("pedidos").select("*").limit(1).execute()
        print("Table 'pedidos' EXISTS.")
    except Exception as e:
        print(f"Table 'pedidos' CHECK FAILED: {e}")
else:
    print("Connection to Supabase FAILED.")
