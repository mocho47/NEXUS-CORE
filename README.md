# NEXUS v3 by Simplex

Sistema de orquestación multi-IA para gestión de negocios — taller Simplex GDL.

> "Soluciones simples a procesos complejos."

---

## Contexto del proyecto

NEXUS es el sistema nervioso central de 3 negocios físicos:
- **Creaciones Milens** — Corte láser, sublimación, stickers, cajas MDF
- **ATF (Actualiza Tus Faros)** — Retrofit de faros bi-LED en Guadalajara
- **CanbusFix** — Red de instaladores retrofit por toda México

NEXUS **no hace trabajo** — orquesta. Recibe una instrucción, decide qué motor la ejecuta, lo llama, devuelve el resultado. El usuario solo ve el resultado final.

---

## Arquitectura

```
nexus_core.py          Puerto 8003 — cerebro FastAPI + chat IA
lib/
  ai_client.py         Routing multi-IA: Groq → Z.ai → OpenRouter → Ollama
  auth.py              Roles + PIN + brute force protection
  database.py          aiosqlite WAL — 8 tablas
  config.py            .env + constantes
  notificaciones.py    Telegram alerts + SSE tiempo real
  memory.py            Memoria persistente por clave
  file_utils.py        Utilidades de archivos
motors/
  motor_atf.py         Puerto 8004 — kits Aozoom, cotizaciones, agenda, pipeline
  motor_auth.py        Puerto 8006 — login PIN, tokens, sesiones
  motor_teens.py       Puerto 8005 — misiones familiares, aprobaciones, SSE
  motor_pagos.py       Puerto 8007 — cotizaciones, pagos, resumen financiero
  motor_reportes.py    Puerto 8008 — diario, semanal, análisis IA
  motor_diseno.py      Generación de archivos para taller (stickers, cajas, planillas)
  motor_negocios.py    Pedidos, clientes, stock
  motor_social.py      Publisher IG/TikTok/FB — rota videos ATF automático
  motor_forja.py       Comunidad FORJA — emprendedores filtrados
  motor_coaching.py    NEXUS Teens — coaching familiar
  motor_archivos.py    Procesamiento y conversión de archivos
templates/
  chat.html            Interfaz principal
  manual.html          Documentación interna
```

---

## Cadena de IA (ai_client.py)

```
1. Groq llama-3.3-70b    → análisis profundo, reportes
2. Groq llama-3.1-8b     → respuestas rápidas, tiempo real
3. Z.ai GLM-5            → fallback principal
4. OpenRouter Nemotron   → revisión de código background
5. Ollama glm4 / qwen2.5 → offline, sin internet
```

Todas las llamadas pasan por `lib/ai_client.py` — nunca directamente.

---

## Endpoints principales (nexus_core.py :8003)

| Método | Ruta | Función |
|--------|------|---------|
| GET | / | Chat principal |
| POST | /chat | Entrada al cerebro IA |
| GET | /motors/status | Estado de los 5 motores |
| GET | /ai/status | Proveedores IA disponibles |
| GET | /api/status | Ping — verificación conexión frontend |
| GET | /panel | Panel de control |
| GET | /manual | Documentación |
| GET | /api/clients | Clientes DB |
| GET | /api/orders | Pedidos DB |
| POST | /tts | Texto a voz (es-MX-JorgeNeural) |

### Motor ATF (:8004)
- `GET /atf/kits` — 7 kits Aozoom con precios dist/pub
- `POST /atf/cotizar` — cotización con instalación
- `POST /atf/agendar` — crear cita
- `GET/PUT /atf/agenda` — agenda instalaciones
- `POST/GET/PUT /atf/pipeline` — pipeline prospectos

### Motor Auth (:8006)
- `POST /auth/login` — rol + PIN → token
- `POST /auth/verify` — valida token
- `POST /auth/set-pin` — configura PINs (admin)

### Motor Teens (:8005)
- `POST /teens/misiones` — crear misión familiar
- `PUT /teens/misiones/{id}/completar` — teen completa
- `PUT /teens/misiones/{id}/aprobar` — padre aprueba + puntos
- `GET /teens/eventos/{familia_id}` — SSE tiempo real

### Motor Pagos (:8007)
- `POST /pagos/cotizacion` — crear cotización
- `POST /pagos/registrar` — registrar pago
- `GET /pagos/resumen` — totales día/mes
- `GET /pagos/listar` — historial filtrado

### Motor Reportes (:8008)
- `GET /reportes/resumen-diario` — datos del día
- `POST /reportes/analisis-ia` — análisis con IA
- `GET /reportes/resumen-semana` — métricas semanales

