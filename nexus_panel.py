"""
nexus_panel.py — Panel de control visual de NEXUS (Tkinter).
Muestra logs en tiempo real, estado del sistema y controles básicos.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import os
import sys
import subprocess

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
WEB_CMD_FILE = os.path.join(BASE_DIR, "web_command.txt")
LOG_DIR      = os.path.join(BASE_DIR, "logs")

class NexusPanel:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("NEXUS CONTROL CENTER")
        self.root.geometry("460x580")
        self.root.configure(bg="#0a0a0a")
        self.listening = False
        self._build_ui()
        self._start_log_refresh()

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="#0a0a0a", foreground="#00ff88", font=("Consolas", 10))
        style.configure("Green.TButton", background="#00ff88", foreground="#000", font=("Consolas", 10, "bold"))
        style.configure("Red.TButton",   background="#333",    foreground="#ff4444", font=("Consolas", 10, "bold"))

        # Header
        hdr = tk.Frame(self.root, bg="#000", pady=8)
        hdr.pack(fill="x")
        self.lbl_status = tk.Label(hdr, text="⚡ NEXUS ONLINE", bg="#000", fg="#00ff88", font=("Consolas", 14, "bold"))
        self.lbl_status.pack()
        self.lbl_sys = tk.Label(hdr, text="CPU: — | RAM: —", bg="#000", fg="#555", font=("Consolas", 9))
        self.lbl_sys.pack()

        # Consola de logs
        frm = tk.Frame(self.root, bg="#0a0a0a", padx=8, pady=4)
        frm.pack(fill="both", expand=True)
        tk.Label(frm, text="LOG EN VIVO", bg="#0a0a0a", fg="#333", font=("Consolas", 8)).pack(anchor="w")
        self.txt = tk.Text(frm, height=18, bg="#050505", fg="#00ff88", font=("Consolas", 8),
                           state="disabled", insertbackground="#00ff88", relief="flat", bd=1)
        sb = tk.Scrollbar(frm, command=self.txt.yview, bg="#111")
        self.txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.txt.pack(fill="both", expand=True)

        # Botones
        btn_frm = tk.Frame(self.root, bg="#0a0a0a", pady=8, padx=8)
        btn_frm.pack(fill="x")

        self.btn_voice = tk.Button(btn_frm, text="🎤  ESCUCHAR",
                                   bg="#00ff8822", fg="#00ff88", relief="flat",
                                   font=("Consolas", 10, "bold"), pady=8,
                                   command=self.toggle_listen)
        self.btn_voice.pack(side="left", expand=True, fill="x", padx=(0, 4))

        tk.Button(btn_frm, text="🌐  WEB",
                  bg="#111", fg="#888", relief="flat",
                  font=("Consolas", 10), pady=8,
                  command=self.open_web).pack(side="left", expand=True, fill="x", padx=4)

        tk.Button(btn_frm, text="🛑  APAGAR",
                  bg="#ff444411", fg="#ff4444", relief="flat",
                  font=("Consolas", 10, "bold"), pady=8,
                  command=self.stop_system).pack(side="right", expand=True, fill="x", padx=(4, 0))

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def log(self, msg: str):
        self.txt.configure(state="normal")
        ts = time.strftime("[%H:%M:%S] ")
        self.txt.insert("end", ts + msg + "\n")
        self.txt.see("end")
        self.txt.configure(state="disabled")

    def toggle_listen(self):
        self.listening = not self.listening
        if self.listening:
            self.btn_voice.configure(text="🔴  ESCUCHANDO", bg="#ff000022", fg="#ff4444")
            self.log("Escucha manual activada...")
            try:
                with open(WEB_CMD_FILE, "w", encoding="utf-8") as f:
                    f.write("escuchar")
            except Exception as e:
                self.log(f"Error al activar escucha: {e}")
        else:
            self.btn_voice.configure(text="🎤  ESCUCHAR", bg="#00ff8822", fg="#00ff88")
            self.log("Escucha manual desactivada.")
            try:
                with open(WEB_CMD_FILE, "w", encoding="utf-8") as f:
                    f.write("")
            except: pass

    def open_web(self):
        import webbrowser
        webbrowser.open("http://localhost:8000/dashboard")

    def stop_system(self):
        if messagebox.askyesno("Confirmar", "¿Apagar NEXUS completamente?"):
            self.log("Apagando NEXUS...")
            self.root.destroy()
            sys.exit(0)

    def on_close(self):
        self.root.destroy()

    def _start_log_refresh(self):
        """Refresca la consola con las últimas líneas del log cada 3 segundos."""
        def _loop():
            last_size = 0
            while True:
                try:
                    import glob, datetime
                    pattern = os.path.join(LOG_DIR, f"nexus_log_{datetime.datetime.now().strftime('%Y-%m')}.txt")
                    files = glob.glob(pattern)
                    if files:
                        size = os.path.getsize(files[0])
                        if size != last_size:
                            last_size = size
                            with open(files[0], "r", encoding="utf-8", errors="ignore") as f:
                                lines = f.readlines()[-5:]
                            for line in lines:
                                self.log(line.strip())
                    # Actualizar CPU/RAM
                    try:
                        import psutil
                        cpu = psutil.cpu_percent(interval=None)
                        ram = psutil.virtual_memory().percent
                        self.root.after(0, lambda c=cpu, r=ram:
                            self.lbl_sys.configure(text=f"CPU: {c:.0f}%  |  RAM: {r:.0f}%"))
                    except: pass
                except: pass
                time.sleep(3)
        t = threading.Thread(target=_loop, daemon=True)
        t.start()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    panel = NexusPanel()
    panel.run()
