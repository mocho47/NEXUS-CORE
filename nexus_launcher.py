import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import sys
import webbrowser
import threading
import time
import psutil

# Configuración de Colores
COLOR_BG = "#121212"
COLOR_FG = "#00ff00"
COLOR_BTN = "#1e1e1e"

class NexusLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("NEXUS CONTROL CENTER")
        self.root.geometry("400x500")
        self.root.configure(bg=COLOR_BG)
        self.root.resizable(False, False)

        # Variables de Proceso
        self.proc_core = None
        self.proc_server = None

        # --- UI ELEMENTS ---
        lbl_title = tk.Label(root, text="N E X U S", font=("Segoe UI", 24, "bold"), bg=COLOR_BG, fg=COLOR_FG)
        lbl_title.pack(pady=20)

        self.status_lbl = tk.Label(root, text="Sistema: DETENIDO", font=("Segoe UI", 10), bg=COLOR_BG, fg="#666")
        self.status_lbl.pack(pady=5)

        # Botón GIGANTE de Inicio
        self.btn_start = tk.Button(root, text="▶ INICIAR SISTEMA", font=("Segoe UI", 14, "bold"), 
                                   bg=COLOR_BTN, fg=COLOR_FG, command=self.toggle_system, height=2, width=25, bd=0)
        self.btn_start.pack(pady=20)

        # Botones de Herramientas
        frame_tools = tk.Frame(root, bg=COLOR_BG)
        frame_tools.pack(pady=10)

        self.create_btn(frame_tools, "📱 Abrir Móvil (Local)", self.open_mobile_local)
        self.create_btn(frame_tools, "🌐 Abrir Móvil (QR)", self.show_qr)
        self.create_btn(frame_tools, "⚙ Configuración", self.open_config)
        self.create_btn(frame_tools, "📂 Carpeta Nexus", self.open_folder)

        # Footer
        lbl_ver = tk.Label(root, text="V3.0 Stable | Powered by Trae AI", font=("Segoe UI", 8), bg=COLOR_BG, fg="#444")
        lbl_ver.pack(side="bottom", pady=10)

        # Check inicial
        self.check_status()

    def create_btn(self, parent, text, cmd):
        btn = tk.Button(parent, text=text, font=("Segoe UI", 10), bg="#222", fg="white", 
                        command=cmd, width=30, bd=0, pady=5)
        btn.pack(pady=5)
        
        # Hover effect
        btn.bind("<Enter>", lambda e: btn.config(bg="#333"))
        btn.bind("<Leave>", lambda e: btn.config(bg="#222"))

    def toggle_system(self):
        if self.proc_core or self.proc_server:
            self.stop_system()
        else:
            self.start_system()

    def start_system(self):
        self.status_lbl.config(text="Iniciando motores...", fg="yellow")
        self.root.update()

        try:
            # RUTAS ABSOLUTAS (CRÍTICO)
            base_dir = os.path.dirname(os.path.abspath(__file__))
            server_path = os.path.join(base_dir, "nexus_server.py")
            core_path = os.path.join(base_dir, "nexus_core.py")

            # Entorno por defecto: fluidez máxima (online) sin romper overrides del usuario.
            env = os.environ.copy()
            env.setdefault("NEXUS_PRIVACY_MODE", "online")
            env.setdefault("NEXUS_DISABLE_CLOUD", "0")

            if not os.path.exists(server_path):
                raise FileNotFoundError(f"No encuentro: {server_path}")

            # 1. Iniciar Servidor Web
            # Usamos CREATE_NO_WINDOW para que no moleste, pero capturamos stderr si falla
            self.proc_server = subprocess.Popen(
                [sys.executable, server_path],
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            
            # 2. Iniciar Core (Voz)
            # Este SI debe tener consola propia para ver logs de voz
            self.proc_core = subprocess.Popen(
                [sys.executable, core_path],
                env=env,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )

            # 3. Iniciar scheduler + telegram bot en background (dentro del proceso launcher)
            try:
                import dotenv as _dotenv
                _dotenv.load_dotenv(os.path.join(base_dir, ".env"))
            except Exception:
                pass
            try:
                import nexus_scheduler
                nexus_scheduler.start()
            except Exception:
                pass
            try:
                from nexus_telegram import bot as _tbot
                _tbot.start()
            except Exception:
                pass

            self.status_lbl.config(text="Sistema: EN LÍNEA 🟢", fg=COLOR_FG)
            self.btn_start.config(text="⏹ DETENER SISTEMA", bg="#330000", fg="#ff4444")
            
        except Exception as e:
            messagebox.showerror("Error Crítico", f"Fallo al iniciar:\n{str(e)}")
            self.stop_system()

    def stop_system(self):
        # Matar procesos
        if self.proc_server: self.proc_server.terminate()
        if self.proc_core: self.proc_core.terminate()
        
        # Asegurar muerte por nombre (limpieza profunda)
        os.system("taskkill /f /im python.exe /fi \"WINDOWTITLE eq Nexus*\" >nul 2>&1")
        
        self.proc_core = None
        self.proc_server = None
        self.status_lbl.config(text="Sistema: DETENIDO", fg="#666")
        self.btn_start.config(text="▶ INICIAR SISTEMA", bg=COLOR_BTN, fg=COLOR_FG)

    def check_status(self):
        # Verificar si siguen vivos
        if self.proc_core and self.proc_core.poll() is not None:
            self.stop_system()
        self.root.after(2000, self.check_status)

    def open_mobile_local(self):
        webbrowser.open("http://localhost:8000")

    def show_qr(self):
        ip = self.get_ip()
        webbrowser.open(f"http://localhost:8000/qr")

    def open_config(self):
        # Abrir archivo JSON por ahora, luego haremos ventana gráfica
        os.startfile(os.path.join(os.getcwd(), "CONFIG"))

    def open_folder(self):
        os.startfile(os.getcwd())

    def get_ip(self):
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

if __name__ == "__main__":
    root = tk.Tk()
    app = NexusLauncher(root)
    root.mainloop()
