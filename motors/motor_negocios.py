#!/usr/bin/env python3
"""
NEXUS v3 - Motor de Negocios
Simplex - Motor de gestión empresarial (CRM, ventas, inventario)
Puerto: 8003
"""

import logging
import time
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("motor_negocios")

# Intentar importar librerías compartidas
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from lib.config import settings
    from lib.database import db
    logger.info("Configuración y base de datos compartidas cargadas exitosamente")
    USAR_DB_COMPARTIDA = True
except ImportError:
    logger.warning("No se pudo importar módulos compartidos, usando almacenamiento local")
    settings = type('Settings', (), {
        'APP_NAME': 'NEXUS v3',
        'VERSION': '3.0.0',
        'DEBUG': False,
    })()
    USAR_DB_COMPARTIDA = False

# ==================== ALMACENAMIENTO LOCAL ====================
# Base de datos en memoria si no hay BD compartida
clientes_db: Dict[str, dict] = {}
productos_db: Dict[str, dict] = {}
ordenes_db: Dict[str, dict] = {}
notas_rapidas: List[dict] = []

# ==================== DATOS PRE-CARGADOS ====================
NEGOCIOS = {
    "atf": {
        "nombre": "ATF",
        "descripcion": "Automotive Technology & Features",
        "tipo": "automotriz",
        "productos": {
            "X4": {"precio": 2699, "categoria": "pantalla", "descripcion": "Pantalla multimedia Android X4"},
            "X1": {"precio": 3149, "categoria": "pantalla", "descripcion": "Pantalla multimedia Android X1"},
            "X2": {"precio": 2799, "categoria": "pantalla", "descripcion": "Pantalla multimedia Android X2"},
            "X3": {"precio": 3149, "categoria": "pantalla", "descripcion": "Pantalla multimedia Android X3"},
            "Instalacion Basico": {"precio": 800, "categoria": "servicio", "descripcion": "Instalación básica de pantalla"},
            "Instalacion Pro": {"precio": 2500, "categoria": "servicio", "descripcion": "Instalación profesional completa"},
        }
    },
    "milens": {
        "nombre": "Milens",
        "descripcion": "Milens - Diseño y personalización",
        "tipo": "diseno",
        "productos": {
            "Corte Laser": {"precio": None, "categoria": "servicio", "descripcion": "Servicio de corte láser", "precio_min": 50, "precio_max": 500},
            "Sublimacion": {"precio": None, "categoria": "servicio", "descripcion": "Sublimación de prendas y objetos", "precio_min": 30, "precio_max": 300},
            "Cajas MDF": {"precio": None, "categoria": "producto", "descripcion": "Cajas personalizadas en MDF", "precio_min": 80, "precio_max": 600},
            "Cajas Acrilico": {"precio": None, "categoria": "producto", "descripcion": "Cajas personalizadas en acrílico", "precio_min": 120, "precio_max": 800},
            "Llaveros": {"precio": None, "categoria": "producto", "descripcion": "Llaveros personalizados", "precio_min": 15, "precio_max": 80},
        }
    },
    "canbusfix": {
        "nombre": "CanbusFix",
        "descripcion": "CanbusFix - Red de instaladores retrofit nacional",
        "tipo": "automotriz",
        "productos": {
            "Instalacion Retrofit": {"precio": None, "categoria": "servicio", "descripcion": "Instalación de retrofit automotriz", "precio_min": 2500, "precio_max": 8000},
            "Kit Canbus": {"precio": 350, "categoria": "producto", "descripcion": "Kit de interfaz CAN Bus"},
            "Capacitacion": {"precio": 2000, "categoria": "formacion", "descripcion": "Capacitación para instaladores"},
            "Membresia Red": {"precio": 500, "categoria": "membresia", "descripcion": "Membresía mensual a la red de instaladores"},
        }
    }
}

# Cargar productos pre-definidos en la BD local
for _negocio_id, _negocio_data in NEGOCIOS.items():
    for _prod_nombre, _prod_info in _negocio_data["productos"].items():
        _prod_id = str(uuid.uuid4())[:8]
        productos_db[_prod_id] = {
            "id": _prod_id,
            "nombre": _prod_nombre,
            "negocio": _negocio_id,
            "precio": _prod_info.get("precio"),
            "precio_min": _prod_info.get("precio_min"),
            "precio_max": _prod_info.get("precio_max"),
            "categoria": _prod_info["categoria"],
            "descripcion": _prod_info["descripcion"],
            "stock": None,
            "fecha_creacion": datetime.now().isoformat(),
        }

