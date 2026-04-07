"""
NEXUS v3 - Utilidades de base de datos SQLite
Desarrollado por Simplex

Este modulo proporciona funciones asincronas para interactuar con la base de datos
SQLite de NEXUS v3. Utiliza aiosqlite para operaciones no bloqueantes y modo WAL
para mejor rendimiento en operaciones concurrentes.
"""

import logging
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

import aiosqlite

# Configuracion del logger
logger = logging.getLogger("nexus.database")


# --- Definiciones de tablas SQL ---

SQL_CREATE_SESSIONS = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    personality TEXT NOT NULL DEFAULT 'nexus',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

SQL_CREATE_MESSAGES = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);
"""

SQL_CREATE_USER_MEMORY = """
CREATE TABLE IF NOT EXISTS user_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'preference' CHECK(category IN ('personal', 'business', 'preference', 'habit')),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

SQL_CREATE_CLIENTS = """
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    business TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

SQL_CREATE_PRODUCTS = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business TEXT NOT NULL CHECK(business IN ('atf', 'milens', 'canbusfix')),
    name TEXT NOT NULL,
    price REAL DEFAULT 0.0,
    description TEXT,
    stock INTEGER DEFAULT 0
);
"""

SQL_CREATE_ORDERS = """
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    business TEXT NOT NULL,
    items_json TEXT NOT NULL,
    total REAL NOT NULL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);
"""

