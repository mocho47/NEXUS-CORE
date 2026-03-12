# -*- mode: python ; coding: utf-8 -*-
# nexus_teens.spec — NEXUS Teens v2026 — Distribucion independiente
# PyInstaller 6.x

import os
block_cipher = None
ROOT = os.path.abspath('.')

datas = [
    (os.path.join(ROOT, 'WEB', 'templates', 'teens.html'),           'WEB/templates'),
    (os.path.join(ROOT, 'WEB', 'templates', 'teens_admin.html'),      'WEB/templates'),
    (os.path.join(ROOT, 'WEB', 'templates', 'teens_bienvenida.html'), 'WEB/templates'),
    (os.path.join(ROOT, 'WEB', 'static'),                             'WEB/static'),
]
for src, dst in [('CONFIG','CONFIG'), ('teens_sw.js','.')]:
    full = os.path.join(ROOT, src)
    if os.path.exists(full):
        datas.append((full, dst))

hiddenimports = [
    'fastapi', 'fastapi.middleware', 'fastapi.middleware.cors',
    'fastapi.responses', 'fastapi.staticfiles', 'fastapi.templating',
    'starlette', 'starlette.routing', 'starlette.staticfiles', 'starlette.templating',
    'uvicorn', 'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto',
    'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan', 'uvicorn.lifespan.on',
    'anyio', 'anyio._backends._asyncio',
    'jinja2', 'jinja2.ext', 'aiofiles',
    'pydantic', 'groq', 'dotenv',
    'sqlite3', 'supabase', 'postgrest',
    'requests', 'httpx',
    'threading', 'asyncio', 'json', 'hashlib', 'pathlib',
    'nexus_teens',
    'nexus_db',
    'nexus_license',
]

a = Analysis(
    ['nexus_teens_server.py'],
    pathex=[ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'torch', 'tensorflow', 'PIL', 'cv2'],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='NEXUS_Teens',
    debug=False,
    strip=False,
    upx=True,
    console=True,
    icon=None,
)

coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False, upx=True, upx_exclude=[],
    name='NEXUS_Teens',
)