# ==================== ESTADÍSTICAS ====================
motor_stats = {
    "tareas_completadas": 0,
    "tareas_con_error": 0,
    "hora_inicio": time.time(),
    "ultima_actividad": None,
}

app = FastAPI(
    title="Motor de Negocios - NEXUS v3",
    description="Motor de gestión empresarial CRM, ventas e inventario para NEXUS v3",
    version="3.0.0"
)


# Modelos Pydantic
class ExecuteRequest(BaseModel):
    action: str = Field(..., description="Acción a ejecutar")
    data: dict = Field(default_factory=dict, description="Datos de la acción")


class QuickNoteRequest(BaseModel):
    text: str = Field(..., description="Texto de la nota")
    category: str = Field("general", description="Categoría de la nota")


# Funciones auxiliares
def _registrar_actividad():
    motor_stats["ultima_actividad"] = datetime.now().isoformat()


def _actualizar_estadisticas(exito: bool):
    if exito:
        motor_stats["tareas_completadas"] += 1
    else:
        motor_stats["tareas_con_error"] += 1
    _registrar_actividad()


def _obtener_tiempo_actividad() -> str:
    segundos = int(time.time() - motor_stats["hora_inicio"])
    horas = segundos // 3600
    minutos = (segundos % 3600) // 60
    segs = segundos % 60
    return f"{horas}h {minutos}m {segs}s"


# ==================== ACCIONES DE CLIENTES ====================

def add_client(data: dict) -> dict:
    """Agregar un nuevo cliente."""
    try:
        nombre = data.get("nombre", data.get("name", ""))
        email = data.get("email", "")
        telefono = data.get("telefono", data.get("phone", ""))
        negocio = data.get("negocio", "atf")
        notas = data.get("notas", "")

        if not nombre:
            return {"exito": False, "mensaje": "El nombre del cliente es obligatorio", "resultado": None}

        # Verificar duplicado
        for c in clientes_db.values():
            if c.get("email") == email and email:
                return {"exito": False, "mensaje": "Ya existe un cliente con ese email", "resultado": None}

        cliente_id = str(uuid.uuid4())[:8]
        cliente = {
            "id": cliente_id,
            "nombre": nombre,
            "email": email,
            "telefono": telefono,
            "negocio": negocio,
            "notas": notas,
            "fecha_registro": datetime.now().isoformat(),
            "total_compras": 0,
            "total_gastado": 0.0,
        }
        clientes_db[cliente_id] = cliente
        logger.info(f"Cliente registrado: {nombre} (ID: {cliente_id})")

        return {
            "exito": True,
            "mensaje": f"Cliente '{nombre}' registrado exitosamente",
            "resultado": cliente
        }
    except Exception as e:
        logger.error(f"Error al agregar cliente: {e}")
        return {"exito": False, "mensaje": f"Error: {str(e)}", "resultado": None}


def get_clients(data: dict) -> dict:
    """Obtener lista de clientes."""
    try:
        negocio = data.get("negocio", None)
        limite = data.get("limite", data.get("limit", 100))

        lista_clientes = list(clientes_db.values())
        if negocio:
            lista_clientes = [c for c in lista_clientes if c.get("negocio") == negocio]

        lista_clientes = lista_clientes[:limite]

        return {
            "exito": True,
            "mensaje": f"{len(lista_clientes)} clientes encontrados",
            "resultado": {
                "total": len(lista_clientes),
                "clientes": lista_clientes
            }
        }
    except Exception as e:
        logger.error(f"Error al obtener clientes: {e}")
        return {"exito": False, "mensaje": f"Error: {str(e)}", "resultado": None}


