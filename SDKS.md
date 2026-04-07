# SDKs disponibles en esta PC — Mapa completo para Z.ai

> Python 3.12 en C:\Program Files\Python312\
> Todos verificados como instalados. Z.ai puede usarlos directamente.

---

## IA y Lenguaje

| SDK | Versión | Uso | Cómo llamar |
|-----|---------|-----|-------------|
| `groq` | 1.0.0 | LLM ultra-rápido (Groq Cloud) | `from groq import Groq` |
| `openai` | 2.30.0 | GPT + compatible con cualquier API OpenAI-like | `from openai import OpenAI` |
| `transformers` | 5.2.0 | Modelos HuggingFace locales | `from transformers import pipeline` |
| `torch` | 2.10.0+cpu | ML/Deep learning (CPU only — sin GPU) | `import torch` |
| `whisper` | 20250625 | Speech-to-text OpenAI Whisper | `import whisper` |
| `edge_tts` | 6.1.18 | TTS Microsoft Edge (es-MX-JorgeNeural) | `import edge_tts` |

**Modelos Ollama instalados localmente:**
- `qwen2.5:7b` — disponible y funcionando
- `glm4` — descargando (en background)

---

## Redes Sociales

| SDK | Versión | Uso | Estado |
|-----|---------|-----|--------|
| `instagrapi` | 2.3.0 | Instagram: publicar Reel, Historia, Post, DMs | ACTIVO — credenciales en .env |
| `google-api-python-client` | 2.192 | YouTube API, Google Drive, Gmail | Requiere OAuth |
| `twilio` | 9.10.3 | SMS + WhatsApp Business API | Requiere account SID en .env |
| `playwright` | (verificar) | Automatización browser: TikTok, FB grupos | Requiere `playwright install` |
| `requests-oauthlib` | 2.0.0 | OAuth2 para cualquier red social | Disponible |

**Instagram activo:**
```python
from instagrapi import Client
cl = Client()
cl.login(os.getenv('IG_USER'), os.getenv('IG_PASS'))
cl.clip_upload(path, caption)  # Reel
cl.photo_upload_to_story(path)  # Historia
```

**Publisher rotativo ATF ya funciona** — ver `motors/motor_social.py`

---

## Archivos y Diseño

| SDK | Versión | Uso |
|-----|---------|-----|
| `Pillow (PIL)` | — | Imágenes: resize, DPI, recorte, composición |
| `opencv (cv2)` | — | Visión computacional, contornos para láser |
| `reportlab` | 4.4.10 | PDF profesional 300 DPI, planillas, cotizaciones |
| `fpdf2` | 2.8.6 | PDFs simples rápidos |
| `ezdxf` | 1.4.3 | Archivos DXF para Corel/Silhouette/láser |
| `qrcode` | 8.2 | Generación de QR (ATF, FORJA, productos) |
| `barcode` | — | Códigos de barras |

---

## Video y Audio

| SDK | Versión | Uso |
|-----|---------|-----|
| `moviepy` | 1.0.3 | Editar video: corte, texto, transiciones, exportar |
| `ffmpeg-python` | 0.2.0 | Conversión video/audio (ffmpeg debe estar en PATH) |

**ffmpeg está instalado** — videos para IG/TikTok/FB:
```python
import ffmpeg
ffmpeg.input('input.mp4').output('vertical.mp4', vf='scale=1080:1920').run()
```

---

## Base de Datos y Cloud

| SDK | Versión | Uso |
|-----|---------|-----|
| `aiosqlite` | 0.20.0 | SQLite async (base local de NEXUS) |
| `supabase` | 2.27.2 | DB en la nube + auth + storage |
| `redis` | (verificar) | Cache + sesiones + colas |

---

## HTTP y APIs

| SDK | Versión | Uso |
|-----|---------|-----|
| `httpx` | 0.28.1 | HTTP async (llamadas entre motores) |
| `httpx-sse` | 0.4.3 | Server-Sent Events client |
| `requests` | 2.32.5 | HTTP sync |
| `fastapi` | 0.115.6 | API REST (servidor de cada motor) |

---

## Sistema Operativo

```python
import subprocess  # ejecutar comandos Windows
import os          # variables de entorno, paths
import shutil      # mover/copiar archivos
import pathlib     # manejo de rutas
import winreg      # registro de Windows (admin)
import ctypes      # llamadas al sistema Windows
```

---

## Apps instaladas (acceso directo)

| App | Ruta | Cómo abrir desde NEXUS |
|-----|------|------------------------|
| CorelDRAW | `C:\Program Files\Corel\...\CorelDRW.exe` | `subprocess.Popen([ruta])` |
| Silhouette Studio | Instalado | `subprocess.Popen(['SilhouetteStudio'])` |
| Aspire CNC | Instalado | `subprocess.Popen(['Aspire'])` |
| Ollama | En PATH | `subprocess.run(['ollama', 'pull', 'modelo'])` |
| Docker | En PATH | `subprocess.run(['docker', 'compose', 'up'])` |

**IMPORTANTE — CorelDRAW:** crackeado, sin internet, firewall bloqueado.
No intentar activaciones ni conexiones remotas. Solo abrir y ejecutar macros VBA.

---

## Datos reales del taller (en .env y DB)

```
IG_USER       → usuario Instagram ATF
IG_PASS       → contraseña Instagram
ATF_PHONE     → 3323530146 (tel cotizaciones)
TELEGRAM_*    → alertas críticas
GROQ_API_KEY  → LLM principal
ZAI_API_KEY   → LLM fallback
OPENROUTER_*  → Nemotron background
```

DB SQLite local: `data/nexus.db` (pedidos, clientes, misiones)
DB con datos reales: `E:\SIMPLEX_DATA\CONFIG\nexus_v2.db` (USB)

---

## Qué puede hacer Z.ai con todo esto

1. **Publicar en redes** — Instagram (Reel+Historia), preparar para TikTok/FB
2. **Generar archivos de taller** — DXF, planillas PDF 300 DPI, cotizaciones
3. **Procesar video** — convertir a vertical, agregar texto, exportar para redes
4. **Transcribir audio** — Whisper local (sin internet)
5. **Cotizar automáticamente** — ATF, Milens, con precios reales
6. **Gestionar pedidos y clientes** — leer/escribir en SQLite
7. **Enviar alertas** — Telegram (bot activo)
8. **Automatizar browser** — Playwright para TikTok, grupos FB
9. **Administrar el sistema** — procesos, archivos, configuración Windows
10. **Analizar con IA** — Groq + Whisper + Transformers

---

*Generado: 2026-04-07 | Verificado contra site-packages de Python 3.12*
