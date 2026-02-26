"""
nexus_motors.py — Lanzador de aplicaciones externas para NEXUS Estudio
CorelDRAW, Silhouette Studio, Aspire, LightBurn, Adobe Photoshop
"""
import os, subprocess, glob as _glob

# ── Rutas conocidas ─────────────────────────────────────────────────────────
_RUTAS_CONOCIDAS = {
    "corel": [
        r"C:\Program Files\Corel\CorelDRAW Graphics Suite\26\Programs64\CorelDRW.exe",
        r"C:\Program Files\Corel\CorelDRAW Graphics Suite\25\Programs64\CorelDRW.exe",
        r"C:\Program Files\Corel\CorelDRAW Graphics Suite 2021\Programs64\CorelDRW.exe",
    ],
    "silhouette": [
        r"C:\Program Files\Silhouette America\Silhouette Studio\Silhouette Studio.exe",
        r"C:\Program Files (x86)\Silhouette America\Silhouette Studio\Silhouette Studio.exe",
    ],
    "aspire": [
        r"C:\Users\anuar\Desktop\SOFTWARE_RECUPERADO\Aspire 10.5\x64\Aspire.exe",
        r"C:\Program Files\Vectric\Aspire 10\Aspire.exe",
        r"C:\Program Files\Vectric\Aspire 11\Aspire.exe",
        r"C:\Program Files (x86)\Vectric\Aspire 10\Aspire.exe",
        r"C:\Program Files (x86)\Vectric\Aspire 11\Aspire.exe",
    ],
    "lightburn": [
        r"C:\Program Files\LightBurn\LightBurn.exe",
        r"C:\Program Files (x86)\LightBurn\LightBurn.exe",
        r"C:\LightBurn\LightBurn.exe",
    ],
    "photoshop": [
        r"C:\Program Files\Adobe\Adobe Photoshop 2024\Photoshop.exe",
        r"C:\Program Files\Adobe\Adobe Photoshop 2023\Photoshop.exe",
        r"C:\Program Files\Adobe\Adobe Photoshop 2022\Photoshop.exe",
        r"C:\Program Files\Adobe\Adobe Photoshop 2025\Photoshop.exe",
    ],
    "rdworks": [
        r"C:\Program Files\RDWorks\RDWorks.exe",
        r"C:\Program Files (x86)\RDWorks\RDWorks.exe",
        r"C:\RDWorks8\RDWorks.exe",
    ],
}

_NOMBRES = {
    "corel":      "CorelDRAW",
    "silhouette": "Silhouette Studio",
    "aspire":     "Aspire",
    "lightburn":  "LightBurn",
    "photoshop":  "Photoshop",
    "rdworks":    "RDWorks",
}

_ICONOS = {
    "corel":      "🎨",
    "silhouette": "✂️",
    "aspire":     "⚙️",
    "lightburn":  "🔥",
    "photoshop":  "📸",
    "rdworks":    "🔴",
}

_FORMATOS = {
    "corel":      ["cdr","ai","eps","svg","dxf","pdf","jpg","png"],
    "silhouette": ["svg","studio","studio3","dxf","pdf","png"],
    "aspire":     ["dxf","svg","crv","v3d","eps"],
    "lightburn":  ["lbrn","dxf","svg","ai","pdf","png","jpg"],
    "photoshop":  ["psd","jpg","jpeg","png","tiff","bmp","webp","pdf"],
    "rdworks":    ["rd","dxf","plt","bmp","jpg","png"],
}


def _encontrar_exe(clave: str) -> str | None:
    """Busca el ejecutable de una app por lista de rutas conocidas."""
    for ruta in _RUTAS_CONOCIDAS.get(clave, []):
        if os.path.isfile(ruta):
            return ruta
    return None


def apps_disponibles() -> list[dict]:
    """
    Devuelve lista de apps instaladas y detectadas.
    [{id, nombre, icono, disponible, ruta, formatos}]
    """
    resultado = []
    for clave in _RUTAS_CONOCIDAS:
        ruta = _encontrar_exe(clave)
        resultado.append({
            "id":         clave,
            "nombre":     _NOMBRES[clave],
            "icono":      _ICONOS[clave],
            "disponible": ruta is not None,
            "ruta":       ruta or "",
            "formatos":   _FORMATOS[clave],
        })
    return resultado