def search_client(data: dict) -> dict:
    """Buscar cliente por nombre, email o teléfono."""
    try:
        query = data.get("query", data.get("busqueda", "")).lower().strip()
        if not query:
            return {"exito": False, "mensaje": "Se requiere un término de búsqueda", "resultado": None}

        resultados = []
        for cliente in clientes_db.values():
            if (query in cliente.get("nombre", "").lower() or
                query in cliente.get("email", "").lower() or
                query in cliente.get("telefono", "").lower()):
                resultados.append(cliente)

        return {
            "exito": True,
            "mensaje": f"{len(resultados)} cliente(s) encontrado(s) para '{query}'",
            "resultado": {
                "total": len(resultados),
                "clientes": resultados
            }
        }
    except Exception as e:
        logger.error(f"Error al buscar cliente: {e}")
        return {"exito": False, "mensaje": f"Error: {str(e)}", "resultado": None}


# ==================== ACCIONES DE PRODUCTOS ====================

def add_product(data: dict) -> dict:
    """Agregar un nuevo producto."""
    try:
        nombre = data.get("nombre", data.get("name", ""))
        precio = data.get("precio", data.get("price"))
        categoria = data.get("categoria", data.get("category", "general"))
        negocio = data.get("negocio", "atf")
        stock = data.get("stock", 0)
        descripcion = data.get("descripcion", data.get("description", ""))

        if not nombre:
            return {"exito": False, "mensaje": "El nombre del producto es obligatorio", "resultado": None}

        producto_id = str(uuid.uuid4())[:8]
        producto = {
            "id": producto_id,
            "nombre": nombre,
            "precio": precio,
            "precio_min": data.get("precio_min"),
            "precio_max": data.get("precio_max"),
            "categoria": categoria,
            "negocio": negocio,
            "stock": stock,
            "descripcion": descripcion,
            "fecha_creacion": datetime.now().isoformat(),
        }
        productos_db[producto_id] = producto
        logger.info(f"Producto agregado: {nombre} (ID: {producto_id})")

        return {
            "exito": True,
            "mensaje": f"Producto '{nombre}' agregado exitosamente",
            "resultado": producto
        }
    except Exception as e:
        logger.error(f"Error al agregar producto: {e}")
        return {"exito": False, "mensaje": f"Error: {str(e)}", "resultado": None}


def get_products(data: dict) -> dict:
    """Obtener lista de productos."""
    try:
        negocio = data.get("negocio", None)
        categoria = data.get("categoria", data.get("category", None))

        lista_productos = list(productos_db.values())
        if negocio:
            lista_productos = [p for p in lista_productos if p.get("negocio") == negocio]
        if categoria:
            lista_productos = [p for p in lista_productos if p.get("categoria") == categoria]

        return {
            "exito": True,
            "mensaje": f"{len(lista_productos)} productos encontrados",
            "resultado": {
                "total": len(lista_productos),
                "productos": lista_productos
            }
        }
    except Exception as e:
        logger.error(f"Error al obtener productos: {e}")
        return {"exito": False, "mensaje": f"Error: {str(e)}", "resultado": None}


def update_stock(data: dict) -> dict:
    """Actualizar stock de un producto."""
    try:
        producto_id = data.get("producto_id", data.get("product_id", data.get("id", "")))
        cantidad = data.get("cantidad", data.get("quantity", 0))
        operacion = data.get("operacion", data.get("operation", "set"))  # set, add, subtract

        if not producto_id or producto_id not in productos_db:
            return {"exito": False, "mensaje": "Producto no encontrado", "resultado": None}

        producto = productos_db[producto_id]
        stock_actual = producto.get("stock", 0) or 0

        if operacion == "add":
            nuevo_stock = stock_actual + cantidad
        elif operacion == "subtract":
            nuevo_stock = max(0, stock_actual - cantidad)
        else:
            nuevo_stock = cantidad

        producto["stock"] = nuevo_stock
        logger.info(f"Stock actualizado: {producto['nombre']} -> {nuevo_stock}")

        return {
            "exito": True,
            "mensaje": f"Stock de '{producto['nombre']}' actualizado a {nuevo_stock}",
            "resultado": {
                "producto_id": producto_id,
                "producto_nombre": producto["nombre"],
                "stock_anterior": stock_actual,
                "stock_nuevo": nuevo_stock
            }
        }
    except Exception as e:
        logger.error(f"Error al actualizar stock: {e}")
        return {"exito": False, "mensaje": f"Error: {str(e)}", "resultado": None}