SQL_CREATE_MISSIONS = """
CREATE TABLE IF NOT EXISTS missions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    points INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',
    assigned_to TEXT,
    created_by TEXT,
    due_date TIMESTAMP,
    evidence TEXT,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

SQL_CREATE_MOTOR_STATUS = """
CREATE TABLE IF NOT EXISTS motor_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    motor_name TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'detenido',
    last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uptime_seconds INTEGER DEFAULT 0,
    tasks_completed INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0
);
"""

# Indices para optimizar consultas frecuentes
SQL_CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, timestamp);",
    "CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);",
    "CREATE INDEX IF NOT EXISTS idx_user_memory_category ON user_memory(category);",
    "CREATE INDEX IF NOT EXISTS idx_clients_business ON clients(business);",
    "CREATE INDEX IF NOT EXISTS idx_products_business ON products(business);",
    "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);",
    "CREATE INDEX IF NOT EXISTS idx_orders_client ON orders(client_id);",
    "CREATE INDEX IF NOT EXISTS idx_missions_status ON missions(status);",
    "CREATE INDEX IF NOT EXISTS idx_motor_status_name ON motor_status(motor_name);",
]

TODAS_LAS_TABLAS = [
    SQL_CREATE_SESSIONS,
    SQL_CREATE_MESSAGES,
    SQL_CREATE_USER_MEMORY,
    SQL_CREATE_CLIENTS,
    SQL_CREATE_PRODUCTS,
    SQL_CREATE_ORDERS,
    SQL_CREATE_MISSIONS,
    SQL_CREATE_MOTOR_STATUS,
]


async def init_db(db_path: str) -> bool:
    """
    Inicializa la base de datos SQLite con modo WAL y crea todas las tablas necesarias.

    Args:
        db_path: Ruta al archivo de base de datos SQLite.

    Returns:
        True si la inicializacion fue exitosa, False en caso contrario.
    """
    logger.info("Iniciando base de datos en: %s", db_path)
    try:
        # Asegurar que el directorio padre existe
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        async with aiosqlite.connect(db_path) as db:
            # Activar modo WAL para mejor rendimiento en lectura/escritura concurrente
            await db.execute("PRAGMA journal_mode=WAL;")
            # Activar claves foraneas
            await db.execute("PRAGMA foreign_keys=ON;")
            # Configurar timeout para evitar bloqueos
            await db.execute("PRAGMA busy_timeout=5000;")

            # Crear todas las tablas
            for sql in TODAS_LAS_TABLAS:
                await db.execute(sql)

            # Crear indices
            for sql in SQL_CREATE_INDEXES:
                await db.execute(sql)

            await db.commit()

        logger.info("Base de datos inicializada correctamente con %d tablas.", len(TODAS_LAS_TABLAS))
        return True

    except sqlite3.Error as e:
        logger.error("Error al inicializar la base de datos: %s", e)
        return False
    except Exception as e:
        logger.error("Error inesperado al inicializar la base de datos: %s", e)
        return False


async def get_session_messages(session_id: int, limit: int = 30) -> list[dict]:
    """
    Obtiene los mensajes de una sesion especifica, ordenados por timestamp.

    Args:
        session_id: Identificador unico de la sesion.
        limit: Numero maximo de mensajes a recuperar (por defecto 30).

    Returns:
        Lista de diccionarios con los mensajes de la sesion.
    """
    logger.debug("Obteniendo mensajes de la sesion %d (limite: %d)", session_id, limit)
    try:
        async with aiosqlite.connect("nexus.db") as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT id, session_id, role, content, timestamp FROM messages "
                "WHERE session_id = ? ORDER BY timestamp ASC LIMIT ?",
                (session_id, limit)
            )
            rows = await cursor.fetchall()
            mensajes = [dict(row) for row in rows]
            logger.debug("Se recuperaron %d mensajes de la sesion %d.", len(mensajes), session_id)
            return mensajes
    except sqlite3.Error as e:
        logger.error("Error al obtener mensajes de la sesion %d: %s", session_id, e)
        return []
    except Exception as e:
        logger.error("Error inesperado al obtener mensajes: %s", e)
        return []


async def save_message(session_id: int, role: str, content: str) -> Optional[int]:
    """
    Guarda un nuevo mensaje en la base de datos.

    Args:
        session_id: Identificador unico de la sesion.
        role: Rol del emisor ('user', 'assistant' o 'system').
        content: Contenido del mensaje.

    Returns:
        Identificador del mensaje insertado, o None si ocurrio un error.
    """
    if role not in ("user", "assistant", "system"):
        logger.error("Rol invalido: %s. Roles permitidos: user, assistant, system.", role)
        return None

    logger.debug("Guardando mensaje [%s] en sesion %d (longitud: %d)", role, session_id, len(content))
    try:
        async with aiosqlite.connect("nexus.db") as db:
            cursor = await db.execute(
                "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
                (session_id, role, content)
            )
            await db.commit()
            msg_id = cursor.lastrowid
            logger.debug("Mensaje guardado con ID: %d", msg_id)
            return msg_id
    except sqlite3.Error as e:
        logger.error("Error al guardar mensaje en sesion %d: %s", session_id, e)
        return None
    except Exception as e:
        logger.error("Error inesperado al guardar mensaje: %s", e)
        return None


async def get_user_memory(key: Optional[str] = None, category: Optional[str] = None) -> list[dict]:
    """
    Recupera memorias del usuario, opcionalmente filtradas por clave o categoria.

    Args:
        key: Clave especifica de la memoria (opcional).
        category: Categoria de la memoria: 'personal', 'business', 'preference', 'habit' (opcional).

    Returns:
        Lista de diccionarios con las memorias encontradas.
    """
    logger.debug("Buscando memoria: clave=%s, categoria=%s", key, category)
    try:
        async with aiosqlite.connect("nexus.db") as db:
            db.row_factory = aiosqlite.Row

            if key:
                cursor = await db.execute(
                    "SELECT id, key, value, category, updated_at FROM user_memory WHERE key = ?",
                    (key,)
                )
            elif category:
                cursor = await db.execute(
                    "SELECT id, key, value, category, updated_at FROM user_memory WHERE category = ?",
                    (category,)
                )
            else:
                cursor = await db.execute(
                    "SELECT id, key, value, category, updated_at FROM user_memory ORDER BY updated_at DESC"
                )

            rows = await cursor.fetchall()
            memorias = [dict(row) for row in rows]
            logger.debug("Se encontraron %d memorias.", len(memorias))
            return memorias
    except sqlite3.Error as e:
        logger.error("Error al obtener memoria del usuario: %s", e)
        return []
    except Exception as e:
        logger.error("Error inesperado al obtener memoria: %s", e)
        return []


async def save_user_memory(key: str, value: str, category: str = "preference") -> bool:
    """
    Guarda o actualiza una memoria del usuario. Usa INSERT OR REPLACE para
    actualizar automaticamente si la clave ya existe.

    Args:
        key: Clave unica de la memoria.
        value: Valor de la memoria a almacenar.
        category: Categoria de la memoria ('personal', 'business', 'preference', 'habit').

    Returns:
        True si la operacion fue exitosa, False en caso contrario.
    """
    if category not in ("personal", "business", "preference", "habit"):
        logger.error("Categoria de memoria invalida: %s", category)
        return False

    logger.info("Guardando memoria: [%s] %s (categoria: %s)", key, value[:50], category)
    try:
        async with aiosqlite.connect("nexus.db") as db:
            await db.execute(
                "INSERT INTO user_memory (key, value, category, updated_at) "
                "VALUES (?, ?, ?, CURRENT_TIMESTAMP) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value, "
                "category = excluded.category, updated_at = CURRENT_TIMESTAMP",
                (key, value, category)
            )
            await db.commit()
            logger.info("Memoria guardada correctamente: %s", key)
            return True
    except sqlite3.Error as e:
        logger.error("Error al guardar memoria '%s': %s", key, e)
        return False
    except Exception as e:
        logger.error("Error inesperado al guardar memoria: %s", e)
        return False


async def search_user_memory(query: str) -> list[dict]:
    """
    Busca memorias del usuario usando coincidencia de texto parcial.

    Args:
        query: Texto de busqueda para encontrar memorias relacionadas.

    Returns:
        Lista de diccionarios con las memorias que coinciden con la busqueda.
    """
    logger.debug("Buscando memorias con consulta: '%s'", query)
    try:
        async with aiosqlite.connect("nexus.db") as db:
            db.row_factory = aiosqlite.Row
            # Buscar en clave y valor usando LIKE con comodines
            patron = f"%{query}%"
            cursor = await db.execute(
                "SELECT id, key, value, category, updated_at FROM user_memory "
                "WHERE key LIKE ? OR value LIKE ? ORDER BY updated_at DESC",
                (patron, patron)
            )
            rows = await cursor.fetchall()
            resultados = [dict(row) for row in rows]
            logger.debug("Busqueda de memoria: %d resultados para '%s'.", len(resultados), query)
            return resultados
    except sqlite3.Error as e:
        logger.error("Error al buscar memorias '%s': %s", query, e)
        return []
    except Exception as e:
        logger.error("Error inesperado al buscar memorias: %s", e)
        return []


async def get_all_clients(business: Optional[str] = None) -> list[dict]:
    """
    Obtiene todos los clientes, opcionalmente filtrados por negocio.

    Args:
        business: Nombre del negocio para filtrar (opcional).

    Returns:
        Lista de diccionarios con la informacion de los clientes.
    """
    logger.debug("Obteniendo clientes (negocio: %s)", business)
    try:
        async with aiosqlite.connect("nexus.db") as db:
            db.row_factory = aiosqlite.Row

            if business:
                cursor = await db.execute(
                    "SELECT id, name, phone, email, business, notes, created_at "
                    "FROM clients WHERE business = ? ORDER BY name ASC",
                    (business,)
                )
            else:
                cursor = await db.execute(
                    "SELECT id, name, phone, email, business, notes, created_at "
                    "FROM clients ORDER BY name ASC"
                )

            rows = await cursor.fetchall()
            clientes = [dict(row) for row in rows]
            logger.debug("Se recuperaron %d clientes.", len(clientes))
            return clientes
    except sqlite3.Error as e:
        logger.error("Error al obtener clientes: %s", e)
        return []
    except Exception as e:
        logger.error("Error inesperado al obtener clientes: %s", e)
        return []


async def save_client(data: dict) -> Optional[int]:
    """
    Guarda un nuevo cliente en la base de datos.

    Args:
        data: Diccionario con los datos del cliente. Claves esperadas:
              'name' (requerido), 'phone', 'email', 'business', 'notes'.

    Returns:
        Identificador del cliente insertado, o None si ocurrio un error.
    """
    if not data or "name" not in data:
        logger.error("Datos de cliente invalidos: se requiere 'name'.")
        return None

    logger.info("Guardando cliente: %s", data.get("name", "desconocido"))
    try:
        async with aiosqlite.connect("nexus.db") as db:
            cursor = await db.execute(
                "INSERT INTO clients (name, phone, email, business, notes) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    data.get("name", ""),
                    data.get("phone"),
                    data.get("email"),
                    data.get("business"),
                    data.get("notes"),
                )
            )
            await db.commit()
            client_id = cursor.lastrowid
            logger.info("Cliente guardado con ID: %d", client_id)
            return client_id
    except sqlite3.Error as e:
        logger.error("Error al guardar cliente '%s': %s", data.get("name"), e)
        return None
    except Exception as e:
        logger.error("Error inesperado al guardar cliente: %s", e)
        return None


async def get_products(business: Optional[str] = None) -> list[dict]:
    """
    Obtiene todos los productos, opcionalmente filtrados por negocio.

    Args:
        business: Negocio para filtrar ('atf', 'milens', 'canbusfix') (opcional).

    Returns:
        Lista de diccionarios con la informacion de los productos.
    """
    logger.debug("Obteniendo productos (negocio: %s)", business)
    try:
        async with aiosqlite.connect("nexus.db") as db:
            db.row_factory = aiosqlite.Row

            if business:
                cursor = await db.execute(
                    "SELECT id, business, name, price, description, stock "
                    "FROM products WHERE business = ? ORDER BY name ASC",
                    (business,)
                )
            else:
                cursor = await db.execute(
                    "SELECT id, business, name, price, description, stock "
                    "FROM products ORDER BY business, name ASC"
                )

            rows = await cursor.fetchall()
            productos = [dict(row) for row in rows]
            logger.debug("Se recuperaron %d productos.", len(productos))
            return productos
    except sqlite3.Error as e:
        logger.error("Error al obtener productos: %s", e)
        return []
    except Exception as e:
        logger.error("Error inesperado al obtener productos: %s", e)
        return []


async def save_product(data: dict) -> Optional[int]:
    """
    Guarda un nuevo producto en la base de datos.

    Args:
        data: Diccionario con los datos del producto. Claves esperadas:
              'business' (requerido: 'atf'|'milens'|'canbusfix'),
              'name' (requerido), 'price', 'description', 'stock'.

    Returns:
        Identificador del producto insertado, o None si ocurrio un error.
    """
    if not data or "name" not in data or "business" not in data:
        logger.error("Datos de producto invalidos: se requieren 'name' y 'business'.")
        return None

    if data["business"] not in ("atf", "milens", "canbusfix"):
        logger.error("Negocio de producto invalido: %s", data["business"])
        return None

    logger.info("Guardando producto: %s (%s)", data.get("name"), data.get("business"))
    try:
        async with aiosqlite.connect("nexus.db") as db:
            cursor = await db.execute(
                "INSERT INTO products (business, name, price, description, stock) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    data.get("business"),
                    data.get("name", ""),
                    data.get("price", 0.0),
                    data.get("description"),
                    data.get("stock", 0),
                )
            )
            await db.commit()
            product_id = cursor.lastrowid
            logger.info("Producto guardado con ID: %d", product_id)
            return product_id
    except sqlite3.Error as e:
        logger.error("Error al guardar producto '%s': %s", data.get("name"), e)
        return None
    except Exception as e:
        logger.error("Error inesperado al guardar producto: %s", e)
        return None


async def get_orders(status: Optional[str] = None, limit: int = 50) -> list[dict]:
    """
    Obtiene pedidos, opcionalmente filtrados por estado.

    Args:
        status: Estado del pedido para filtrar (opcional).
        limit: Numero maximo de pedidos a recuperar (por defecto 50).

    Returns:
        Lista de diccionarios con la informacion de los pedidos.
    """
    logger.debug("Obteniendo pedidos (estado: %s, limite: %d)", status, limit)
    try:
        async with aiosqlite.connect("nexus.db") as db:
            db.row_factory = aiosqlite.Row

            if status:
                cursor = await db.execute(
                    "SELECT o.id, o.client_id, o.business, o.items_json, o.total, "
                    "o.status, o.created_at, c.name as client_name "
                    "FROM orders o LEFT JOIN clients c ON o.client_id = c.id "
                    "WHERE o.status = ? ORDER BY o.created_at DESC LIMIT ?",
                    (status, limit)
                )
            else:
                cursor = await db.execute(
                    "SELECT o.id, o.client_id, o.business, o.items_json, o.total, "
                    "o.status, o.created_at, c.name as client_name "
                    "FROM orders o LEFT JOIN clients c ON o.client_id = c.id "
                    "ORDER BY o.created_at DESC LIMIT ?",
                    (limit,)
                )

            rows = await cursor.fetchall()
            pedidos = [dict(row) for row in rows]
            logger.debug("Se recuperaron %d pedidos.", len(pedidos))
            return pedidos
    except sqlite3.Error as e:
        logger.error("Error al obtener pedidos: %s", e)
        return []
    except Exception as e:
        logger.error("Error inesperado al obtener pedidos: %s", e)
        return []


async def save_order(data: dict) -> Optional[int]:
    """
    Guarda un nuevo pedido en la base de datos.

    Args:
        data: Diccionario con los datos del pedido. Claves esperadas:
              'client_id' (requerido), 'business' (requerido),
              'items_json' (requerido), 'total', 'status'.

    Returns:
        Identificador del pedido insertado, o None si ocurrio un error.
    """
    if not data or "client_id" not in data or "business" not in data or "items_json" not in data:
        logger.error("Datos de pedido invalidos: se requieren 'client_id', 'business' e 'items_json'.")
        return None

    logger.info("Guardando pedido para cliente %d (%s)", data.get("client_id"), data.get("business"))
    try:
        async with aiosqlite.connect("nexus.db") as db:
            cursor = await db.execute(
                "INSERT INTO orders (client_id, business, items_json, total, status) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    data.get("client_id"),
                    data.get("business"),
                    data.get("items_json"),
                    data.get("total", 0.0),
                    data.get("status", "pending"),
                )
            )
            await db.commit()
            order_id = cursor.lastrowid
            logger.info("Pedido guardado con ID: %d", order_id)
            return order_id
    except sqlite3.Error as e:
        logger.error("Error al guardar pedido: %s", e)
        return None
    except Exception as e:
        logger.error("Error inesperado al guardar pedido: %s", e)
        return None


async def update_motor_status(motor_name: str, status: str, **kwargs) -> bool:
    """
    Actualiza el estado de un motor. Si el motor no existe, lo crea automaticamente.

    Args:
        motor_name: Nombre unico del motor.
        status: Nuevo estado del motor.
        **kwargs: Campos adicionales a actualizar:
                  uptime_seconds, tasks_completed, errors_count.

    Returns:
        True si la operacion fue exitosa, False en caso contrario.
    """
    logger.info("Actualizando motor '%s' a estado: %s", motor_name, status)
    try:
        async with aiosqlite.connect("nexus.db") as db:
            # Intentar actualizar registro existente
            cursor = await db.execute(
                "UPDATE motor_status SET status = ?, last_check = CURRENT_TIMESTAMP, "
                "uptime_seconds = COALESCE(?, uptime_seconds), "
                "tasks_completed = COALESCE(?, tasks_completed), "
                "errors_count = COALESCE(?, errors_count) "
                "WHERE motor_name = ?",
                (
                    status,
                    kwargs.get("uptime_seconds"),
                    kwargs.get("tasks_completed"),
                    kwargs.get("errors_count"),
                    motor_name,
                )
            )

            if cursor.rowcount == 0:
                # El motor no existe, crearlo
                logger.debug("Motor '%s' no existe, creando nuevo registro.", motor_name)
                await db.execute(
                    "INSERT INTO motor_status "
                    "(motor_name, status, uptime_seconds, tasks_completed, errors_count) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        motor_name,
                        status,
                        kwargs.get("uptime_seconds", 0),
                        kwargs.get("tasks_completed", 0),
                        kwargs.get("errors_count", 0),
                    )
                )

            await db.commit()
            logger.info("Motor '%s' actualizado correctamente.", motor_name)
            return True
    except sqlite3.Error as e:
        logger.error("Error al actualizar motor '%s': %s", motor_name, e)
        return False
    except Exception as e:
        logger.error("Error inesperado al actualizar motor: %s", e)
        return False


async def get_motor_status(motor_name: str) -> Optional[dict]:
    """
    Obtiene el estado actual de un motor especifico.

    Args:
        motor_name: Nombre unico del motor.

    Returns:
        Diccionario con el estado del motor, o None si no existe o hay error.
    """
    logger.debug("Consultando estado del motor: %s", motor_name)
    try:
        async with aiosqlite.connect("nexus.db") as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT id, motor_name, status, last_check, uptime_seconds, "
                "tasks_completed, errors_count FROM motor_status WHERE motor_name = ?",
                (motor_name,)
            )
            row = await cursor.fetchone()
            if row:
                resultado = dict(row)
                logger.debug("Estado del motor '%s': %s", motor_name, resultado.get("status"))
                return resultado
            else:
                logger.debug("Motor '%s' no encontrado en la base de datos.", motor_name)
                return None
    except sqlite3.Error as e:
        logger.error("Error al obtener estado del motor '%s': %s", motor_name, e)
        return None
    except Exception as e:
        logger.error("Error inesperado al obtener estado del motor: %s", e)
        return None


def backup_db(db_path: str, backup_dir: str) -> dict:
    """
    Crea una copia de seguridad de la base de datos con marca de tiempo.
    Esta funcion es sincrona porque shutil.copy2 es una operacion rapida del sistema.

    Args:
        db_path: Ruta al archivo de base de datos original.
        backup_dir: Directorio donde se guardara la copia de seguridad.

    Returns:
        Diccionario con: {'success': bool, 'backup_path': str, 'message': str}
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_filename = Path(db_path).stem
    backup_filename = f"{db_filename}_backup_{timestamp}.db"
    backup_path = str(Path(backup_dir) / backup_filename)

    logger.info("Creando copia de seguridad de la base de datos: %s", backup_path)

    try:
        # Verificar que el archivo de base de datos existe
        if not Path(db_path).exists():
            logger.error("El archivo de base de datos no existe: %s", db_path)
            return {
                "success": False,
                "backup_path": "",
                "message": f"El archivo de base de datos no existe: {db_path}"
            }

        # Crear directorio de respaldo si no existe
        Path(backup_dir).mkdir(parents=True, exist_ok=True)

        # Copiar el archivo de base de datos
        shutil.copy2(db_path, backup_path)

        # Verificar tamano del archivo copiado
        original_size = Path(db_path).stat().st_size
        backup_size = Path(backup_path).stat().st_size

        if backup_size == 0:
            logger.error("La copia de seguridad creada esta vacia: %s", backup_path)
            return {
                "success": False,
                "backup_path": backup_path,
                "message": "La copia de seguridad creada esta vacia."
            }

        logger.info(
            "Copia de seguridad creada exitosamente: %s (tamano: %d bytes)",
            backup_path, backup_size
        )

        return {
            "success": True,
            "backup_path": backup_path,
            "message": f"Copia de seguridad creada: {backup_filename} "
                       f"({backup_size / 1024:.1f} KB)"
        }

    except PermissionError as e:
        logger.error("Error de permisos al crear copia de seguridad: %s", e)
        return {
            "success": False,
            "backup_path": "",
            "message": f"Error de permisos: {e}"
        }
    except OSError as e:
        logger.error("Error del sistema al crear copia de seguridad: %s", e)
        return {
            "success": False,
            "backup_path": "",
            "message": f"Error del sistema: {e}"
        }
    except Exception as e:
        logger.error("Error inesperado al crear copia de seguridad: %s", e)
        return {
            "success": False,
            "backup_path": "",
            "message": f"Error inesperado: {e}"
        }
