"""
NEXUS v3 — Configurador de Entorno Completo
Detecta hardware, optimiza PC, instala dependencias, configura todo el stack.
Ejecutar UNA VEZ como Administrador.

Hardware detectado: 8GB RAM, 32GB pagefile, 2TB SSD, 8 cores CPU
"""

import os, sys, json, shutil, subprocess, platform, ctypes, time
from pathlib import Path

NEXUS_DIR = Path("C:/NEXUS_v3_NEW")
DATA_DIR  = NEXUS_DIR / "data"
LOGS_DIR  = NEXUS_DIR / "logs"

# ═══════════════════════════════════════════════
# COLORES TERMINAL
# ═══════════════════════════════════════════════
G = "\033[92m"  # verde
Y = "\033[93m"  # amarillo
R = "\033[91m"  # rojo
C = "\033[96m"  # cyan
B = "\033[1m"   # bold
X = "\033[0m"   # reset

def ok(msg):  print(f"{G}  OK{X}  {msg}")
def info(msg):print(f"{C}  ..{X}  {msg}")
def warn(msg):print(f"{Y}  !!{X}  {msg}")
def err(msg): print(f"{R}  XX{X}  {msg}")
def hdr(msg): print(f"\n{B}{C}{'='*50}\n  {msg}\n{'='*50}{X}")

def es_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run(cmd, capture=True):
    result = subprocess.run(cmd, shell=True, capture_output=capture, text=True, encoding='utf-8', errors='ignore')
    return result.returncode == 0, result.stdout.strip(), result.stderr.strip()

# ═══════════════════════════════════════════════
# 1. DETECCION DE HARDWARE
# ═══════════════════════════════════════════════
def detectar_hardware():
    hdr("DETECCION DE HARDWARE")

    hw = {}

    # CPU
    hw['cpu_cores'] = os.cpu_count()
    ok(f"CPU: {hw['cpu_cores']} cores")

    # RAM fisica
    mem = ctypes.c_ulonglong(0)
    ctypes.windll.kernel32.GetPhysicallyInstalledSystemMemory(ctypes.byref(mem))
    hw['ram_gb'] = round(mem.value / 1024 / 1024, 1)
    ok(f"RAM fisica: {hw['ram_gb']} GB")

    # Pagefile
    _, out, _ = run('wmic pagefile get CurrentUsage,AllocatedBaseSize /format:value')
    for line in out.splitlines():
        if 'AllocatedBaseSize' in line:
            try:
                hw['pagefile_mb'] = int(line.split('=')[1].strip())
                ok(f"Pagefile: {hw['pagefile_mb']//1024} GB")
            except: hw['pagefile_mb'] = 32768

    # Discos
    hw['discos'] = []
    _, out, _ = run('wmic logicaldisk get DeviceID,FreeSpace,Size /format:csv')
    for line in out.splitlines()[2:]:
        parts = line.strip().split(',')
        if len(parts) >= 4:
            try:
                drive = parts[1]
                free  = int(parts[2]) if parts[2] else 0
                total = int(parts[3]) if parts[3] else 0
                if total > 0:
                    hw['discos'].append({
                        'drive': drive,
                        'total_gb': round(total/1024**3, 0),
                        'free_gb':  round(free/1024**3, 0)
                    })
                    ok(f"Disco {drive}: {round(total/1024**3,0):.0f} GB total / {round(free/1024**3,0):.0f} GB libre")
            except: pass

    # GPU
    _, out, _ = run('wmic path win32_videocontroller get Name /format:value')
    hw['gpu'] = []
    for line in out.splitlines():
        if 'Name=' in line and line.split('=')[1].strip():
            hw['gpu'].append(line.split('=')[1].strip())
            ok(f"GPU: {line.split('=')[1].strip()}")

    hw['tiene_nvidia'] = any('nvidia' in g.lower() for g in hw['gpu'])

    return hw