# ==================== ACCIONES DE ÓRDENES ====================

def create_order(data: dict) -> dict:
    """Crear una nueva orden de venta."""
    try:
        cliente_id = data.get("cliente_id", data.get("client_id", ""))
        productos_orden = data.get("productos", data.get("items", []))
        notas = data.get("notas", data.get("notes", ""))

        if not cliente_id or cliente_id not in clientes_db:
            return {"exito": False, "mensaje": "Cliente no encontrado", "resultado": None}

        if not productos_orden:
            return {"exito": False, "mensaje": "La orden debe tener al menos un producto", "resultado": None}

        # Calcular totales
        total = 0.0
        items_procesados = []
        for item in productos_orden:
            prod_id = item.get("producto_id", item.get("product_id", ""))
            cantidad = item.get("cantidad", item.get("quantity", 1))
            precio_unitario = item.get("precio", item.get("price", 0))

            if prod_id and prod_id in productos_db:
                prod_info = productos_db[prod_id]
                if precio_unitario == 0 and prod_info.get("precio"):
                    precio_unitario = prod_info["precio"]

            subtotal = precio_unitario * cantidad
            total += subtotal
            items_procesados.append({
                "producto_id": prod_id,
                "cantidad": cantidad,
                "precio_unitario": precio_unitario,
                "subtotal": subtotal
            })

        orden_id = str(uuid.uuid4())[:8]
        orden = {
            "id": orden_id,
            "cliente_id": cliente_id,
            "cliente_nombre": clientes_db[cliente_id].get("nombre", "Desconocido"),
            "items": items_procesados,
            "total": total,
            "notas": notas,
            "estado": "pendiente",
            "fecha_creacion": datetime.now().isoformat(),
            "negocio": clientes_db[cliente_id].get("negocio", "atf"),
        }
        ordenes_db[orden_id] = orden

        # Actualizar métricas del cliente
        clientes_db[cliente_id]["total_compras"] = clientes_db[cliente_id].get("total_compras", 0) + 1
        clientes_db[cliente_id]["total_gastado"] = clientes_db[cliente_id].get("total_gastado", 0.0) + total

        logger.info(f"Orden creada: {orden_id} - Total: ${total:.2f}")

        return {
            "exito": True,
            "mensaje": f"Orden {orden_id} creada exitosamente por ${total:.2f}",
            "resultado": orden
        }
    except Exception as e:
        logger.error(f"Error al crear orden: {e}")
        return {"exito": False, "mensaje": f"Error: {str(e)}", "resultado": None}


def get_orders(data: dict) -> dict:
    """Obtener lista de órdenes."""
    try:
        estado = data.get("estado", data.get("status", None))
        negocio = data.get("negocio", None)
        limite = data.get("limite", data.get("limit", 100))

        lista_ordenes = list(ordenes_db.values())
        if estado:
            lista_ordenes = [o for o in lista_ordenes if o.get("estado") == estado]
        if negocio:
            lista_ordenes = [o for o in lista_ordenes if o.get("negocio") == negocio]

        lista_ordenes = sorted(lista_ordenes, key=lambda x: x.get("fecha_creacion", ""), reverse=True)
        lista_ordenes = lista_ordenes[:limite]

        total_ingresos = sum(o.get("total", 0) for o in lista_ordenes if o.get("estado") in ["completada", "entregada"])

        return {
            "exito": True,
            "mensaje": f"{len(lista_ordenes)} orden(es) encontrada(s)",
            "resultado": {
                "total": len(lista_ordenes),
                "ingresos_totales": round(total_ingresos, 2),
                "ordenes": lista_ordenes
            }
        }
    except Exception as e:
        logger.error(f"Error al obtener órdenes: {e}")
        return {"exito": False, "mensaje": f"Error: {str(e)}", "resultado": None}


def update_order_status(data: dict) -> dict:
    """Actualizar estado de una orden."""
    try:
        orden_id = data.get("orden_id", data.get("order_id", data.get("id", "")))
        nuevo_estado = data.get("estado", data.get("status", ""))

        estados_validos = ["pendiente", "confirmada", "en_proceso", "completada", "entregada", "cancelada"]

        if not orden_id or orden_id not in ordenes_db:
            return {"exito": False, "mensaje": "Orden no encontrada", "resultado": None}

        if nuevo_estado not in estados_validos:
            return {
                "exito": False,
                "mensaje": f"Estado inválido. Estados válidos: {', '.join(estados_validos)}",
                "resultado": None
            }

        orden = ordenes_db[orden_id]
        estado_anterior = orden["estado"]
        orden["estado"] = nuevo_estado
        orden["fecha_actualizacion"] = datetime.now().isoformat()

        logger.info(f"Orden {orden_id}: {estado_anterior} -> {nuevo_estado}")

        return {
            "exito": True,
            "mensaje": f"Orden {orden_id} actualizada: {estado_anterior} -> {nuevo_estado}",
            "resultado": {
                "orden_id": orden_id,
                "estado_anterior": estado_anterior,
                "estado_nuevo": nuevo_estado,
                "fecha_actualizacion": orden["fecha_actualizacion"]
            }
        }
    except Exception as e:
        logger.error(f"Error al actualizar orden: {e}")
        return {"exito": False, "mensaje": f"Error: {str(e)}", "resultado": None}


# ==================== MÉTRICAS ====================

def get_metrics(data: dict) -> dict:
    """Obtener métricas del dashboard."""
    try:
        ahora = datetime.now()
        inicio_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Métricas generales
        total_clientes = len(clientes_db)
        total_productos = len(productos_db)
        total_ordenes = len(ordenes_db)

        # Órdenes del mes
        ordenes_mes = [
            o for o in ordenes_db.values()
            if o.get("estado") in ["completada", "entregada"]
            and datetime.fromisoformat(o.get("fecha_creacion", ahora.isoformat())) >= inicio_mes
        ]
        ingresos_mes = sum(o.get("total", 0) for o in ordenes_mes)

        # Ventas por negocio
        ventas_por_negocio = {}
        for negocio_id, negocio_info in NEGOCIOS.items():
            ord_neg = [o for o in ordenes_db.values() if o.get("negocio") == negocio_id]
            ventas_por_negocio[negocio_id] = {
                "nombre": negocio_info["nombre"],
                "total_ordenes": len(ord_neg),
                "ingresos": round(sum(o.get("total", 0) for o in ord_neg), 2)
            }

        # Top productos vendidos
        conteo_productos = {}
        for orden in ordenes_db.values():
            for item in orden.get("items", []):
                nombre = item.get("producto_id", "desconocido")
                if nombre in productos_db:
                    nombre = productos_db[nombre].get("nombre", nombre)
                conteo_productos[nombre] = conteo_productos.get(nombre, 0) + item.get("cantidad", 1)

        top_productos = sorted(conteo_productos.items(), key=lambda x: x[1], reverse=True)[:5]

        # Órdenes por estado
        ordenes_por_estado = {}
        for orden in ordenes_db.values():
            estado = orden.get("estado", "desconocido")
            ordenes_por_estado[estado] = ordenes_por_estado.get(estado, 0) + 1

        metricas = {
            "resumen": {
                "total_clientes": total_clientes,
                "total_productos": total_productos,
                "total_ordenes": total_ordenes,
                "ordenes_mes": len(ordenes_mes),
                "ingresos_mes": round(ingresos_mes, 2),
            },
            "ventas_por_negocio": ventas_por_negocio,
            "top_productos": [{"producto": p[0], "unidades": p[1]} for p in top_productos],
            "ordenes_por_estado": ordenes_por_estado,
            "fecha_generacion": ahora.isoformat(),
        }

        return {
            "exito": True,
            "mensaje": "Métricas generadas exitosamente",
            "resultado": metricas
        }
    except Exception as e:
        logger.error(f"Error al generar métricas: {e}")
        return {"exito": False, "mensaje": f"Error: {str(e)}", "resultado": None}


# Mapa de acciones
ACCIONES = {
    "add_client": add_client,
    "get_clients": get_clients,
    "search_client": search_client,
    "add_product": add_product,
    "get_products": get_products,
    "update_stock": update_stock,
    "create_order": create_order,
    "get_orders": get_orders,
    "update_order_status": update_order_status,
    "get_metrics": get_metrics,
}


# ==================== ENDPOINTS ====================

