# PLAN DE TRABAJO PARALELO — NEXUS
## Lo que Claude construye mientras tú pruebas

---

## BLOQUE 1 — Sistema de Licencias y Anti-piratería
**Archivos a crear:**
- `nexus_license.py` — motor de validación de licencias
- `nexus_fingerprint.py` — huella de hardware (CPU + MAC + disco)
- `CONFIG/license.key` — archivo de licencia cifrado

**Funcionalidad:**
- Genera huella única por máquina
- Valida expiración en cada arranque
- Valida módulos habilitados por licencia
- Bloquea UI de módulos no autorizados
- Ping opcional a Supabase para validación remota

---

## BLOQUE 2 — Generador de Demos
**Archivos a crear:**
- `nexus_demo_creator.py` — herramienta de creación de demos
- `WEB/templates/admin_demos.html` — panel de gestión de demos

**Funcionalidad:**
- Crear demo con nombre de cliente, módulos y días de vigencia
- Genera paquete ZIP listo para enviar
- Registra en base de datos qué demos están activas
- Puede revocar demos desde el admin

---

## BLOQUE 3 — Dashboard Financiero
**Archivos a crear/modificar:**
- `nexus_finanzas.py` — módulo de finanzas
- `WEB/templates/finanzas.html` — panel financiero

**Funcionalidad:**
- Ingresos del mes (basado en pedidos entregados)
- Margen por trabajo (precio cotizado vs costo de materiales)
- Clientes que no han pedido en 30+ días
- Top 5 productos más vendidos

---

## BLOQUE 4 — Mejoras al Panel Central
**Basado en los bugs que reporte Copilot:**
- Correcciones de los BUGs CRÍTICOS y ALTOS
- Búsqueda en pedidos
- Filtro por estado en pedidos
- Paginación si hay muchos registros

---

## BLOQUE 5 — Versión Portable (PyInstaller)
- Empaquetar NEXUS como .exe autocontenido
- Sin necesidad de Python instalado
- Incluye base de datos vacía + configuración base
- Script de build: `build_nexus.bat`

---

## ORDEN DE PRIORIDAD

1. Primero: terminar pruebas con Copilot → reporte de bugs
2. Yo construyo Bloques 1 y 2 mientras tanto
3. Al recibir reporte: corrijo bugs críticos
4. Luego: Bloques 3, 4 y 5 en ese orden

---

## CÓMO PASARME EL REPORTE

Cuando termines las pruebas, pégame el reporte completo que generó Copilot
en un solo mensaje. Yo proceso todo y genero los bloques de corrección completos
sin que tengas que aprobar cada línea.