def abrir_en_app(clave: str, archivo: str | None = None) -> dict:
    """
    Abre una aplicación. Si se especifica 'archivo', lo pasa como argumento.
    Retorna {ok, mensaje}
    """
    ruta = _encontrar_exe(clave)
    if not ruta:
        return {"ok": False, "mensaje": f"No se encontró {_NOMBRES.get(clave, clave)} instalado"}

    try:
        if archivo and os.path.isfile(archivo):
            subprocess.Popen([ruta, archivo],
                             creationflags=subprocess.CREATE_NO_WINDOW
                             if os.name == "nt" else 0)
            return {"ok": True, "mensaje": f"Abriendo {_NOMBRES[clave]} con {os.path.basename(archivo)}"}
        else:
            subprocess.Popen([ruta],
                             creationflags=subprocess.CREATE_NO_WINDOW
                             if os.name == "nt" else 0)
            return {"ok": True, "mensaje": f"Abriendo {_NOMBRES[clave]}"}
    except Exception as e:
        return {"ok": False, "mensaje": f"Error al abrir {_NOMBRES[clave]}: {e}"}


def abrir_carpeta_out() -> dict:
    """Abre la carpeta de salida en el Explorador de Windows."""
    carpeta = os.path.join(os.path.dirname(__file__), "out")
    os.makedirs(carpeta, exist_ok=True)
    try:
        subprocess.Popen(["explorer", carpeta])
        return {"ok": True, "mensaje": f"Carpeta abierta: {carpeta}"}
    except Exception as e:
        return {"ok": False, "mensaje": str(e)}


# ── CORELDRAW MACRO (VBA / COM) ───────────────────────────────────────────────
# Directorio donde CorelDRAW busca macros GMS
_COREL_MACROS_DIR = os.path.join(
    os.environ.get("APPDATA", ""),
    "Corel", "CorelDRAW Graphics Suite", "26", "GMS"
)

# Macros predefinidas que NEXUS puede invocar
_MACROS_PREDEFINIDAS = {
    "importar_archivo": {
        "desc": "Importa un archivo al documento activo de CorelDRAW",
        "vba": """
Sub ImportarArchivo(sRuta As String)
    Dim app As CorelDRAW.Application
    Set app = CorelDRAW.Application
    If app.Documents.Count = 0 Then app.Documents.Add
    app.ActiveDocument.ImportFile(sRuta)
End Sub
""",
    },
    "exportar_svg": {
        "desc": "Exporta el documento activo a SVG",
        "vba": """
Sub ExportarSVG(sRuta As String)
    Dim app As CorelDRAW.Application
    Set app = CorelDRAW.Application
    If app.Documents.Count = 0 Then Exit Sub
    Dim ef As CorelDRAW.ExportFilter
    Set ef = app.ActiveDocument.ExportEx(sRuta, cdrSVG)
    ef.Finish
End Sub
""",
    },
    "exportar_dxf": {
        "desc": "Exporta el documento activo a DXF",
        "vba": """
Sub ExportarDXF(sRuta As String)
    Dim app As CorelDRAW.Application
    Set app = CorelDRAW.Application
    If app.Documents.Count = 0 Then Exit Sub
    Dim ef As CorelDRAW.ExportFilter
    Set ef = app.ActiveDocument.ExportEx(sRuta, cdrDXF)
    ef.Finish
End Sub
""",
    },
    "ajustar_colores_laser": {
        "desc": "Convierte todos los objetos a contorno negro 0.001pt (listo para laser)",
        "vba": """
Sub AjustarColoresLaser()
    Dim app As CorelDRAW.Application
    Set app = CorelDRAW.Application
    If app.Documents.Count = 0 Then Exit Sub
    Dim doc As CorelDRAW.Document
    Set doc = app.ActiveDocument
    Dim sh As CorelDRAW.Shape
    For Each sh In doc.ActiveLayer.Shapes
        sh.Outline.Color.RGBAssign 0, 0, 0
        sh.Outline.SetProperties 0.001, CreateObject("CorelDRAW.LineStyle")
        sh.Fill.Type = cdrNoFill
    Next sh
End Sub
""",
    },
    "centrar_pagina": {
        "desc": "Centra todos los objetos en la pagina",
        "vba": """
Sub CentrarEnPagina()
    Dim app As CorelDRAW.Application
    Set app = CorelDRAW.Application
    If app.Documents.Count = 0 Then Exit Sub
    app.ActiveDocument.ActiveLayer.Shapes.All
    app.ActiveDocument.ActiveSelection.AlignAndDistribute _
        cdrAlignCenterPage, cdrAlignCenterPage, False, False
End Sub
""",
    },
}


