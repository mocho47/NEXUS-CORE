"""
NEXUS - Generador de Manuales PDF
"""
from fpdf import FPDF
import os, datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR  = os.path.join(BASE_DIR, "docs")
os.makedirs(OUT_DIR, exist_ok=True)

VERDE  = (0, 200, 120)
NEGRO  = (10, 10, 10)
GRIS   = (60, 60, 60)
BLANCO = (255, 255, 255)
FECHA  = datetime.date.today().strftime("%d/%m/%Y")

def safe(t):
    """Convierte texto a latin-1 seguro."""
    t = t.replace('\u00f1','n').replace('\u00d1','N')  # n~
    t = t.replace('\u00e1','a').replace('\u00e9','e')
    t = t.replace('\u00ed','i').replace('\u00f3','o')
    t = t.replace('\u00fa','u').replace('\u00fc','u')
    t = t.replace('\u00c1','A').replace('\u00c9','E')
    t = t.replace('\u00cd','I').replace('\u00d3','O')
    t = t.replace('\u00da','U').replace('\u00bf','?')
    t = t.replace('\u00a1','!')
    return t.encode('latin-1', 'replace').decode('latin-1')

class PDF(FPDF):
    def __init__(self, doc_title):
        super().__init__()
        self.doc_title = doc_title
        self.set_auto_page_break(True, 18)
        self.set_margins(18, 18, 18)

    def header(self):
        self.set_fill_color(*NEGRO)
        self.rect(0, 0, 210, 14, 'F')
        self.set_text_color(*VERDE)
        self.set_font("Helvetica", "B", 9)
        self.set_xy(18, 3)
        self.cell(100, 8, safe(f"NEXUS | {self.doc_title}"), align="L")
        self.set_text_color(*GRIS)
        self.set_font("Helvetica", "", 8)
        self.set_xy(110, 3)
        self.cell(80, 8, f"v2026 | {FECHA}", align="R")
        self.ln(8)

    def footer(self):
        self.set_y(-12)
        self.set_fill_color(*NEGRO)
        self.rect(0, self.get_y(), 210, 12, 'F')
        self.set_text_color(*GRIS)
        self.set_font("Helvetica", "", 8)
        self.cell(0, 8, f"Pagina {self.page_no()}  |  NEXUS Sistema de Gestion", align="C")

    def W(self):
        return self.epw  # effective page width

    def set_left(self):
        self.set_x(self.l_margin)

    # ── Portada ────────────────────────────────────────────────────────────
    def portada(self, subtitulo, desc):
        self.add_page()
        self.set_fill_color(*NEGRO)
        self.rect(0, 0, 210, 297, 'F')
        self.set_fill_color(*VERDE)
        self.rect(0, 108, 210, 3, 'F')
        self.rect(0, 178, 210, 3, 'F')
        self.set_text_color(*VERDE)
        self.set_font("Helvetica", "B", 48)
        self.set_xy(0, 68)
        self.cell(210, 18, safe("NEXUS"), align="C")
        self.set_text_color(*BLANCO)
        self.set_font("Helvetica", "B", 20)
        self.set_xy(0, 118)
        self.cell(210, 12, safe(subtitulo), align="C")
        self.set_text_color(150, 150, 150)
        self.set_font("Helvetica", "", 11)
        self.set_xy(30, 188)
        self.multi_cell(150, 7, safe(desc), align="C")
        self.set_text_color(*GRIS)
        self.set_font("Helvetica", "", 10)
        self.set_xy(0, 262)
        self.cell(210, 8, f"Version 2026  |  Generado el {FECHA}", align="C")

    # ── Seccion ────────────────────────────────────────────────────────────
    def seccion(self, txt):
        self.ln(5)
        self.set_left()
        self.set_fill_color(14, 14, 14)
        self.set_text_color(*VERDE)
        self.set_font("Helvetica", "B", 13)
        self.cell(self.W(), 9, safe(f"  {txt}"), fill=True, ln=True)
        self.set_draw_color(*VERDE)
        self.set_left()
        self.ln(3)

    # ── Subtitulo ──────────────────────────────────────────────────────────
    def sub(self, txt):
        self.ln(2)
        self.set_left()
        self.set_text_color(*VERDE)
        self.set_font("Helvetica", "B", 10)
        self.cell(self.W(), 7, safe(txt), ln=True)
        self.set_left()

    # ── Parrafo ────────────────────────────────────────────────────────────
    def p(self, txt):
        self.set_left()
        self.set_font("Helvetica", "", 10)
        self.set_text_color(200, 200, 200)
        self.multi_cell(self.W(), 6, safe(txt))
        self.set_left()
        self.ln(2)

    # ── Bullet ────────────────────────────────────────────────────────────
    def li(self, txt, nivel=0):
        pad = 5 + nivel * 5
        self.set_left()
        self.set_font("Helvetica", "", 10)
        self.set_text_color(200, 200, 200)
        self.cell(pad, 6, "")
        self.cell(5, 6, "-")
        self.multi_cell(self.W() - pad - 5, 6, safe(txt))
        self.set_left()

    # ── Caja destacada ─────────────────────────────────────────────────────
    def caja(self, titulo, cuerpo, bg=(0, 60, 38)):
        self.set_left()
        self.ln(2)
        self.set_fill_color(*bg)
        self.set_text_color(*VERDE)
        self.set_font("Helvetica", "B", 9)
        self.cell(self.W(), 6, safe(f"  {titulo}"), fill=True, ln=True)
        self.set_left()
        self.set_fill_color(15, 28, 20)
        self.set_text_color(170, 210, 190)
        self.set_font("Helvetica", "", 9)
        self.multi_cell(self.W(), 6, safe(f"  {cuerpo}"), fill=True)
        self.set_left()
        self.ln(3)

    # ── Tabla ─────────────────────────────────────────────────────────────
    def tabla(self, cab, rows, ws=None):
        if ws is None:
            w = self.W() / len(cab)
            ws = [w] * len(cab)
        self.set_left()
        self.set_fill_color(*NEGRO)
        self.set_text_color(*VERDE)
        self.set_font("Helvetica", "B", 8)
        for i, c in enumerate(cab):
            self.cell(ws[i], 7, safe(c), border=1, fill=True)
        self.ln()
        self.set_left()
        self.set_text_color(200, 200, 200)
        self.set_font("Helvetica", "", 8)
        for ri, row in enumerate(rows):
            self.set_left()
            self.set_fill_color(16, 16, 16) if ri % 2 == 0 else self.set_fill_color(12, 12, 12)
            for i, cel in enumerate(row):
                self.cell(ws[i], 6, safe(str(cel)), border="B", fill=True)
            self.ln()
        self.set_left()
        self.ln(3)

    # ── Comando ────────────────────────────────────────────────────────────
    def cmd(self, comando, desc=""):
        self.set_left()
        self.set_fill_color(12, 22, 12)
        self.set_text_color(*VERDE)
        self.set_font("Courier", "B", 9)
        w = min(100, self.W())
        self.cell(w, 7, safe(f"  {comando}"), fill=True)
        if desc:
            self.set_text_color(140, 140, 140)
            self.set_font("Helvetica", "", 8)
            self.cell(self.W() - w, 7, safe(f"  {desc}"))
        self.ln(8)
        self.set_left()

    # ── Separador ──────────────────────────────────────────────────────────
    def sep(self):
        self.set_left()
        self.ln(2)
        self.set_draw_color(*GRIS)
        self.line(self.l_margin, self.get_y(), 210 - self.r_margin, self.get_y())
        self.ln(4)
        self.set_left()

    # ── Indice ─────────────────────────────────────────────────────────────
    def indice(self, items):
        self.set_left()
        self.set_font("Helvetica", "", 10)
        self.set_text_color(180, 180, 180)
        for num, titulo in items:
            self.set_left()
            self.cell(12, 7, safe(str(num) + "."), border="B")
            self.cell(self.W() - 12, 7, safe(titulo), border="B", ln=True)
        self.set_left()


# =============================================================================
#  MANUAL DE USUARIO
# =============================================================================
def manual_usuario():
    pdf = PDF("Manual de Usuario")

    # PORTADA
    pdf.portada(
        "MANUAL DE USUARIO",
        "Guia completa para el uso diario del sistema NEXUS.\n"
        "Gestion de pedidos, clientes, inventario y mas."
    )

    # INDICE
    pdf.add_page()
    pdf.seccion("INDICE")
    pdf.indice([
        (1,  "Que es NEXUS?"),
        (2,  "Como iniciar el sistema"),
        (3,  "El Panel Central (Dashboard)"),
        (4,  "Modulo de Pedidos"),
        (5,  "Modulo de Clientes"),
        (6,  "Inventario (Stock)"),
        (7,  "Cotizador"),
        (8,  "Agenda"),
        (9,  "Marketing"),
        (10, "Acceso desde el celular"),
        (11, "Preguntas frecuentes"),
    ])

    # 1. QUE ES NEXUS
    pdf.add_page()
    pdf.seccion("1. Que es NEXUS?")
    pdf.p(
        "NEXUS es un sistema de gestion empresarial para negocios de produccion "
        "personalizada: laser, sublimacion, DTF, retrofit, neon, y mas. "
        "Funciona en tu computadora y es accesible desde celular en la misma red."
    )
    pdf.sub("Que puedo hacer con NEXUS?")
    for item in [
        "Registrar y dar seguimiento a pedidos de clientes",
        "Administrar tu base de clientes con datos de contacto",
        "Controlar el inventario de materiales e insumos",
        "Generar cotizaciones rapidas y profesionales",
        "Programar citas y tareas en la agenda",
        "Crear campanas de marketing",
        "Ver reportes de ventas e historial",
        "Acceder desde tu celular via codigo QR",
    ]:
        pdf.li(item)
    pdf.caja("IMPORTANTE",
        "NEXUS no requiere internet para funcionar. Todo se guarda localmente.\n"
        "Internet solo se usa para sincronizacion con la nube (opcional).")

    # 2. COMO INICIAR
    pdf.seccion("2. Como iniciar el sistema")
    pdf.sub("Metodo rapido - Acceso directo del escritorio")
    pdf.p(
        "En el escritorio de Windows encontraras el icono NEXUS (circulo azul con N blanca). "
        "Haz doble clic. El sistema inicia automaticamente y abre el panel en tu navegador. "
        "Espera 3-4 segundos la primera vez."
    )
    pdf.sub("Metodo alternativo - Desde la carpeta")
    pdf.p("Si el acceso directo no funciona, ve a C:\\nexus\\ y ejecuta:")
    pdf.cmd("INICIAR_NEXUS_FULL.bat", "Abre todo el sistema completo")
    pdf.sub("Como se que esta funcionando?")
    for item in [
        "Se abre tu navegador con el panel en pantalla",
        "En la barra superior del panel dice ONLINE",
        "La direccion es: http://localhost:8000/dashboard",
    ]:
        pdf.li(item)
    pdf.caja("CONSEJO",
        "Deja la ventana del sistema minimizada mientras trabajas.\n"
        "No la cierres o el sistema se apagara.")

    # 3. PANEL CENTRAL
    pdf.add_page()
    pdf.seccion("3. El Panel Central (Dashboard)")
    pdf.p(
        "El panel central es tu punto de entrada. Accede a todos los modulos "
        "sin cambiar de pagina, usando las pestanas superiores."
    )
    pdf.sub("Las pestanas del panel")
    pdf.tabla(
        ["Pestana", "Funcion"],
        [
            ["Inicio",     "Resumen general: pedidos urgentes, stock bajo, estado del sistema"],
            ["Pedidos",    "Ver todos los pedidos, agregar nuevos, marcar como listos"],
            ["Clientes",   "Lista de clientes, agregar, buscar, ir a WhatsApp"],
            ["Stock",      "Inventario de materiales, agregar items, ver alertas de stock"],
            ["Cotizar",    "Cotizador rapido y cotizador profesional"],
            ["Agenda",     "Citas y tareas programadas"],
            ["Marketing",  "Campanas y comunicacion con clientes"],
            ["Config",     "Configuracion del negocio, precios, acceso movil"],
        ],
        ws=[45, 130]
    )
    pdf.sub("Los KPIs (numeros de resumen)")
    pdf.p(
        "En la pestana Inicio veras 4 numeros grandes:\n"
        "- Pendientes: cuantos pedidos estan sin terminar (amarillo = hay pedidos)\n"
        "- Clientes: total de clientes registrados\n"
        "- Stock items: total de materiales en inventario\n"
        "- Stock bajo: materiales con 3 unidades o menos (rojo = reponer)"
    )

    # 4. PEDIDOS
    pdf.add_page()
    pdf.seccion("4. Modulo de Pedidos")
    pdf.sub("Agregar un nuevo pedido")
    pdf.p("Ve a la pestana Pedidos. En la parte superior completa el formulario:")
    pdf.tabla(
        ["Campo", "Descripcion", "Ejemplo"],
        [
            ["Cliente",   "Nombre del cliente",              "Maria Garcia"],
            ["Producto",  "Descripcion de lo que hacer",     "Taza sublimada con foto"],
            ["Entrega",   "Fecha y hora de entrega",         "2026-03-01 14:00"],
        ],
        ws=[35, 100, 45]
    )
    pdf.p("Haz clic en '+ Agregar'. El pedido aparecera en la lista de abajo.")
    pdf.sub("Estados de un pedido")
    pdf.tabla(
        ["Estado", "Significado"],
        [
            ["PENDIENTE",  "Pedido registrado, aun en proceso"],
            ["LISTO",      "Produccion terminada, esperando entrega al cliente"],
            ["ENTREGADO",  "El cliente ya recibio su pedido"],
        ],
        ws=[40, 135]
    )
    pdf.sub("Marcar un pedido como listo")
    pdf.p(
        "En la columna de acciones, haz clic en '[OK] Listo'. "
        "El estado cambiara a LISTO y el cliente recibira una notificacion "
        "automatica si Telegram esta configurado."
    )
    pdf.caja("PEDIDOS URGENTES",
        "En la pestana Inicio, los pedidos pendientes aparecen al tope\n"
        "para que los veas de inmediato.")

    # 5. CLIENTES
    pdf.add_page()
    pdf.seccion("5. Modulo de Clientes")
    pdf.sub("Agregar un cliente")
    pdf.p("Ve a la pestana Clientes. Llena el formulario superior:")
    pdf.tabla(
        ["Campo",    "Obligatorio", "Descripcion"],
        [
            ["Nombre",   "Si",  "Nombre completo del cliente"],
            ["Telefono", "Si",  "10 digitos sin espacios (ej: 8121234567)"],
            ["Email",    "No",  "Correo electronico para contacto"],
        ],
        ws=[35, 30, 110]
    )
    pdf.sub("Buscar un cliente")
    pdf.p("Usa la barra de busqueda para filtrar la lista en tiempo real por nombre, telefono o email.")
    pdf.sub("Contactar por WhatsApp")
    pdf.p(
        "En la columna Acciones de cada cliente, el icono [WA] abre directamente "
        "una conversacion de WhatsApp con ese numero (10 digitos)."
    )
    pdf.sub("Ver el perfil completo del cliente")
    pdf.p("Haz clic en 'Perfil' para ver el historial de pedidos y notas del cliente.")

    # 6. STOCK
    pdf.add_page()
    pdf.seccion("6. Inventario (Stock)")
    pdf.p(
        "El inventario te permite saber que materiales tienes disponibles, "
        "su cantidad y precio. El sistema avisa cuando un material baja de 3 unidades."
    )
    pdf.sub("Agregar un material")
    pdf.tabla(
        ["Campo",     "Descripcion",                     "Ejemplo"],
        [
            ["Nombre",    "Nombre del material",             "Vinyl negro 30cm"],
            ["Cantidad",  "Unidades disponibles",            "50"],
            ["Precio $",  "Costo unitario del material",     "12.50"],
            ["Categoria", "Tipo de proceso",                 "LASER / DTF / SUBLIMACION"],
        ],
        ws=[30, 100, 45]
    )
    pdf.sub("Categorias disponibles")
    for cat in [
        "GENERAL  - Materiales de uso general",
        "LASER    - Materiales para corte/grabado laser",
        "SUBLIMACION - Papeles, tazas, playeras",
        "RETROFIT - Materiales para retrofitting",
        "DTF      - Films y polvos DTF",
        "NEON     - Cables y materiales de neon",
    ]:
        pdf.li(cat)
    pdf.caja("ALERTA STOCK BAJO",
        "Cuando un material llega a 3 unidades o menos, aparece en rojo\n"
        "en el inventario y en las alertas del panel de Inicio.")

    # 7. COTIZADOR
    pdf.add_page()
    pdf.seccion("7. Cotizador")
    pdf.sub("Cotizador Rapido")
    pdf.p("Para cotizaciones simples y rapidas. Ideal para dar un precio aproximado al cliente en el momento.")
    pdf.sub("Cotizador Pro")
    pdf.p("Cotizacion completa con desglose por categoria, materiales y costos. Mas detallado y profesional.")
    pdf.p("Accede a ambos desde la pestana Cotizar del panel.")

    # 8. AGENDA
    pdf.seccion("8. Agenda")
    pdf.p("La agenda te permite programar citas, recordatorios y tareas con fecha y hora.")
    pdf.li("Programa entregas de pedidos como eventos")
    pdf.li("Registra citas con clientes")
    pdf.li("Agrega recordatorios de pago o reposicion de materiales")

    # 9. MARKETING
    pdf.seccion("9. Marketing")
    pdf.p("El modulo de marketing permite crear y gestionar campanas de comunicacion con tus clientes.")
    pdf.li("Crear campanas con titulo, mensaje y audiencia")
    pdf.li("Conectar con Instagram (Meta API)")
    pdf.li("Enviar mensajes a grupos de clientes")

    # 10. CELULAR
    pdf.add_page()
    pdf.seccion("10. Acceso desde el celular")
    pdf.p(
        "Puedes acceder a NEXUS desde tu celular siempre que este conectado "
        "al mismo Wi-Fi que tu computadora."
    )
    pdf.sub("Pasos para conectarte:")
    for paso in [
        "1. Asegurate de que el sistema NEXUS esta corriendo en la computadora",
        "2. Conecta tu celular al mismo Wi-Fi",
        "3. Ve a Config -> Acceso Movil (QR) en el panel",
        "4. Escanea el codigo QR con la camara del celular",
        "5. El navegador del celular abrira el panel de NEXUS",
    ]:
        pdf.li(paso)
    pdf.caja("CONSEJO",
        "Guarda la IP en el navegador de tu celular como favorito\n"
        "para acceder rapido (ej: http://192.168.1.100:8000).")

    # 11. FAQ
    pdf.add_page()
    pdf.seccion("11. Preguntas Frecuentes")
    faq = [
        ("El panel no abre",
         "Haz doble clic en el acceso directo NEXUS del escritorio. Si sigue sin abrir,\n"
         "ve a C:\\nexus\\ y ejecuta INICIAR_NEXUS_FULL.bat"),
        ("Puedo usar NEXUS sin internet?",
         "Si, todo funciona localmente. El internet solo es necesario para la\n"
         "sincronizacion con la nube o para el modulo de marketing."),
        ("Los datos se pierden si apago la computadora?",
         "No. Todo se guarda en la base de datos local y en la nube de respaldo."),
        ("Como busco un pedido especifico?",
         "En la pestana Pedidos veras toda la lista. Usa el scroll para navegar."),
        ("Como cambio el precio de un servicio?",
         "Ve a Config -> Precios base. Ahi puedes editar los precios del cotizador."),
        ("Puedo agregar fotos a los pedidos?",
         "Esta funcion esta en desarrollo. Por ahora escribe la descripcion completa\n"
         "en el campo Producto."),
    ]
    for preg, resp in faq:
        pdf.sub(f"? {safe(preg)}")
        pdf.p(resp)
        pdf.sep()

    out = os.path.join(OUT_DIR, "NEXUS_Manual_Usuario.pdf")
    pdf.output(out)
    print(f"[OK] Manual de Usuario  ->  {out}")
    return out


