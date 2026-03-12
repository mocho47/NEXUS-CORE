# -*- mode: python ; coding: utf-8 -*-
# nexus.spec — NEXUS Business Suite v2026 — VERSION FINAL
# Generado para PyInstaller 6.x

import os
block_cipher = None

ROOT = os.path.abspath('.')

# ── DATOS A INCLUIR ───────────────────────────────────────────────────────────
datas = [
    (os.path.join(ROOT, 'WEB', 'templates'), 'WEB/templates'),
    (os.path.join(ROOT, 'WEB', 'static'),    'WEB/static'),
    (os.path.join(ROOT, 'CONFIG'),           'CONFIG'),
]

# Opcionales — solo si existen
for src, dst in [
    ('nexus_v2.db',  '.'),
    ('PLAN_NEGOCIO', 'PLAN_NEGOCIO'),
    ('logs',         'logs'),
    ('LABORATORIO',  'LABORATORIO'),
    ('DROP_IN',      'DROP_IN'),
]:
    full = os.path.join(ROOT, src)
    if os.path.exists(full):
        datas.append((full, dst))

# ── MÓDULOS OCULTOS ───────────────────────────────────────────────────────────
hiddenimports = [
    # FastAPI / Starlette / Uvicorn
    'fastapi', 'fastapi.middleware', 'fastapi.middleware.cors',
    'fastapi.responses', 'fastapi.staticfiles', 'fastapi.templating',
    'starlette', 'starlette.middleware', 'starlette.responses',
    'starlette.routing', 'starlette.staticfiles', 'starlette.templating',
    'uvicorn', 'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto',
    'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan', 'uvicorn.lifespan.on',
    'anyio', 'anyio._backends._asyncio', 'anyio._backends._trio',
    # Templates / HTTP
    'jinja2', 'jinja2.ext', 'jinja2.filters', 'aiofiles',
    'httpx', 'httpx._transports.default', 'httpcore',
    # Pydantic
    'pydantic', 'pydantic.v1',
    # Base de datos
    'sqlite3', 'supabase', 'postgrest',
    # IA
    'groq', 'dotenv',
    # Audio
    'edge_tts',
    # Cripto
    'cryptography', 'cryptography.fernet',
    # Utilidades
    'psutil', 'requests', 'multipart', 'python_multipart',
    'email', 'email.mime', 'email.mime.text', 'email.mime.multipart',
    'email.mime.application', 'concurrent.futures', 'asyncio',
    'threading', 'hashlib', 'secrets', 'json', 'logging',
    'pathlib', 'platform', 'subprocess', 'importlib', 'importlib.metadata',
    'websockets', 'websockets.legacy',
    # ── MÓDULOS NEXUS CORE ───────────────────────────────────────────────────
    'nexus_cerebro',
    'nexus_db',
    'nexus_orders',
    'nexus_crm',
    'nexus_stock',
    'nexus_marketing',
    'nexus_assistant',
    'nexus_autoventas',
    'nexus_admin',
    'nexus_paranormal',
    'nexus_legal',
    'nexus_teens',
    'nexus_galeria',
    'nexus_license',
    'nexus_authorization',
    'nexus_notifier',
    'nexus_telegram',
    'nexus_scheduler',
    'nexus_backup',
    'nexus_milens',
    'nexus_spy',
    'nexus_social',
    'nexus_social_operator',
    'nexus_coder',
    'nexus_catalog',
    'nexus_panel',
    'nexus_finanzas',
    'nexus_video',
    'nexus_video_studio',
    'nexus_video_maker',
    'nexus_motion_video',
    'nexus_studio_module',
    'nexus_estudio',
    'nexus_merch_design',
    'nexus_image_processor',
    'nexus_cartoon_module',
    # ── MÓDULOS NUEVOS (v2026 final) ─────────────────────────────────────────
    'nexus_autonomo',
    'nexus_briefing',
    'nexus_meli',
    'nexus_dream',
    'nexus_autopilot',
    'nexus_self_heal',
    'nexus_doctor',
    'nexus_health',
    'nexus_logs',
    'nexus_memory',
    'nexus_vault',
    'nexus_watchtower',
    'nexus_housekeeping',
    'nexus_supabase_keepalive',
    'nexus_voz_router',
    'nexus_voz_v2',
    'nexus_voice',
    'nexus_agent',
    'nexus_market_analyzer',
    'nexus_boxes_gen',
    'nexus_planilla_stickers',
    'nexus_fingerprint',
    'nexus_atf' if os.path.exists(os.path.join(ROOT,'nexus_atf.py')) else None,
]
# Filtrar Nones
hiddenimports = [m for m in hiddenimports if m]

# ── ANÁLISIS ──────────────────────────────────────────────────────────────────
a = Analysis(
    ['nexus_server.py'],
    pathex=[ROOT],
    binaries=[
        # ffmpeg/ffprobe si existen
        *[(os.path.join(ROOT, b), '.') for b in ('ffmpeg.exe','ffprobe.exe')
          if os.path.exists(os.path.join(ROOT, b))],
    ],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'scipy', 'torch', 'tensorflow',
        'cv2', 'PIL', 'notebook', 'IPython',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ── EXE ───────────────────────────────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NEXUS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

# ── COLLECT ───────────────────────────────────────────────────────────────────
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NEXUS',
)
