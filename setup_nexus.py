from PIL import Image, ImageDraw, ImageFont
import os
import winshell
from win32com.client import Dispatch

def create_icon():
    size = (256, 256)
    # Fondo Rojo (Solicitud Usuario)
    img = Image.new('RGB', size, color=(255, 0, 0))
    d = ImageDraw.Draw(img)
    
    # Intentar cargar fuente, sino default
    try:
        font = ImageFont.truetype("arial.ttf", 200)
    except:
        font = ImageFont.load_default()
    
    # Dibujar "N"
    d.text((60, 20), "N", fill=(255, 255, 255), font=font)
    
    icon_path = r"C:\NEXUS\nexus.ico"
    img.save(icon_path)
    print(f"Icono creado en: {icon_path}")
    return icon_path

def create_shortcut(icon_path):
    # Usar Public Desktop para que sea visible para TODOS los usuarios
    public_desktop = os.path.join(os.environ['PUBLIC'], 'Desktop')
    path = os.path.join(public_desktop, "NEXUS.lnk")
    
    target = r"C:\NEXUS\INICIAR_NEXUS.bat"
    wDir = r"C:\NEXUS"
    
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortcut(path)
    shortcut.TargetPath = target
    shortcut.WorkingDirectory = wDir
    shortcut.IconLocation = icon_path
    shortcut.save()
    print(f"Acceso directo creado en: {path}")

if __name__ == "__main__":
    try:
        icon = create_icon()
        create_shortcut(icon)
        print("Instalación de acceso directo completada.")
    except Exception as e:
        print(f"Error: {e}")