---

## Los 17 Motores (arquitectura objetivo)

| # | Nombre | Función |
|---|--------|---------|
| 1 | Conversor universal | Cualquier archivo → formato correcto |
| 2 | Cotizador sublimación | Artículo + cantidad → precio dist/pub/ganancia |
| 3 | Preparador de archivo | 300 DPI + perfil color + sangrado |
| 4 | Cotizador láser | Material + dimensiones → precio |
| 5 | Generador de cajas | Medidas → DXF para Corel/Silhouette |
| 6A | Optimizador archivo | DPI, tamaño, sangrado |
| 6B | Vectorizador | Raster → vectorial (Inkscape, NO CorelDRAW) |
| 7 | Cotizador ATF | Aozoom X1-X7 → precios automáticos |
| 8 | Agenda ATF | Registro + seguimiento + alertas |
| 9 | Material ATF | Tarjetas, llaveros QR, portadas redes |
| 10 | Directorio CanbusFix | Instaladores por ciudad |
| 11 | Catálogo servicios | Precios por tier |
| 12 | Pedidos + Clientes | CRM completo |
| 13 | Cerebro orquestador | Instrucción → motor → resultado |
| 14 | Detector oportunidades | Clientes fríos, cotizaciones sin respuesta |
| 15 | Generador mensajes | WhatsApp listo por contexto |
| 16 | Publicador redes | IG/TikTok/FB automático |
| 17 | Pipeline ventas | Lead → Cerrado → Entregado |

**Reglas:**
- Cada motor = UN archivo = UNA responsabilidad
- El cerebro NO implementa lógica — solo delega
- Nada se declara listo sin prueba real

---

## Precios de referencia (Aozoom)

| Kit | Dist | Pub |
|-----|------|-----|
| X1 | $2,350 | $3,149 |
| X2 | $2,050 | $2,799 |
| X3 | $2,350 | $3,149 |
| X4 | $1,990 | $2,699 |
| X5/X6 | $1,199 | $1,599 |
| X7 | $1,550 | $2,069 |

Instalación estándar: $500. Margen ejemplo X4: 26.3%

---

## Reglas de archivos (Milens)

- Resolución: **300 DPI siempre**
- Salida: **PDF + PNG en par**
- Dimensiones: **siempre en cm**
- Directorio: `C:\nexus\MERCH_OUTPUT\`
- Planillas: calcular máximo de piezas que caben

---

## Stack técnico

```
Python 3.12
FastAPI + Jinja2 + uvicorn
aiosqlite (WAL mode)
Groq SDK
httpx (async HTTP)
edge_tts (es-MX-JorgeNeural)
instagrapi (publisher Instagram)
ffmpeg (procesamiento video)
Ollama (modelos locales: glm4, qwen2.5:7b)
Docker Desktop (compose pendiente)
```

---

## Productos del ecosistema

### NEXUS by Simplex (se vende con licencia)
Sistema modular: DEMO / LITE / PRO / FULL / ADMIN
El cliente configura su negocio, nunca ve datos de Anuar.

### NEXUS Teens (app familiar independiente)
- 4 roles: Papá / Mamá / Hijo / Hija
- Misiones + canjes + aprobación padre + SSE
- PWA funcional + URL pública ngrok
- Puerto 8005 dentro de v3

### FORJA (comunidad emprendedores independiente)
- *"Solo los mejores aceros son capaces de mezclarse para crear piezas únicas."*
- Acceso por QR único + cuestionario 20 preguntas
- Solo pasan los probados por el fuego
- Motor en: `motors/motor_forja.py`

---

## Iniciar el sistema

```bash
# Windows
INICIAR_NEXUS_v3.bat

# Manual
set PYTHONIOENCODING=utf-8
python nexus_core.py                    # Puerto 8003
python motors/motor_atf.py              # Puerto 8004
python motors/motor_teens.py            # Puerto 8005
python motors/motor_auth.py             # Puerto 8006
python motors/motor_pagos.py            # Puerto 8007
python motors/motor_reportes.py         # Puerto 8008
```

Abre: http://localhost:8003/

---

## Bug conocido activo

`GET /api/status` retorna 404 — el frontend lo llama para verificar conexión cada 30s.
Falta agregar el endpoint en `nexus_core.py`. El sistema funciona pero muestra "Desconectado".

---

## GitHub / Autor

- Repo: https://github.com/mocho47/NEXUS-CORE (privado)
- Autor: Anuar — Simplex GDL
- Sistema operando desde: 2026
