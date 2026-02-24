# NEXUS — Lista Maestra de Comandos y URLs
## Actualizado: 2026-02-24 | Versión: v2026 FULL

---

## ARRANQUE RÁPIDO

```bash
# Iniciar NEXUS completo (doble clic en escritorio):
INICIAR_NEXUS_FULL.bat

# O desde terminal:
python nexus_server.py

# Primera vez — configurar admin:
python nexus_admin.py setup

# Pruebas del sistema:
python nexus_test_runner.py
```

---

## PANELES WEB (http://localhost:8000/...)

| URL | Descripción |
|---|---|
| `/` | Dashboard principal |
| `/dashboard` | Panel de control |
| `/admin` | Control ADMIN exclusivo (PIN) |
| `/autoventas` | Pipeline de auto-ventas NEXUS |
| `/landing` | Landing page pública (captura leads) |
| `/nexus-ear` | Oído NEXUS — transcripción en vivo + chat |
| `/teens` | NEXUS Teens + Bloque Familia |
| `/galeria` | Galería Binaural (audios + visuales) |
| `/legal` | Aviso de Privacidad + Términos (LFPDPPP) |
| `/marketing` | Marketing IA + Subliminal |
| `/finanzas` | Dashboard Financiero |
| `/clientes` | CRM Clientes |
| `/stock` | Inventario |
| `/cotizar-rapido` | Cotizador express |
| `/nuevo_pedido` | Nuevo pedido |

---

## COMANDOS DE VOZ (di "Nexus" primero)

### SISTEMA
- `"sistema"` / `"estatus"` → RAM y CPU en tiempo real
- `"diagnóstico"` → revisión completa del sistema
- `"autorrepara"` → instala dependencias faltantes
- `"cállate"` / `"silencio"` / `"cancela"` → interrumpe NEXUS
- `"descansa"` → apaga el sistema

### NEGOCIO
- `"¿cuántos pedidos tengo hoy?"` → pedidos pendientes
- `"¿cómo está el stock?"` → inventario y alertas
- `"¿cuántos clientes tenemos?"` → total de clientes
- `"¿cuáles son mis ventas de hoy?"` → ingresos del día
- `"genera un post para instagram"` → marketing IA

### MEMORIA
- `"anota [texto]"` / `"memoriza [texto]"` → guarda nota
- `"recuerda [tema]"` → busca en memoria
- `"lista tareas"` → todas las tareas pendientes
- `"hecho tarea [N]"` → marcar tarea como completada
- `"duerme"` → consolidación de memoria offline

### MARKETING
- `"Nexus... Campaña Viral"` → genera campaña para TikTok
- `"Nexus... Catálogo"` → genera catálogo de productos
- `"Nexus... Cotiza [N] minutos"` → precio láser

### WATCHTOWER
- `"mensajes nuevos"` → mensajes sin leer
- `"lee mensajes [N]"` → leer últimos N mensajes
- `"modo vigilancia"` / `"silencia vigilancia"`

### APPS Y SISTEMA
- `"abre youtube"` / `"abre whatsapp"` / `"abre corel"` → lanza apps
- `"temporizador de [N] minutos"` → alarma

### PRIVACIDAD Y NUBE
- `"autoriza nube"` → permite conexión a internet
- `"bloquea nube"` → modo offline
- `"autoriza acciones [N]"` → ventana temporal de acciones sensibles
- `"supabase vivo ahora"` → ping manual Supabase

---

## COMANDOS CLI PYTHON

### ADMIN Y CONFIGURACIÓN
```bash
python nexus_admin.py setup          # Primera configuración de admin
python nexus_admin.py login          # Login y obtener token de sesión
python nexus_admin.py catalogo       # Ver catálogo de módulos con precios
python nexus_admin.py tiers          # Ver módulos por tier de licencia
```

### LICENCIAS
```bash
python nexus_license.py info         # Info de licencia actual
python nexus_license.py huella       # Huella de hardware de este equipo
python nexus_license.py demo         # Activar demo 30 días
python nexus_license.py validar      # Verificar si la licencia es válida
```

