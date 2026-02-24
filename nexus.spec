# -*- mode: python ; coding: utf-8 -*-
# nexus.spec — NEXUS Business Suite v2026
# Generado para PyInstaller 6.x

import os
block_cipher = None

# Directorio raíz del proyecto
ROOT = os.path.abspath('.')

# ── DATOS A INCLUIR ──────────────────────────────────────────────────
datas = [
    # Templates HTML
    (os.path.join(ROOT, 'WEB', 'templates'), 'WEB/templates'),
    # Archivos estáticos
    (os.path.join(ROOT, 'WEB', 'static'),    'WEB/static'),
    # Configuración
    (os.path.join(ROOT, 'CONFIG'),           'CONFIG'),
    # Archivos de base de datos
    (os.path.join(ROOT, 'nexus_v2.db'),      '.'),
]

# Agregar solo si existen
extra = [
    ('PLAN_NEGOCIO', 'PLAN_NEGOCIO'),
    ('logs',         'logs'),
]
for src, dst in extra:
    full = os.path.join(ROOT, src)
    if os.path.exists(full):
        datas.append((full, dst))

# ── MÓDULOS OCULTOS ──────────────────────────────────────────────────
hiddenimports = [
    # FastAPI / Starlette / Uvicorn
    'fastapi',
    'fastapi.middleware',
    'fastapi.middleware.cors',
    'fastapi.responses',
    'fastapi.staticfiles',
    'fastapi.templating',
    'starlette',
    'starlette.middleware',
    'starlette.responses',
    'starlette.routing',
    'starlette.staticfiles',
    'starlette.templating',
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'anyio',
    'anyio._backends._asyncio',
    'anyio._backends._trio',
    # Templates
    'jinja2',
    'jinja2.ext',
    'jinja2.filters',
    'aiofiles',
    # Pydantic
    'pydantic',
    'pydantic.v1',
    # Base de datos
    'sqlite3',
    'supabase',
    'postgrest',
    # Módulos NEXUS propios
    'nexus_db',
    'nexus_core',
    'nexus_stock',
    'nexus_crm',
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
    'nexus_meta',
    'nexus_scheduler',
    'nexus_backup',
    'nexus_iot',
    'nexus_milens',
    'nexus_spy',
    'nexus_social',
    'nexus_coder',
    'nexus_catalog',
    'nexus_panel',
    'nexus_launcher',
    # Audio / Voz
    'pyttsx3',
    'pyttsx3.drivers',
    'pyttsx3.drivers.sapi5',
    # Utilidades
    'dotenv',
    'psutil',
    'requests',
    'multipart',
    'python_multipart',
    'email',
    'email.mime',
    'email.mime.text',
    'email.mime.multipart',
    'email.mime.application',
    'concurrent.futures',
    'asyncio',
    'threading',
    'hashlib',
    'secrets',
    'json',
    'logging',
    'pathlib',
    'platform',
    'subprocess',
    'importlib',
    'importlib.metadata',
]

# ── ANÁLISIS ─────────────────────────────────────────────────────────
a = Analysis(
    ['nexus_server.py'],
    pathex=[ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
        'torch',
        'tensorflow',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ── EXE ──────────────────────────────────────────────────────────────
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
    console=True,       # True = muestra terminal (para logs)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

# ── COLLECT (carpeta con todo) ────────────────────────────────────────
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