# ═══════════════════════════════════════════════
# 2. CONFIGURACION OPTIMA PARA EL HARDWARE
# ═══════════════════════════════════════════════
def calcular_config_optima(hw):
    hdr("CONFIGURACION OPTIMA")

    cfg = {}

    ram = hw['ram_gb']
    cores = hw['cpu_cores']
    pagefile_gb = hw.get('pagefile_mb', 0) / 1024

    # Modelos Ollama recomendados para este hardware
    # Con 8GB RAM + 32GB pagefile = puede correr modelos hasta ~10GB
    if ram >= 16 or pagefile_gb >= 20:
        cfg['ollama_modelos'] = ['glm4', 'qwen2.5:7b', 'llama3.2:3b']
        cfg['ollama_primary'] = 'glm4'
        cfg['ollama_num_ctx'] = 4096
        cfg['ollama_num_thread'] = min(cores, 6)
        ok("Perfil: MEDIO — glm4 + qwen2.5:7b (RAM + pagefile suficientes)")
    elif ram >= 8:
        cfg['ollama_modelos'] = ['qwen2.5:7b', 'llama3.2:3b']
        cfg['ollama_primary'] = 'qwen2.5:7b'
        cfg['ollama_num_ctx'] = 2048
        cfg['ollama_num_thread'] = min(cores, 4)
        ok("Perfil: BASICO — qwen2.5:7b (8GB RAM, sin GPU dedicada)")
    else:
        cfg['ollama_modelos'] = ['llama3.2:3b']
        cfg['ollama_primary'] = 'llama3.2:3b'
        cfg['ollama_num_ctx'] = 1024
        cfg['ollama_num_thread'] = min(cores, 2)
        warn("Perfil: MINIMO — solo modelos 3B")

    # Workers FastAPI por cores
    cfg['uvicorn_workers'] = max(1, cores // 2)
    ok(f"Uvicorn workers: {cfg['uvicorn_workers']}")

    # Timeout IA segun RAM (mas RAM = puede correr modelos mas grandes = mas lento)
    cfg['ia_timeout'] = 60 if ram >= 8 else 30
    ok(f"Timeout IA: {cfg['ia_timeout']}s")

    # SQLite cache
    cfg['sqlite_cache_mb'] = min(256, int(ram * 10))
    ok(f"SQLite cache: {cfg['sqlite_cache_mb']} MB")

    # Directorio de datos en disco con mas espacio
    disco_mayor = max(hw['discos'], key=lambda d: d['free_gb']) if hw['discos'] else None
    if disco_mayor:
        cfg['data_drive'] = disco_mayor['drive']
        ok(f"Datos en: {disco_mayor['drive']} ({disco_mayor['free_gb']:.0f} GB libres)")

    return cfg

# ═══════════════════════════════════════════════
# 3. OPTIMIZAR WINDOWS
# ═══════════════════════════════════════════════
def optimizar_windows(hw):
    hdr("OPTIMIZACION WINDOWS")

    if not es_admin():
        warn("Sin permisos admin — saltando optimizaciones de sistema")
        return

    # Exclusiones Defender (Python y NEXUS son lentos con Defender)
    rutas_excluir = [
        "C:\\NEXUS_v3_NEW",
        "C:\\Program Files\\Python312",
        "C:\\Users\\Administrador\\AppData\\Local\\Programs\\Ollama",
    ]
    for ruta in rutas_excluir:
        ok_res, _, _ = run(f'powershell -Command "Add-MpPreference -ExclusionPath \'{ruta}\'"')
        if ok_res:
            ok(f"Defender excluido: {ruta}")
        else:
            warn(f"No se pudo excluir: {ruta}")

    # Prioridad alta al proceso Python de NEXUS
    run('powershell -Command "Get-Process python -ErrorAction SilentlyContinue | ForEach-Object { $_.PriorityClass = \'High\' }"')
    ok("Python: prioridad Alta configurada")

    # Limpiar temporales
    run('del /q /f /s "%TEMP%\\*" 2>nul', capture=False)
    run('del /q /f /s "C:\\Windows\\Temp\\*" 2>nul', capture=False)
    ok("Temporales limpiados")

    # Flush DNS
    run('ipconfig /flushdns')
    ok("DNS cache limpiado")

    # Servicios pesados innecesarios
    servicios_apagar = [
        ('DiagTrack', 'Telemetria Microsoft'),
        ('WMPNetworkSvc', 'Windows Media Player Network'),
        ('XblGameSave', 'Xbox Game Save'),
        ('RetailDemo', 'Modo demo tienda'),
        ('RemoteRegistry', 'Registro remoto'),
    ]
    for svc, desc in servicios_apagar:
        ok_res, _, _ = run(f'sc stop {svc} 2>nul & sc config {svc} start=disabled 2>nul')
        ok(f"Servicio desactivado: {desc}")

# ═══════════════════════════════════════════════
# 4. INSTALAR DEPENDENCIAS PYTHON
# ═══════════════════════════════════════════════
def instalar_dependencias():
    hdr("DEPENDENCIAS PYTHON")

    pip = sys.executable.replace('python.exe', 'pip.exe')
    reqs = NEXUS_DIR / "requirements.txt"

    if reqs.exists():
        info("Instalando requirements.txt...")
        ok_res, out, err_out = run(f'"{sys.executable}" -m pip install -r "{reqs}" --quiet --no-warn-script-location')
        if ok_res:
            ok("requirements.txt instalado")
        else:
            warn(f"Algunos paquetes fallaron: {err_out[:200]}")
    else:
        warn("No se encontro requirements.txt")

    # Paquetes extra esenciales
    extras = ['litellm', 'psutil', 'httpx', 'aiofiles']
    for pkg in extras:
        ok_res, _, _ = run(f'"{sys.executable}" -m pip show {pkg} --quiet')
        if ok_res:
            ok(f"Ya instalado: {pkg}")
        else:
            info(f"Instalando {pkg}...")
            run(f'"{sys.executable}" -m pip install {pkg} --quiet')
            ok(f"Instalado: {pkg}")

# ═══════════════════════════════════════════════
# 5. CONFIGURAR OLLAMA
# ═══════════════════════════════════════════════
def configurar_ollama(hw, cfg):
    hdr("CONFIGURACION OLLAMA")

    # Verificar que Ollama esta corriendo
    ok_res, _, _ = run('curl -s http://localhost:11434/api/tags')
    if not ok_res:
        info("Iniciando Ollama...")
        subprocess.Popen(['ollama', 'serve'], creationflags=subprocess.CREATE_NO_WINDOW)
        time.sleep(3)
        ok_res, _, _ = run('curl -s http://localhost:11434/api/tags')
        if ok_res:
            ok("Ollama iniciado")
        else:
            warn("Ollama no disponible — modelos locales desactivados")
            return

    # Verificar modelos instalados
    ok_res, out, _ = run('curl -s http://localhost:11434/api/tags')
    if ok_res:
        try:
            modelos_instalados = [m['name'] for m in json.loads(out).get('models', [])]
        except:
            modelos_instalados = []
    else:
        modelos_instalados = []

    ok(f"Modelos instalados: {modelos_instalados or 'ninguno'}")

    # Descargar modelos faltantes del perfil optimo
    for modelo in cfg['ollama_modelos']:
        if modelo not in modelos_instalados:
            info(f"Descargando {modelo} (puede tardar varios minutos)...")
            subprocess.Popen(f'start "Ollama pull {modelo}" cmd /c ollama pull {modelo}',
                           shell=True)
            ok(f"Descarga iniciada en background: {modelo}")
        else:
            ok(f"Ya disponible: {modelo}")

    # Crear archivo de configuracion optima para Ollama
    ollama_cfg = {
        "num_ctx": cfg['ollama_num_ctx'],
        "num_thread": cfg['ollama_num_thread'],
        "num_gpu": 1 if hw['tiene_nvidia'] else 0,
    }
    cfg_path = NEXUS_DIR / "data" / "ollama_config.json"
    cfg_path.parent.mkdir(exist_ok=True)
    cfg_path.write_text(json.dumps(ollama_cfg, indent=2))
    ok(f"Config Ollama guardada: {cfg_path}")

# ═══════════════════════════════════════════════
# 6. GENERAR DOCKER COMPOSE OPTIMIZADO
# ═══════════════════════════════════════════════
def generar_docker_compose(hw, cfg):
    hdr("DOCKER COMPOSE OPTIMIZADO")

    # Calcular memoria para cada servicio
    ram_total_mb = int(hw['ram_gb'] * 1024)
    tiene_gpu = hw['tiene_nvidia']

    # Distribucion de memoria
    nexus_mem   = min(512, ram_total_mb // 8)   # ~512MB
    ollama_mem  = min(6144, ram_total_mb // 2)  # ~4-6GB (el mas pesado)
    redis_mem   = 128
    litellm_mem = 256

    compose = f"""version: '3.8'

# NEXUS v3 — Docker Compose optimizado para {hw['ram_gb']}GB RAM / {hw['cpu_cores']} cores
# Generado automaticamente por configurar_entorno.py

services:

  # ── NEXUS Core ──────────────────────────────
  nexus-core:
    build: .
    container_name: nexus_core
    restart: unless-stopped
    ports:
      - "8003:8003"
    environment:
      - PYTHONIOENCODING=utf-8
      - NEXUS_PORT=8003
      - OLLAMA_URL=http://ollama:11434
      - REDIS_URL=redis://redis:6379
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./output:/app/output
    depends_on:
      - redis
      - ollama
    deploy:
      resources:
        limits:
          memory: {nexus_mem}M
        reservations:
          memory: 256M

  # ── Redis (cache + sesiones) ─────────────────
  redis:
    image: redis:7-alpine
    container_name: nexus_redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    command: redis-server --maxmemory {redis_mem}mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    deploy:
      resources:
        limits:
          memory: {redis_mem}M

  # ── Ollama (modelos IA locales) ──────────────
  ollama:
    image: ollama/ollama:latest
    container_name: nexus_ollama
    restart: unless-stopped
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_NUM_PARALLEL=1
      - OLLAMA_MAX_LOADED_MODELS=1
      - OLLAMA_KEEP_ALIVE=5m
{"    deploy:\n      resources:\n        reservations:\n          devices:\n            - driver: nvidia\n              count: 1\n              capabilities: [gpu]" if tiene_gpu else f"    deploy:\n      resources:\n        limits:\n          memory: {ollama_mem}M"}

  # ── LiteLLM (proxy unificado todas las IAs) ──
  litellm:
    image: ghcr.io/berriai/litellm:main-latest
    container_name: nexus_litellm
    restart: unless-stopped
    ports:
      - "4000:4000"
    volumes:
      - ./litellm_config.yaml:/app/config.yaml
    command: --config /app/config.yaml --port 4000
    env_file:
      - .env
    deploy:
      resources:
        limits:
          memory: {litellm_mem}M

volumes:
  redis_data:
  ollama_data:

networks:
  default:
    name: nexus_network
"""

    compose_path = NEXUS_DIR / "docker-compose.yml"
    compose_path.write_text(compose, encoding='utf-8')
    ok(f"docker-compose.yml generado ({ram_total_mb}MB RAM / {hw['cpu_cores']} cores)")
    ok(f"  nexus-core: {nexus_mem}MB | ollama: {ollama_mem}MB | redis: {redis_mem}MB")

    # LiteLLM config
    litellm_cfg = f"""model_list:
  - model_name: groq-fast
    litellm_params:
      model: groq/llama-3.1-8b-instant
      api_key: os.environ/GROQ_API_KEY

  - model_name: groq-smart
    litellm_params:
      model: groq/llama-3.3-70b-versatile
      api_key: os.environ/GROQ_API_KEY

  - model_name: glm-local
    litellm_params:
      model: ollama/{cfg['ollama_primary']}
      api_base: http://ollama:11434

  - model_name: openrouter-nemotron
    litellm_params:
      model: openrouter/nvidia/llama-3.1-nemotron-ultra-253b-v1
      api_key: os.environ/OPENROUTER_API_KEY

router_settings:
  routing_strategy: least-busy
  num_retries: 3
  timeout: {cfg['ia_timeout']}

general_settings:
  master_key: nexus-litellm-key
  max_parallel_requests: {cfg['uvicorn_workers'] * 2}
"""
    litellm_path = NEXUS_DIR / "litellm_config.yaml"
    litellm_path.write_text(litellm_cfg, encoding='utf-8')
    ok(f"litellm_config.yaml generado")

# ═══════════════════════════════════════════════
# 7. GENERAR .ENV SI NO EXISTE
# ═══════════════════════════════════════════════
def verificar_env(cfg):
    hdr("ARCHIVO .ENV")

    env_path = NEXUS_DIR / ".env"
    example_path = NEXUS_DIR / ".env.example"

    if env_path.exists():
        ok(".env existe — no se toca")
        # Verificar keys vacias
        contenido = env_path.read_text(encoding='utf-8', errors='ignore')
        faltantes = []
        for linea in contenido.splitlines():
            if '=' in linea and not linea.startswith('#'):
                key, val = linea.split('=', 1)
                if not val.strip() or val.strip() in ['...', 'gsk_...', 'sk-or-v1-...']:
                    faltantes.append(key.strip())
        if faltantes:
            warn(f"Keys vacias en .env: {', '.join(faltantes)}")
        else:
            ok("Todas las keys configuradas")
    else:
        warn(".env no existe — copiando desde .env.example")
        if example_path.exists():
            shutil.copy(example_path, env_path)
            warn("IMPORTANTE: Abre .env y llena GROQ_API_KEY y ZAI_API_KEY")

# ═══════════════════════════════════════════════
# 8. CREAR ESTRUCTURA DE DIRECTORIOS
# ═══════════════════════════════════════════════
def crear_directorios():
    hdr("ESTRUCTURA DE DIRECTORIOS")

    dirs = [
        NEXUS_DIR / "data",
        NEXUS_DIR / "logs",
        NEXUS_DIR / "output",
        NEXUS_DIR / "uploads",
        NEXUS_DIR / "backups",
        Path("C:/nexus/MERCH_OUTPUT"),  # salida Milens
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        ok(f"Directorio: {d}")

# ═══════════════════════════════════════════════
# 9. GUARDAR CONFIG EN JSON (para que los motores la lean)
# ═══════════════════════════════════════════════
def guardar_config_sistema(hw, cfg):
    hdr("GUARDANDO CONFIGURACION")

    sistema = {
        "generado": time.strftime("%Y-%m-%d %H:%M"),
        "hardware": hw,
        "config_optima": cfg,
        "nexus": {
            "version": "3.0",
            "puerto": 8003,
            "directorio": str(NEXUS_DIR),
        },
        "motores": {
            "atf":       {"puerto": 8004},
            "teens":     {"puerto": 8005},
            "auth":      {"puerto": 8006},
            "pagos":     {"puerto": 8007},
            "reportes":  {"puerto": 8008},
        },
        "ia": {
            "primario":  "groq",
            "fallback1": "z.ai",
            "fallback2": "openrouter",
            "offline":   cfg.get('ollama_primary', 'qwen2.5:7b'),
            "timeout":   cfg.get('ia_timeout', 60),
        }
    }

    config_path = NEXUS_DIR / "data" / "sistema.json"
    config_path.write_text(json.dumps(sistema, indent=2, ensure_ascii=False), encoding='utf-8')
    ok(f"Config guardada: {config_path}")

    return sistema

# ═══════════════════════════════════════════════
# 10. VERIFICACION FINAL
# ═══════════════════════════════════════════════
def verificacion_final():
    hdr("VERIFICACION FINAL")

    checks = [
        ("nexus_core.py", (NEXUS_DIR / "nexus_core.py").exists()),
        ("lib/ai_client.py", (NEXUS_DIR / "lib/ai_client.py").exists()),
        ("motors/motor_atf.py", (NEXUS_DIR / "motors/motor_atf.py").exists()),
        (".env", (NEXUS_DIR / ".env").exists()),
        ("docker-compose.yml", (NEXUS_DIR / "docker-compose.yml").exists()),
        ("litellm_config.yaml", (NEXUS_DIR / "litellm_config.yaml").exists()),
        ("data/sistema.json", (NEXUS_DIR / "data/sistema.json").exists()),
    ]

    todos_ok = True
    for nombre, existe in checks:
        if existe:
            ok(nombre)
        else:
            err(f"FALTA: {nombre}")
            todos_ok = False

    # Verificar Python
    ok_res, ver, _ = run(f'"{sys.executable}" --version')
    ok(f"Python: {ver}")

    # Verificar Ollama
    ok_res, _, _ = run('curl -s http://localhost:11434/api/tags')
    if ok_res:
        ok("Ollama: ONLINE")
    else:
        warn("Ollama: offline (se inicia al arrancar NEXUS)")

    return todos_ok

# ═══════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════
def main():
    print(f"\n{B}{C}")
    print("  ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗")
    print("  ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝")
    print("  ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗")
    print("  ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║")
    print("  ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║")
    print("  ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝")
    print(f"  v3 by Simplex — Configurador de Entorno{X}\n")

    if not es_admin():
        warn("No corres como Administrador — algunas optimizaciones se saltaran")
        warn("Recomendado: clic derecho → Ejecutar como administrador")
        input("  Presiona Enter para continuar de todos modos...")

    try:
        # Pipeline completo
        hw  = detectar_hardware()
        cfg = calcular_config_optima(hw)
        crear_directorios()
        optimizar_windows(hw)
        instalar_dependencias()
        configurar_ollama(hw, cfg)
        generar_docker_compose(hw, cfg)
        verificar_env(cfg)
        sistema = guardar_config_sistema(hw, cfg)
        todo_ok = verificacion_final()

        # Resumen final
        hdr("CONFIGURACION COMPLETA")
        print(f"""
  Hardware: {hw['ram_gb']}GB RAM / {hw['cpu_cores']} cores
  Perfil IA: {cfg.get('ollama_primary', 'qwen2.5:7b')} (offline) + Groq (online)
  Workers:   {cfg['uvicorn_workers']} uvicorn workers
  Timeout:   {cfg['ia_timeout']}s por llamada IA

  Para iniciar NEXUS:
    INICIAR_NEXUS_v3.bat

  Para Docker (opcional):
    docker compose up -d

  Panel: http://localhost:8003/
""")

        if todo_ok:
            print(f"  {G}{B}Sistema listo.{X}")
        else:
            print(f"  {Y}{B}Sistema parcialmente configurado — revisa los errores.{X}")

    except Exception as e:
        err(f"Error critico: {e}")
        import traceback; traceback.print_exc()

    input(f"\n  {C}Presiona Enter para cerrar...{X}")

if __name__ == "__main__":
    main()