@app.get("/health")
async def health_check():
    """Endpoint de salud del motor."""
    try:
        return {
            "status": "ok",
            "motor": "negocios",
            "version": "3.0.0",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@app.get("/status")
async def get_status():
    """Obtener estadísticas del motor."""
    try:
        return {
            "motor": "negocios",
            "estado": "funcionando",
            "tareas_completadas": motor_stats["tareas_completadas"],
            "tareas_con_error": motor_stats["tareas_con_error"],
            "tiempo_actividad": _obtener_tiempo_actividad(),
            "hora_inicio": datetime.fromtimestamp(motor_stats["hora_inicio"]).isoformat(),
            "ultima_actividad": motor_stats["ultima_actividad"],
            "total_clientes": len(clientes_db),
            "total_productos": len(productos_db),
            "total_ordenes": len(ordenes_db),
            "version": settings.VERSION if hasattr(settings, 'VERSION') else "3.0.0"
        }
    except Exception as e:
        logger.error(f"Error al obtener estado: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener estadísticas")


@app.get("/businesses")
async def get_businesses():
    """Obtener lista de negocios con sus productos."""
    try:
        resultado = {}
        for negocio_id, negocio_info in NEGOCIOS.items():
            productos_negocio = [
                p for p in productos_db.values() if p.get("negocio") == negocio_id
            ]
            resultado[negocio_id] = {
                "nombre": negocio_info["nombre"],
                "descripcion": negocio_info["descripcion"],
                "tipo": negocio_info["tipo"],
                "total_productos": len(productos_negocio),
                "productos": productos_negocio
            }
        return {
            "success": True,
            "result": resultado,
            "message": f"{len(resultado)} negocios registrados"
        }
    except Exception as e:
        logger.error(f"Error en /businesses: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener negocios")


@app.get("/metrics")
async def metrics_endpoint():
    """Obtener métricas del dashboard."""
    try:
        resultado = get_metrics({})
        return {
            "success": resultado["exito"],
            "result": resultado.get("resultado"),
            "message": resultado["mensaje"]
        }
    except Exception as e:
        logger.error(f"Error en /metrics: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener métricas")


@app.post("/quick_note")
async def quick_note(request: QuickNoteRequest):
    """Guardar una nota rápida de negocio."""
    try:
        nota = {
            "id": str(uuid.uuid4())[:8],
            "texto": request.text,
            "categoria": request.category,
            "fecha": datetime.now().isoformat(),
        }
        notas_rapidas.append(nota)
        logger.info(f"Nota rápida guardada: [{request.category}] {request.text[:50]}...")
        _actualizar_estadisticas(True)

        return {
            "success": True,
            "result": nota,
            "message": "Nota guardada exitosamente"
        }
    except Exception as e:
        logger.error(f"Error al guardar nota: {e}")
        _actualizar_estadisticas(False)
        return {
            "success": False,
            "result": None,
            "message": f"Error al guardar nota: {str(e)}"
        }


@app.post("/execute")
async def execute(request: ExecuteRequest):
    """Endpoint principal de ejecución del motor de negocios."""
    try:
        accion = request.action.lower().strip()
        data = request.data or {}

        logger.info(f"Ejecutando acción: {accion}")

        if accion not in ACCIONES:
            acciones_disp = ", ".join(sorted(ACCIONES.keys()))
            _actualizar_estadisticas(False)
            return {
                "success": False,
                "result": None,
                "message": f"Acción '{accion}' no reconocida. Acciones disponibles: {acciones_disp}"
            }

        funcion = ACCIONES[accion]
        resultado = funcion(data)
        exito = resultado.get("exito", False)
        _actualizar_estadisticas(exito)

        return {
            "success": exito,
            "result": resultado.get("resultado"),
            "message": resultado.get("mensaje", "Acción ejecutada")
        }

    except Exception as e:
        logger.error(f"Error en execute: {e}", exc_info=True)
        _actualizar_estadisticas(False)
        return {
            "success": False,
            "result": None,
            "message": f"Error interno del servidor: {str(e)}"
        }


# ==================== INICIO ====================

if __name__ == "__main__":
    import uvicorn
    logger.info("Iniciando Motor de Negocios - NEXUS v3 en puerto 8003...")
    uvicorn.run(app, host="127.0.0.1", port=8003)
