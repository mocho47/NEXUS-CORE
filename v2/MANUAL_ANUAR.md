# Manual NEXUS v2 — Anuar (Administrador)
**Taller Simplex · Milens · ATF**

---

## Cómo entrar
1. Abre el navegador → escribe `http://localhost:8001`
2. Aparece la pantalla de PIN → escribe **1111**
3. El panel se abre con tu nombre arriba a la derecha

---

## La pantalla principal (Resumen)
Cuando entras ves 6 tarjetas:
- **Pedidos activos** — cuántos trabajos tienes en curso
- **Entregan hoy** — los que vencen hoy
- **Atrasados** (rojo) — los que ya pasaron su fecha de entrega
- **Listos p/entregar** (amarillo) — terminados, esperando que el cliente los recoja
- **Prospectos activos** — clientes en el pipeline de ventas
- **Ingresos del mes** — solo tú lo ves (Rocío no)

Debajo aparece el **briefing del día** con un resumen de todo.

---

## Pedidos — lo más importante del día

### Registrar un pedido nuevo
1. Click en tab **Pedidos**
2. Llena: Cliente, Teléfono, Descripción, Servicio, Fecha de entrega, Precio, Notas
3. Click **+ Registrar** o presiona **Enter**

También puedes dictarle al chat:
```
nuevo pedido para Carlos 50 tazas sublimadas entrega viernes
```

### Cambiar el estado de un pedido
En la tabla de pedidos, cada fila tiene botones:
- **▶** = En proceso (ya estás trabajando en él)
- **✓** = Listo (terminado, espera al cliente)
- **✔✔** = Entregado (el cliente ya lo recogió y pagó)
- **✕** (rojo) = Cancelar — **solo tú puedes cancelar**

### Editar el precio de un pedido
Haz click directo sobre el precio en la tabla — se vuelve editable.
Escribe el nuevo precio y presiona **Enter** o click fuera.
**Solo el administrador puede cambiar precios.**

### Ver las notas de un pedido
Haz click en cualquier fila de la tabla — se expande y muestra las notas.
También puedes editar las notas ahí mismo.

### Buscar un pedido
Usa la barra de búsqueda arriba de la tabla — filtra por nombre de cliente o descripción en tiempo real.

### Ver el historial de un cliente
En la tabla de pedidos, haz click en el **nombre del cliente** (subrayado).
Abre un panel con todos sus pedidos anteriores, total facturado, y accesos rápidos.

---

## Cotizaciones rápidas

### Cotizar ATF (faros)
1. Tab **Cotizar** → sección ATF
2. Selecciona el modelo (X1 al X7)
3. Escribe el nombre del cliente (opcional)
4. Click **Cotizar** → aparece precio dist, precio público y tu ganancia
5. Botón **Copiar mensaje WA** para mandárselo al cliente

O desde el chat:
```
cotiza X4 para Mario
cotiza X2
```

### Cotizar Sublimación
```
cotiza 50 tarjetas sublimacion
cotiza 100 tazas sublimacion
cotiza lona 2x1 sublimacion
```

### Cotizar Láser / Generar caja
```
cotiza laser 30x20 mdf_3
genera caja 20x15x8 mdf_3
```

---

## Agenda ATF
Registra las instalaciones programadas.

### Agendar una instalación
1. Tab **Agenda ATF**
2. Llena: Cliente, Kit, Carro, Fecha, Hora
3. Click **+ Agendar**

O desde el chat:
```
agenda instalacion X4 para Juan el viernes
nueva instalacion X2 para Pedro el martes a las 10
```

---

## Pipeline de ventas
Controla en qué etapa está cada cliente potencial.

**Estados del pipeline:**
- **Prospecto** → primer contacto
- **Cotizado** → ya le mandaste precio
- **Seguimiento** → esperando respuesta
- **Cerrado** → ¡vendido!
- **Perdido** → no se concretó

### Mover un prospecto
En la tabla del Pipeline, usa el selector de la derecha para cambiar su estado.

Desde el chat:
```
nuevo prospecto Roberto atf
mover Roberto a cotizado
ver pipeline
```

---

## Mensajes WhatsApp
NEXUS genera el mensaje — tú lo copias y lo mandas desde tu WhatsApp Business.

```
redacta mensaje followup para Carlos
redacta mensaje listo para Ana
redacta mensaje reactivacion para Luis
```

También desde el historial del cliente (click en su nombre) tienes botones directos.

---

## Publicaciones para redes
```
post de instagram para atf
post de tiktok para laser
post de facebook para sublimacion
```

---

## Finanzas
Solo tú las ves.
```
finanzas del mes
finanzas semana
```
O click en la tarjeta **Ingresos del mes** en el Resumen.

---

## Proveedores y distribuidores
Registra a quienes te surten material, hacen maquila, o distribuyen equipo.

1. Tab **Proveedores**
2. Solo tú puedes registrar (Rocío solo consulta)
3. Llena: Nombre, Empresa, WhatsApp, Categoría, Qué suministra, Precios, Tiempo de entrega

Desde el chat:
```
proveedores
quien surte mdf
maquilas disponibles
```

---

## Detectar oportunidades
```
quien no ha pagado
```
NEXUS detecta: pedidos atrasados, listos sin entregar, prospectos fríos, y clientes que no han regresado en 30+ días.

---

## Cambiar el PIN de Rocío
Por ahora se hace directo en la base de datos. Próximamente desde el panel.
PIN actual de Rocío: **2222**

---

## Briefing diario
Cada mañana escribe:
```
briefing
```
Te da un resumen de todo: atrasados, listos, prospectos, agenda del día.

---

## Atajos de teclado
- **Enter** en cualquier campo de formulario → guarda/registra
- **Ctrl + /** → mueve el cursor al chat
- **Escape** → cierra cualquier modal/popup

---

## Si NEXUS no entiende algo
Pregúntale directamente:
```
que puedes hacer
ayuda
como registro un pedido
como cotizo
```

---

## Cerrar sesión
Click en tu nombre (arriba a la derecha) → confirmar.