def escribir_macro_corel(nombre: str, codigo_vba: str) -> dict:
    """
    Escribe un macro VBA en el directorio GMS de CorelDRAW.
    El archivo se guarda como <nombre>.gms y estara disponible en CorelDRAW > Herramientas > Macros.
    """
    gms_dir = _COREL_MACROS_DIR
    os.makedirs(gms_dir, exist_ok=True)

    # Cabecera de modulo VBA
    header = f'Attribute VB_Name = "NEXUS_{nombre}"\n'
    contenido = header + codigo_vba.strip() + "\n"

    ruta_gms = os.path.join(gms_dir, f"NEXUS_{nombre}.gms")
    try:
        with open(ruta_gms, "w", encoding="utf-8") as f:
            f.write(contenido)
        return {"ok": True, "ruta": ruta_gms, "mensaje": f"Macro '{nombre}' guardado en {ruta_gms}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def ejecutar_macro_corel_com(nombre_modulo: str, nombre_sub: str, *args) -> dict:
    """
    Ejecuta un macro en CorelDRAW via COM (win32com).
    CorelDRAW debe estar abierto.
    """
    try:
        import win32com.client as com
        corel = com.GetActiveObject("CorelDRAW.Application.26")
        macro_mgr = corel.MacroManager
        # Formato: "NEXUS_nombre.nombre_sub"
        full_name = f"NEXUS_{nombre_modulo}.{nombre_sub}"
        if args:
            macro_mgr.Run(full_name, list(args))
        else:
            macro_mgr.Run(full_name)
        return {"ok": True, "mensaje": f"Macro {full_name} ejecutado"}
    except ImportError:
        return {"ok": False, "error": "pywin32 no instalado. Ejecuta: pip install pywin32"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def instalar_macros_nexus() -> dict:
    """
    Escribe todos los macros predefinidos de NEXUS en el directorio GMS de CorelDRAW.
    Llama esto una vez para que queden disponibles en CorelDRAW.
    """
    resultados = []
    for nombre, info in _MACROS_PREDEFINIDAS.items():
        r = escribir_macro_corel(nombre, info["vba"])
        resultados.append({"nombre": nombre, "ok": r["ok"], "ruta": r.get("ruta",""), "error": r.get("error","")})
    ok_count = sum(1 for r in resultados if r["ok"])
    return {
        "ok": True,
        "instalados": ok_count,
        "total": len(resultados),
        "detalle": resultados,
        "directorio": _COREL_MACROS_DIR,
    }


def macros_disponibles() -> list[dict]:
    """Lista los macros predefinidos de NEXUS para CorelDRAW."""
    return [
        {"nombre": k, "desc": v["desc"]}
        for k, v in _MACROS_PREDEFINIDAS.items()
    ]


if __name__ == "__main__":
    for a in apps_disponibles():
        estado = "OK" if a["disponible"] else "no encontrado"
        print(f"{a['icono']} {a['nombre']:20s}  {estado}  {a['ruta']}")
    print("\nInstalando macros NEXUS para CorelDRAW...")
    r = instalar_macros_nexus()
    print(f"  {r['instalados']}/{r['total']} macros instalados en: {r['directorio']}")
