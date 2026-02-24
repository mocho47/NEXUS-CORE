# NEXUS_PRIVATE_PROTOCOLS (DEFINIDOS POR EL USUARIO)

Este archivo es tu “fuente de verdad” privada. El agente debe seguir estas reglas por defecto.

## 0) Cómo se usa
- Escribe reglas en formato claro y comprobable.
- Si algo requiere confirmación (red/firewall/permisos/credenciales), indícalo explícitamente.
- Si hay contradicciones, la regla más reciente (con fecha) gana.

---

## 1) Perfil operativo
- **Objetivo primario:** (ej. "Velocidad en taller sin romper estabilidad")
- **Tolerancia al riesgo:** (baja/media/alta)
- **Preferencias UI/UX:** (panel, logs, notificaciones, voz)

## 1.1 Privacidad (recomendado)
- Modo por defecto: `online` (nube habilitada) para máxima fluidez.
- Cuando requieras privacidad: di `bloquea nube` (en modo `online`, aplica solo a esta sesión; en `supervised` puede persistir).
- Si quieres arranque 100% privado: usar `INICIAR_NEXUS_PRIVADO.bat`.
- Activación sugerida (BAT): usar `INICIAR_NEXUS_PRIVADO.bat`.
- Comandos de voz/texto:
	- `autoriza nube` (habilita nube en modo supervised)
	- `bloquea nube` (corta nube)

## 1.2 Contraseñas / Login (bóveda local)
- Las credenciales se guardan cifradas en `CONFIG/VAULT_PRIVATE/`.
- Regla: **nunca** se dictan ni se imprimen contraseñas.
- Regla: antes de iniciar sesión o escribir credenciales, Nexus pide confirmación con código.
- Comandos:
	- `inicia sesión en Facebook` → Nexus pide confirmación.
	- `confirmo 1234` → ejecuta el login automático.
	- `cancela login` → cancela.

## 1.3 Operación Redes Sociales (modo manos libres)
- Regla: antes de **enviar** WhatsApp / publicar / comentar / escribir en redes, Nexus pide confirmación con código.
- Regla: no spam (nunca enviar a múltiples personas si no lo pides explícito).
- Opción (para no repetir códigos): puedes abrir una **ventana de autorización temporal** para acciones sensibles.
- Libreta local:
	- Contactos y páginas se guardan en `CONFIG/social_targets.json`.
- Comandos:
	- `autoriza acciones 10` (autoriza por 10 minutos envíos/abrir redes/instalaciones supervisadas; **no** aplica a logins con contraseñas)
	- `bloquea acciones` (revoca la ventana)
	- `estado autorizaciones` (dice si está activa)
	- `memoriza contacto Alfredo es +5213312345678`
	- `memoriza página canbusfix es https://www.facebook.com/tu_pagina`
	- `envía por whatsapp a Alfredo: texto...` (pide confirmación)
	- `dile a Alfredo que ... envíalo por whatsapp` (pide confirmación)
	- `en fb ve a pagina canbusfix` (pide confirmación)

## 1.4 Monitoreo (Watchtower local / "mis ojos")
- Regla: Nexus solo monitorea lo que **llega a tu PC** por canales autorizados (sin scraping oculto).
- Entrada estándar: `DROP_IN/INBOX/` (archivos `.json` o `.txt`).
- Comandos:
	- `cuantos mensajes` / `mensajes nuevos`
	- `lee mensajes 3`
	- `resumen mensajes 5`
	- `modo vigilancia` / `silencia vigilancia`
	- `monitor rendimiento` / `silencia rendimiento`
	- `reporte rendimiento`

## 1.5 Memoria larga (privada) + Sueño
- La memoria larga vive en `CONFIG/nexus_memory.db` (SQLite local).
- Comandos:
	- `anota ...` / `memoriza ...`
	- `recuerda ...`
	- `tarea ...` / `lista tareas` / `hecho tarea 3`
	- `duerme` (consolidación offline)

## 1.6 Autonomía (Jarvis, pero tú mandas)
- Regla: Nexus puede **proponer** acciones (sugerencias), pero para acciones externas (enviar, loguear, publicar, abrir sitios) requiere confirmación con código.

## 1.7 Auto-corrección (supervisada)
- Regla: antes de instalar dependencias, limpiar, o cualquier cambio/mejora, Nexus debe pedir confirmación con código.
- Comandos: `diagnostico` / `autorreparar`
- Nota: `diagnostico` incluye chequeo end-to-end (Supabase URL/DNS/TCP/keepalive si la nube está permitida).

## 1.8 Autolimpieza / Optimización continua (segura)
- Regla: NEXUS puede borrar automáticamente **solo basura generada por NEXUS** (logs/snapshots/temporales/voice_*.mp3).
- Regla: nunca borra ASSETS, TALLER, PEDIDOS, RESPALDO_MAESTRO ni archivos que no estén en targets.
- Comandos:
	- `autolimpieza estado`
	- `autolimpieza activar` / `autolimpieza desactivar`
	- `autolimpieza solo reporte`
	- `autolimpieza ahora`

## 1.9 Supabase (anti-pausa por inactividad)
- Objetivo: evitar que el proyecto Supabase se pause por falta de actividad.
- Regla: solo se ejecuta si la nube está permitida (`online` o `autoriza nube`).
- Config: `CONFIG/supabase_keepalive.json` y auditoría en `CONFIG/supabase_keepalive_last.json`.
- Comandos:
	- `supabase vivo estado`
	- `supabase vivo activar` / `supabase vivo desactivar`
	- `supabase vivo ahora` (ping manual)

## 1.10 Ayuda / lista de comandos
- Fuente de verdad: `NEXUS_COMMANDS.md`
- Comandos: `ayuda` / `comandos`

---

## 2) Protocolos por tarea (plantillas)

### 2.1 Permisos / Admin / Seguridad
- Regla:
- Confirmación requerida:
- Procedimiento (pasos exactos):

### 2.2 Voz
- Hotword/estilo:
- Respuesta esperada:
- Fallback si no hay internet:

### 2.3 Marketing
- Tono:
- Ofertas permitidas/prohibidas:
- Plantillas oficiales:

### 2.4 Video
- Longitud objetivo:
- Watermark/branding:
- Presets preferidos (ffmpeg/moviepy):

### 2.5 Base de datos
- Fuente de verdad (nube/local):
- Qué nunca se borra:
- Backups:

### 2.6 “Modo programador” (código generado)
- Dónde se guarda:
- Reglas de ejecución:
- Librerías permitidas:

### 2.7 Investigación Web (supervisada)
- Motores preferidos (DDG/Google/Bing):
- Fuentes confiables favoritas (docs oficiales, GitHub issues, etc.):
- Fuentes prohibidas:
- Máximo de fuentes a proponer (2–6 recomendado):
- Regla de aprobación: (ej. “no fetchear nada sin mi OK”)

### 2.7 Investigación Web (supervisada por mí)
- Fuentes permitidas (lista):
- Fuentes prohibidas:
- Nivel de evidencia requerido: (docs oficiales / issues / benchmarks / etc.)
- Reglas de aprobación: (ej. "no abrir links sin mi OK")
- Entornos objetivo típicos: (Windows-only / Windows+Linux / cloud)

---

## 3) Frases prohibidas / estilo (anti-manipulación)
- Prohibido usar:
- Formato de respuesta preferido:

---

## 4) Fecha y firma
- Última actualización:
- Autor:
