"""
nexus_legal.py — Marco legal de NEXUS: privacidad, deslinde y términos de uso.

Cumplimiento:
  - LFPDPPP (Ley Federal de Protección de Datos Personales en Posesión
    de los Particulares) — México, 2010 y reformas vigentes.
  - Principios ARCO (Acceso, Rectificación, Cancelación, Oposición).
  - NOM-151-SCFI (conservación de mensajes de datos y digitalización).

NEXUS es un software de gestión LOCAL. Los datos permanecen en el
equipo del usuario, no se transfieren a terceros sin autorización
explícita del titular.

DESLINDE:
  - El acceso al equipo es otorgado voluntaria y explícitamente por
    el usuario titular. Dicho acceso no compromete al desarrollador.
  - El uso de tonos binaurales, contenidos de audio y experiencias
    visuales es responsabilidad exclusiva del usuario final.
  - El software es una herramienta; el uso indebido es responsabilidad
    del operador, no del fabricante (Art. 27 LFPDPPP, analogía).
"""

import os
import json
import datetime

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "CONFIG")

# ── Versión vigente del aviso ──────────────────────────────────────────────────
VERSION_AVISO = "2026-02-24"
VERSION_TERMINOS = "2026-02-24"

# ── Aviso de Privacidad (Art. 15-17 LFPDPPP) ──────────────────────────────────

AVISO_PRIVACIDAD = """
AVISO DE PRIVACIDAD SIMPLIFICADO — NEXUS Business Suite
Versión: 2026-02-24

RESPONSABLE DEL TRATAMIENTO
El presente aviso es emitido por el propietario o licenciatario de
este software NEXUS, quien actúa como responsable del tratamiento de
los datos personales ingresados en el sistema.

DATOS PERSONALES QUE SE RECABAN
Nombre, teléfono, correo electrónico y notas de clientes; información
de pedidos, inventario y actividad comercial del negocio. Estos datos
se ingresan voluntariamente por el usuario operador del software.

FINALIDADES DEL TRATAMIENTO
• Gestión operativa del negocio: pedidos, clientes, inventario.
• Generación de reportes, cotizaciones y comunicaciones internas.
• Mejora continua del servicio mediante análisis estadístico local.

TRANSFERENCIA DE DATOS
Los datos NO se transfieren a terceros sin consentimiento explícito,
salvo obligación legal. La sincronización opcional con servicios
externos (p. ej. Supabase) requiere activación manual del usuario y
se rige por los términos de privacidad del proveedor externo.

ALMACENAMIENTO LOCAL
Todos los datos se almacenan en el equipo del usuario (base de datos
SQLite local). El desarrollador de NEXUS no tiene acceso remoto a
dichos datos, salvo que el usuario lo habilite explícitamente.

DERECHOS ARCO
El titular de los datos puede ejercer sus derechos de Acceso,
Rectificación, Cancelación y Oposición directamente desde el panel
de administración de NEXUS o eliminando los registros correspondientes.

CONTACTO
Para dudas sobre este aviso, contacte al responsable del tratamiento
(propietario de la licencia NEXUS en su organización).

LFPDPPP — Diario Oficial de la Federación, 5 de julio de 2010.
"""

# ── Términos y Condiciones de Uso ─────────────────────────────────────────────

TERMINOS_USO = """
TÉRMINOS Y CONDICIONES DE USO — NEXUS Business Suite
Versión: 2026-02-24

1. ACEPTACIÓN
Al instalar, activar o utilizar NEXUS, el usuario acepta íntegramente
estos términos. Si no está de acuerdo, debe desinstalar el software.

2. LICENCIA DE USO
NEXUS se licencia, no se vende. La licencia es personal, intransferible
y vinculada al hardware del equipo donde se activa (fingerprint único).
Está prohibida la copia, distribución o modificación sin autorización.

3. ACCESO AL EQUIPO DEL USUARIO
NEXUS opera localmente en el equipo del usuario. Las funcionalidades
que requieren acceso al sistema de archivos, red o dispositivos
conectados son habilitadas EXCLUSIVAMENTE por el usuario de forma
voluntaria y explícita. El desarrollador no almacena ni tiene acceso
a información del equipo del usuario. El usuario es el único responsable
de los permisos que otorgue al software.

4. CONTENIDO DE AUDIO — TONOS BINAURALES Y EXPERIENCIAS AUDITIVAS
NEXUS incluye contenido de audio generado con frecuencias binaurales
y de estimulación sonora. Este contenido es de uso OPCIONAL y tiene
fines ambientales, de productividad y bienestar general.

   a) Los tonos binaurales son una técnica reconocida de estimulación
      auditiva. Su uso no garantiza resultados específicos.
   b) EL USUARIO ES EL ÚNICO RESPONSABLE del uso de dichos contenidos.
      Se recomienda no utilizarlos con audífonos a volumen elevado,
      durante la conducción de vehículos o maquinaria, ni en personas
      con epilepsia, trastornos auditivos u otras condiciones sensibles.
   c) El desarrollador de NEXUS, sus colaboradores y distribuidores
      quedan expresamente DESLINDADOS de cualquier efecto, daño o
      perjuicio derivado del uso de estos contenidos.
   d) Al activar cualquier audio o experiencia de la galería, el usuario
      confirma haber leído y aceptado este deslinde.

5. CONTENIDO VISUAL — EXPERIENCIAS GRÁFICAS AMBIENTALES
Las experiencias visuales (Canvas/WebGL) son de baja opacidad y uso
estético-ambiental. El usuario puede desactivarlas en cualquier momento.
El desarrollador no se responsabiliza por molestias visuales derivadas
del uso prolongado.

6. MENSAJES PERSUASIVOS Y CONTENIDO SUBLIMINAL
NEXUS incluye mensajes motivacionales y de contexto comercial
reproducidos a volumen reducido. Estos mensajes son éticos, positivos
y están orientados al desarrollo del negocio y bienestar del usuario.
No contienen sugestiones ilegales, engañosas ni invasivas. Su uso es
opcional y desactivable en todo momento.

7. LIMITACIÓN DE RESPONSABILIDAD
NEXUS se provee "tal como es" (as-is). El desarrollador no garantiza
su funcionamiento ininterrumpido ni libre de errores. En ningún caso
el desarrollador será responsable por daños directos, indirectos,
incidentales o consecuentes derivados del uso del software, incluyendo
pérdida de datos, interrupción del negocio u otros perjuicios, aun
cuando haya sido informado de la posibilidad de tales daños.

8. LEY APLICABLE Y JURISDICCIÓN
Estos términos se rigen por las leyes de los Estados Unidos Mexicanos.
Cualquier controversia se somete a la jurisdicción de los tribunales
competentes de la Ciudad de México, con renuncia expresa a cualquier
otro fuero.

9. MODIFICACIONES
El desarrollador puede actualizar estos términos. La versión vigente
siempre estará disponible en el panel de NEXUS (/legal).

10. CONTACTO
Para reportar mal uso, vulnerabilidades de seguridad o ejercer derechos
de privacidad, contacte al administrador de su licencia NEXUS.
"""


# ── Funciones de utilidad ─────────────────────────────────────────────────────

def registrar_aceptacion(usuario: str = "operador") -> dict:
    """
    Registra en CONFIG/legal_acepto.json que el usuario aceptó
    el aviso de privacidad y los términos de uso.
    Retorna el registro generado.
    """
    os.makedirs(CONFIG_DIR, exist_ok=True)
    path = os.path.join(CONFIG_DIR, "legal_acepto.json")
    registro = {
        "aceptado":         True,
        "usuario":          usuario,
        "fecha":            datetime.datetime.now().isoformat(),
        "version_aviso":    VERSION_AVISO,
        "version_terminos": VERSION_TERMINOS,
        "ip_local":         _get_local_ip(),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(registro, f, ensure_ascii=False, indent=2)
    return registro


def verificar_aceptacion() -> dict:
    """
    Verifica si el usuario ya aceptó los términos vigentes.
    Retorna dict con 'aceptado' (bool) y detalles.
    """
    path = os.path.join(CONFIG_DIR, "legal_acepto.json")
    if not os.path.exists(path):
        return {"aceptado": False, "motivo": "Sin registro previo"}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not data.get("aceptado"):
            return {"aceptado": False, "motivo": "Aceptación revocada"}
        # Verificar que aceptó la versión actual
        if data.get("version_terminos") != VERSION_TERMINOS:
            return {
                "aceptado":     False,
                "motivo":       "Versión de términos desactualizada",
                "version_ok":   VERSION_TERMINOS,
                "version_tiene": data.get("version_terminos"),
            }
        return {"aceptado": True, **data}
    except Exception as e:
        return {"aceptado": False, "motivo": f"Error leyendo registro: {e}"}


def get_aviso() -> str:
    """Retorna el texto completo del Aviso de Privacidad."""
    return AVISO_PRIVACIDAD.strip()


def get_terminos() -> str:
    """Retorna el texto completo de los Términos y Condiciones."""
    return TERMINOS_USO.strip()


def _get_local_ip() -> str:
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "estado"

    if cmd == "aviso":
        print(get_aviso())
    elif cmd == "terminos":
        print(get_terminos())
    elif cmd == "aceptar":
        r = registrar_aceptacion()
        print(f"[OK] Aceptación registrada: {r['fecha']}")
    elif cmd == "estado":
        r = verificar_aceptacion()
        print(f"[LEGAL] Aceptado: {r['aceptado']}")
        if not r["aceptado"]:
            print(f"       Motivo: {r.get('motivo','?')}")
        else:
            print(f"       Fecha:  {r.get('fecha','?')}")
            print(f"       Versión: {r.get('version_terminos','?')}")
    else:
        print("Uso: python nexus_legal.py [aviso|terminos|aceptar|estado]")