# =============================================================================
#  MANUAL DE ADMINISTRADOR
# =============================================================================
def manual_admin():
    pdf = PDF("Manual de Administrador")

    # PORTADA
    pdf.portada(
        "MANUAL DE ADMINISTRADOR",
        "Guia tecnica de configuracion, mantenimiento\n"
        "y administracion del sistema NEXUS."
    )

    # INDICE
    pdf.add_page()
    pdf.seccion("INDICE")
    pdf.indice([
        (1,  "Arquitectura del sistema"),
        (2,  "Requisitos e instalacion"),
        (3,  "Estructura de directorios"),
        (4,  "Modulos del sistema"),
        (5,  "Configuracion de base de datos"),
        (6,  "Servidor web y rutas API"),
        (7,  "Variables de entorno (.env)"),
        (8,  "Respaldo y recuperacion"),
        (9,  "Comandos de administracion"),
        (10, "Configuracion de Telegram"),
        (11, "Configuracion de Meta / Instagram"),
        (12, "Mantenimiento y logs"),
        (13, "Solucion de problemas"),
    ])

    # 1. ARQUITECTURA
    pdf.add_page()
    pdf.seccion("1. Arquitectura del sistema")
    pdf.p(
        "NEXUS es una aplicacion Python que combina un servidor web local (FastAPI/Uvicorn) "
        "con modulos especializados por area. Sincroniza opcionalmente con Supabase "
        "(PostgreSQL en la nube) para respaldo y acceso remoto."
    )
    pdf.sub("Stack tecnologico")
    pdf.tabla(
        ["Capa", "Tecnologia", "Uso"],
        [
            ["Backend",   "Python 3.10+ / FastAPI", "Servidor web y logica de negocio"],
            ["Frontend",  "HTML5 / CSS3 / JS",      "Interfaz web del panel"],
            ["Templates", "Jinja2",                  "Renderizado de paginas HTML"],
            ["BD Local",  "SQLite (nexus_v2.db)",   "Almacenamiento local primario"],
            ["BD Nube",   "Supabase (PostgreSQL)",   "Sincronizacion y respaldo"],
            ["Voz",       "ElevenLabs API",           "Sintesis de voz (opcional)"],
            ["IA",        "Groq / Claude API",        "Asistente inteligente"],
            ["Notif.",    "Telegram Bot API",         "Notificaciones de pedidos"],
        ],
        ws=[28, 52, 95]
    )

    # 2. INSTALACION
    pdf.add_page()
    pdf.seccion("2. Requisitos e instalacion")
    pdf.sub("Requisitos minimos")
    pdf.tabla(
        ["Componente", "Minimo", "Recomendado"],
        [
            ["Python",    "3.10",          "3.11 o superior"],
            ["RAM",       "2 GB",          "4 GB"],
            ["Disco",     "500 MB libres", "2 GB libres"],
            ["Windows",   "10",            "11"],
            ["Navegador", "Chrome / Edge", "Chrome actualizado"],
        ],
        ws=[45, 50, 80]
    )
    pdf.sub("Instalacion desde cero")
    for c, d in [
        ("git clone <repo> C:\\nexus",    "Clonar el repositorio"),
        ("cd C:\\nexus",                   "Entrar al directorio"),
        ("pip install -r requirements.txt","Instalar dependencias"),
        ("python setup_nexus.py",          "Configuracion inicial"),
        ("python nexus_server.py",         "Iniciar el servidor"),
    ]:
        pdf.cmd(c, d)

    pdf.sub("Dependencias principales")
    for dep in [
        "fastapi    - Framework web",
        "uvicorn    - Servidor ASGI",
        "jinja2     - Templates HTML",
        "supabase   - Cliente Supabase",
        "fpdf2      - Generacion de PDFs",
        "psutil     - Monitoreo del sistema",
        "pillow     - Procesamiento de imagenes",
    ]:
        pdf.li(dep)

    # 3. DIRECTORIOS
    pdf.add_page()
    pdf.seccion("3. Estructura de directorios")
    pdf.tabla(
        ["Ruta", "Descripcion"],
        [
            ["C:\\nexus\\",                 "Directorio raiz del sistema"],
            ["C:\\nexus\\nexus_server.py",  "Servidor web principal (FastAPI)"],
            ["C:\\nexus\\nexus_v2.db",      "Base de datos SQLite local"],
            ["C:\\nexus\\CONFIG\\",         "Archivos de configuracion JSON"],
            ["C:\\nexus\\WEB\\templates\\", "Plantillas HTML del panel"],
            ["C:\\nexus\\WEB\\static\\",    "Archivos estaticos (CSS, imagenes)"],
            ["C:\\nexus\\logs\\",           "Logs del sistema por mes"],
            ["C:\\nexus\\docs\\",           "Documentacion y manuales PDF"],
            ["C:\\nexus\\RESPALDO_MAESTRO\\","Respaldos de configuracion"],
            ["C:\\nexus\\.env",             "Variables de entorno (secretos)"],
        ],
        ws=[65, 110]
    )
    pdf.caja("SEGURIDAD",
        "El archivo .env contiene claves API y credenciales. NUNCA lo compartas\n"
        "ni lo subas a repositorios publicos (Git). Esta en .gitignore.",
        bg=(70, 20, 0))

    # 4. MODULOS
    pdf.add_page()
    pdf.seccion("4. Modulos del sistema")
    pdf.tabla(
        ["Modulo", "Archivo", "Funcion"],
        [
            ["Servidor Web",  "nexus_server.py",   "FastAPI - rutas y API REST"],
            ["Base de datos", "nexus_db.py",        "SQLite + Supabase"],
            ["Pedidos",       "nexus_orders.py",    "Gestion de ordenes de trabajo"],
            ["CRM",           "nexus_crm.py",       "Clientes y contactos"],
            ["Stock",         "nexus_stock.py",     "Inventario de materiales"],
            ["Catalogo",      "nexus_catalog.py",   "Catalogo de productos"],
            ["Marketing",     "nexus_marketing.py", "Campanas y comunicacion"],
            ["Voz",           "nexus_voice.py",     "Sintesis de voz ElevenLabs"],
            ["Video",         "nexus_video.py",     "Procesamiento de videos"],
            ["Notificador",   "nexus_notifier.py",  "Telegram y alertas"],
            ["Scheduler",     "nexus_scheduler.py", "Tareas programadas"],
            ["Respaldo",      "nexus_backup.py",    "Backup automatico"],
            ["Monitor",       "system_monitor.py",  "CPU, RAM, disco"],
            ["Meta/IG",       "nexus_meta.py",      "Instagram y WhatsApp API"],
            ["Telegram",      "nexus_telegram.py",  "Bot de Telegram"],
            ["Asistente IA",  "nexus_assistant.py", "Consultas con IA (Groq)"],
            ["Launcher",      "nexus_launcher.py",  "Orquestador del sistema"],
        ],
        ws=[35, 50, 90]
    )

    # 5. BASE DE DATOS
    pdf.add_page()
    pdf.seccion("5. Configuracion de base de datos")
    pdf.sub("Base de datos local (SQLite)")
    pdf.p("El archivo nexus_v2.db en C:\\nexus\\ contiene todas las tablas. Se crea automaticamente.")
    pdf.tabla(
        ["Tabla", "Contenido"],
        [
            ["pedidos",   "Ordenes de trabajo: estado, cliente, producto, fechas"],
            ["clientes",  "Base de clientes: nombre, telefono, email"],
            ["stock",     "Inventario: nombre, cantidad, precio, categoria"],
            ["agenda",    "Citas y eventos programados"],
            ["campanas",  "Campanas de marketing"],
        ],
        ws=[40, 135]
    )
    pdf.sub("Supabase (nube)")
    pdf.p("Para configurar Supabase, agrega al archivo .env las siguientes variables:")
    pdf.cmd("SUPABASE_URL=https://tu-proyecto.supabase.co")
    pdf.cmd("SUPABASE_KEY=tu_anon_key_aqui")
    pdf.p("La sincronizacion es automatica. Si no hay conexion, trabaja en modo local.")

    # 6. RUTAS API
    pdf.add_page()
    pdf.seccion("6. Servidor web y rutas API")
    pdf.sub("Rutas principales del panel")
    pdf.tabla(
        ["Ruta",              "Metodo", "Descripcion"],
        [
            ["/dashboard",      "GET",  "Panel central con tabs"],
            ["/pedidos",        "GET",  "Lista de pedidos"],
            ["/clientes",       "GET",  "Lista de clientes"],
            ["/stock",          "GET",  "Inventario"],
            ["/cotizar-rapido", "GET",  "Cotizador rapido"],
            ["/cotizar",        "GET",  "Cotizador profesional"],
            ["/agenda",         "GET",  "Agenda"],
            ["/marketing",      "GET",  "Panel de marketing"],
            ["/historial",      "GET",  "Historial de pedidos"],
            ["/qr",             "GET",  "Codigo QR acceso movil"],
            ["/precios_admin",  "GET",  "Administracion de precios"],
            ["/config_negocio", "GET",  "Configuracion del negocio"],
            ["/reporte",        "GET",  "Reportes de ventas"],
        ],
        ws=[52, 20, 103]
    )
    pdf.sub("Endpoints API (JSON)")
    pdf.tabla(
        ["Endpoint",          "Metodo", "Respuesta"],
        [
            ["/api/nexus_status",  "GET",  "Estado del sistema y modulos"],
            ["/api/pedidos",       "GET",  "Lista completa de pedidos JSON"],
            ["/api/clientes",      "GET",  "Lista de clientes JSON"],
            ["/api/stock",         "GET",  "Inventario JSON"],
            ["/api/resumen",       "GET",  "Resumen ejecutivo del dia"],
            ["/api/system",        "GET",  "CPU, RAM y uso de disco"],
            ["/nuevo_pedido",      "POST", "Crear un pedido nuevo"],
            ["/nuevo_cliente",     "POST", "Registrar un cliente"],
            ["/nuevo_item_stock",  "POST", "Agregar item al inventario"],
            ["/marcar_listo",      "POST", "Cambiar pedido a LISTO"],
            ["/marcar_entregado",  "POST", "Cambiar pedido a ENTREGADO"],
            ["/eliminar_pedido",   "POST", "Eliminar un pedido"],
        ],
        ws=[52, 20, 103]
    )

    # 7. VARIABLES DE ENTORNO
    pdf.add_page()
    pdf.seccion("7. Variables de entorno (.env)")
    pdf.tabla(
        ["Variable",           "Descripcion"],
        [
            ["SUPABASE_URL",       "URL del proyecto Supabase"],
            ["SUPABASE_KEY",       "Clave anonima de Supabase"],
            ["ELEVENLABS_API_KEY", "Clave para sintesis de voz"],
            ["TELEGRAM_BOT_TOKEN", "Token del bot de Telegram"],
            ["TELEGRAM_CHAT_ID",   "ID del chat para notificaciones"],
            ["META_ACCESS_TOKEN",  "Token de acceso Meta/Instagram"],
            ["META_PHONE_ID",      "ID numero WhatsApp Business"],
            ["META_IG_USER_ID",    "ID cuenta Instagram"],
            ["GROQ_API_KEY",       "Clave API de Groq (IA)"],
        ],
        ws=[55, 120]
    )
    pdf.caja("EJEMPLO DE ARCHIVO .env",
        "SUPABASE_URL=https://xyz.supabase.co\n"
        "SUPABASE_KEY=eyJhbGci...\n"
        "TELEGRAM_BOT_TOKEN=123456:ABC-DEF\n"
        "TELEGRAM_CHAT_ID=-100123456789")

    # 8. RESPALDO
    pdf.add_page()
    pdf.seccion("8. Respaldo y recuperacion")
    pdf.sub("Respaldo automatico")
    pdf.p("NEXUS hace respaldos automaticos en C:\\nexus\\RESPALDO_MAESTRO\\")
    pdf.sub("Respaldo manual")
    pdf.cmd("python nexus_backup.py", "Genera un respaldo inmediato")
    pdf.sub("Archivos criticos a respaldar")
    for f in [
        "nexus_v2.db    - Base de datos completa",
        ".env           - Credenciales y claves API",
        "CONFIG/        - Toda la carpeta de configuracion",
        "WEB/templates/ - Plantillas personalizadas",
    ]:
        pdf.li(f)
    pdf.caja("RECOMENDACION",
        "Copia manual semanal de nexus_v2.db a USB o Google Drive.\n"
        "En caso de fallo del disco, este archivo contiene TODOS los datos.")

    # 9. COMANDOS
    pdf.add_page()
    pdf.seccion("9. Comandos de administracion")
    pdf.sub("Iniciar y detener")
    for c, d in [
        ("python nexus_server.py",     "Iniciar servidor web (puerto 8000)"),
        ("INICIAR_NEXUS_FULL.bat",      "Iniciar todo el ecosistema"),
        ("Ctrl + C",                    "Detener el servidor (en la terminal)"),
    ]:
        pdf.cmd(c, d)
    pdf.sub("Mantenimiento")
    for c, d in [
        ("python nexus_backup.py",      "Generar respaldo manual"),
        ("python nexus_housekeeping.py","Limpieza de archivos temporales"),
        ("python system_monitor.py",    "Ver estado del sistema"),
        ("python generar_manuales.py",  "Regenerar los manuales PDF"),
        ("python check_supabase.py",    "Verificar conexion a la nube"),
    ]:
        pdf.cmd(c, d)

    # 10. TELEGRAM
    pdf.add_page()
    pdf.seccion("10. Configuracion de Telegram")
    pdf.p("NEXUS envia notificaciones automaticas cuando un pedido se marca como listo.")
    pdf.sub("Pasos de configuracion")
    for paso in [
        "1. Abre Telegram y busca @BotFather",
        "2. Escribe /newbot y sigue las instrucciones",
        "3. Copia el token que te da BotFather",
        "4. Agrega en .env:  TELEGRAM_BOT_TOKEN=tu_token",
        "5. Inicia una conversacion con tu bot y escribe /start",
        "6. Visita: api.telegram.org/bot<TOKEN>/getUpdates",
        "7. Copia el chat_id y agrega en .env:  TELEGRAM_CHAT_ID=tu_chat_id",
        "8. Reinicia NEXUS para aplicar cambios",
    ]:
        pdf.li(paso)
    pdf.caja("NOTA",
        "Las notificaciones se envian cuando usas el boton '[OK] Listo' en un pedido.\n"
        "El mensaje incluye nombre del cliente, producto y hora de entrega.")

    # 11. META / INSTAGRAM
    pdf.seccion("11. Configuracion de Meta / Instagram")
    pdf.p("El modulo nexus_meta.py permite interactuar con la API de Meta para Instagram y WhatsApp Business.")
    pdf.sub("Requisitos previos")
    pdf.li("Cuenta de Meta Business verificada")
    pdf.li("Aplicacion creada en developers.facebook.com")
    pdf.li("Token de acceso permanente generado")
    pdf.sub("Variables necesarias en .env")
    for v in [
        "META_ACCESS_TOKEN=tu_token_de_acceso",
        "META_PHONE_ID=id_numero_whatsapp_business",
        "META_IG_USER_ID=id_cuenta_instagram",
    ]:
        pdf.cmd(v)

    # 12. MANTENIMIENTO Y LOGS
    pdf.add_page()
    pdf.seccion("12. Mantenimiento y logs")
    pdf.sub("Archivos de log")
    pdf.p("Los logs se guardan en C:\\nexus\\logs\\ con formato nexus_log_YYYY-MM.txt (un archivo por mes).")
    pdf.sub("Monitoreo de recursos")
    pdf.tabla(
        ["Recurso", "Normal",   "Alerta"],
        [
            ["CPU",     "< 30%",    "> 80% constante"],
            ["RAM",     "< 50%",    "> 85%"],
            ["Disco",   "< 70%",    "> 90%"],
        ],
        ws=[40, 50, 85]
    )
    pdf.sub("Tareas de mantenimiento mensual")
    for t in [
        "Revisar logs del mes y verificar errores recurrentes",
        "Ejecutar nexus_backup.py y guardar copia en almacenamiento externo",
        "Verificar que Supabase sigue sincronizando correctamente",
        "Revisar stock bajo y reponer materiales",
        "Actualizar dependencias: pip install -r requirements.txt --upgrade",
        "Limpiar pedidos entregados mas antiguos de 6 meses",
    ]:
        pdf.li(t)

    # 13. SOLUCION DE PROBLEMAS
    pdf.add_page()
    pdf.seccion("13. Solucion de problemas")
    problemas = [
        ("El servidor no inicia / Puerto en uso",
         "Otro proceso usa el puerto 8000.\n"
         "  netstat -ano | findstr :8000\n"
         "  taskkill /PID <numero> /F\n"
         "Luego vuelve a iniciar NEXUS."),
        ("ModuleNotFoundError al iniciar",
         "Falta una dependencia.\n"
         "  pip install -r requirements.txt\n"
         "  pip install <nombre_modulo>"),
        ("No conecta a Supabase",
         "Verifica el archivo .env: SUPABASE_URL y SUPABASE_KEY.\n"
         "Comprueba la conexion a internet.\n"
         "Ejecuta: python check_supabase.py"),
        ("El panel web carga en blanco",
         "El servidor esta iniciando. Espera 5 seg y recarga el navegador.\n"
         "Si persiste, revisa la terminal donde corre NEXUS."),
        ("Las notificaciones Telegram no llegan",
         "Verifica TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID en .env.\n"
         "Asegurate de haber iniciado conversacion con el bot primero."),
        ("La base de datos esta corrupta",
         "Restaura desde respaldo: copia nexus_v2.db del respaldo\n"
         "a C:\\nexus\\ reemplazando el archivo actual."),
    ]
    for titulo, sol in problemas:
        pdf.sub(f"[!] {safe(titulo)}")
        pdf.set_left()
        pdf.set_fill_color(18, 18, 22)
        pdf.set_text_color(160, 180, 200)
        pdf.set_font("Courier", "", 9)
        pdf.multi_cell(pdf.W(), 6, safe(sol), fill=True)
        pdf.set_left()
        pdf.ln(4)

    out = os.path.join(OUT_DIR, "NEXUS_Manual_Administrador.pdf")
    pdf.output(out)
    print(f"[OK] Manual de Administrador  ->  {out}")
    return out


# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Generando manuales NEXUS...")
    u = manual_usuario()
    a = manual_admin()
    print(f"\nListo. PDFs en: {OUT_DIR}")
    print(f"  - {os.path.basename(u)}")
    print(f"  - {os.path.basename(a)}")
