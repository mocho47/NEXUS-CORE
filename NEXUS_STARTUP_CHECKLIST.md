# NEXUS - Checklist de arranque (FULL)

## 1) Arranque recomendado
- Ejecuta `INICIAR_NEXUS_FULL.bat` (Control Center: web + core voz).
- Alternativa consola: `INICIAR_NEXUS.bat`.

## 2) Verificación rápida (2 minutos)
1. Di/escribe: `ayuda` → debe imprimir la lista actual.
2. Di/escribe: `diagnostico` → debe reportar dependencias + estado nube/Supabase.
3. Abre el panel móvil: `http://localhost:8000`.

## 3) Nube / Supabase (anti-pausa)
- Asegura que en `.env` exista:
  - `SUPABASE_URL=https://<project-ref>.supabase.co`
  - `SUPABASE_KEY=...`
- En Supabase Dashboard → Settings → API → Project URL (ese es el correcto).
- Comandos:
  - `supabase vivo estado`
  - `supabase vivo ahora`

## 4) “Ojos” y “brazos” (Jarvis supervisado)
- Ojos (local): `mensajes nuevos`, `lee mensajes 3`, `resumen mensajes 5`.
- Brazos (acciones sensibles): siempre pide confirmación por código.
  - `autoriza acciones 10` (ventana temporal)
  - `bloquea acciones`

## 5) Si algo falla
- Corre: `diagnostico` y sigue el “Siguiente: …” que te diga.
- Si es Supabase: normalmente es `SUPABASE_URL` incorrecto o red/DNS.