### AUTOVENTAS
```bash
python nexus_autoventas.py pipeline     # Ver pipeline de prospectos
python nexus_autoventas.py seguimiento  # Mensajes pendientes de enviar
python nexus_autoventas.py hooks        # Hooks virales TikTok
python nexus_autoventas.py hooks instagram  # Hooks para Instagram
python nexus_autoventas.py calendario   # Calendario editorial semanal
python nexus_autoventas.py metricas     # Estadísticas de conversión
```

### LEGAL Y PRIVACIDAD
```bash
python nexus_legal.py aviso          # Mostrar aviso de privacidad completo
python nexus_legal.py terminos       # Mostrar términos de uso
python nexus_legal.py estado         # ¿El usuario aceptó los términos?
python nexus_legal.py aceptar        # Registrar aceptación de términos
```

### TEENS Y FAMILIA
```bash
python nexus_teens.py demo           # Demo del módulo teens
python nexus_teens.py misiones       # Ver catálogo de misiones
python nexus_teens.py aptitudes      # Ver catálogo de aptitudes
```

### PRUEBAS DEL SISTEMA
```bash
python nexus_test_runner.py          # Pruebas E2E completas (todos los módulos)
python nexus_test_runner.py --api    # Solo endpoints HTTP
# Resultados en: logs/test_results.log + logs/test_results.json
```

### OTROS
```bash
python nexus_galeria.py              # Info de catálogo de galería
python nexus_backup.py               # Respaldo manual
python nexus_doctor.py               # Diagnóstico del sistema
python nexus_self_heal.py            # Auto-reparación
```

---

## PLAN DE NEGOCIO Y PRECIOS

```
NEXUS DEMO  — GRATIS       / 30 días    / 8 módulos
NEXUS LITE  — $1,200 MXN   / 1 año     / 13 módulos
NEXUS PRO   — $2,800 MXN   / 3 años    / 16 módulos + binaural
NEXUS FULL  — $5,999 MXN   / 10 años   / TODOS los módulos
```

**Módulos extra (compra única):**
```
Teens + Familia  — $499 MXN
Galería extra    — $100 MXN (5 activaciones)
Spy Competencia  — $399 MXN
Meta/IG Ads      — $499 MXN
Facturación CFDI — $599 MXN
IoT + Sensores   — $699 MXN
Paranormal Mode  — $399 MXN
```

Plan de negocio completo: `PLAN_NEGOCIO/nexus_business_plan.md`

---

## ARCHIVOS CLAVE

| Archivo | Descripción |
|---|---|
| `nexus_server.py` | Servidor FastAPI (1,300+ líneas, 90+ rutas) |
| `nexus_admin.py` | Panel de control y catálogo de módulos |
| `nexus_autoventas.py` | Motor de auto-ventas |
| `nexus_teens.py` | Motor teens + bloque familia |
| `nexus_legal.py` | Cumplimiento LFPDPPP México |
| `nexus_galeria.py` | 40 audios binaurales + 8 visuales |
| `nexus_subliminal.py` | 60 mensajes persuasivos + generador WAV |
| `nexus_test_runner.py` | Pruebas E2E con log |
| `CONFIG/admin_config.json` | Config del admin (tiers, precios, PIN hash) |
| `CONFIG/autoventas.json` | Pipeline de prospectos |
| `logs/test_results.log` | Log de última prueba E2E |
| `PLAN_NEGOCIO/nexus_business_plan.md` | Plan de negocio completo |

---

## SESIÓN DE PREGUNTAS FRECUENTES

**¿Cómo abro el panel admin?**
→ `http://localhost:8000/admin` — requiere PIN (configura con `python nexus_admin.py setup`)

**¿Cómo agrego un prospecto al pipeline de ventas?**
→ `http://localhost:8000/autoventas` → tab "Nuevo Lead"
→ O desde la landing: `http://localhost:8000/landing`

**¿Cómo activo el modo de voz + texto en NEXUS?**
→ `http://localhost:8000/nexus-ear` — toggle Voz/Texto en la esquina superior derecha

**¿Dónde veo los logs del sistema?**
→ `logs/nexus_log_2026-02.txt` — log de operaciones
→ `logs/test_results.log` — resultado de última prueba E2E

**¿Cómo reinicio el servidor con los cambios nuevos?**
→ Ctrl+C en la terminal → `python nexus_server.py` → `python nexus_test_runner.py`
