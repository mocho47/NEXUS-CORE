import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import os
import sys
import re
import math
import shutil
import datetime
from PIL import Image, ImageOps, ImageDraw
import nexus_db # CONECTOR A NUBE

# --- CONFIGURACIÓN ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WATCH_DIR_BOXES = os.path.join(BASE_DIR, "TALLER", "CAJAS")
WATCH_DIR_ENGRAVE = os.path.join(BASE_DIR, "TALLER", "GRABADOS")
WATCH_DIR_STICKERS = os.path.join(BASE_DIR, "TALLER", "STICKERS")
WATCH_DIR_LONAS = os.path.join(BASE_DIR, "TALLER", "LONAS")
BOXES_SCRIPT = os.path.join(BASE_DIR, "TOOLS", "boxes", "boxes", "scripts", "boxes_main.py")
PYTHON_PATH_BOXES = os.path.join(BASE_DIR, "TOOLS", "boxes")
OFFLINE_MODE_FILE = os.path.join(BASE_DIR, "offline_mode.flag")

# Asegurar carpetas
os.makedirs(WATCH_DIR_BOXES, exist_ok=True)
os.makedirs(WATCH_DIR_ENGRAVE, exist_ok=True)
os.makedirs(WATCH_DIR_STICKERS, exist_ok=True)
os.makedirs(WATCH_DIR_LONAS, exist_ok=True)

class NexusWorkshopGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("NEXUS WORKSHOP - CANBUSFIX (OFFLINE CAPABLE)")
        self.root.geometry("650x850")
        self.root.configure(bg="#121212")
        
        # Check Offline Mode
        self.offline = os.path.exists(OFFLINE_MODE_FILE)
        
        # Estilos Dark Mode
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TLabel", background="#121212", foreground="#00ff00", font=("Consolas", 11))
        style.configure("TButton", background="#333", foreground="#fff", font=("Consolas", 10, "bold"))
        style.configure("TEntry", fieldbackground="#333", foreground="#fff")
        style.configure("TCombobox", fieldbackground="#333", foreground="#fff")
        style.configure("TNotebook", background="#121212", borderwidth=0)
        style.configure("TNotebook.Tab", background="#222", foreground="#888", padding=[10, 5])
        style.map("TNotebook.Tab", background=[("selected", "#005500")], foreground=[("selected", "#fff")])

        # Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set("SYSTEM: ONLINE" if not self.offline else "⚠️ SYSTEM: OFFLINE MODE (LOCAL ONLY)")
        tk.Label(self.root, textvariable=self.status_var, bg="#222", fg="#00ff00" if not self.offline else "yellow", anchor="w").pack(side="bottom", fill="x")

        # Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_boxes = tk.Frame(self.notebook, bg="#121212")
        self.tab_engrave = tk.Frame(self.notebook, bg="#121212")
        self.tab_stickers = tk.Frame(self.notebook, bg="#121212")
        self.tab_upscale = tk.Frame(self.notebook, bg="#121212")
        
        self.notebook.add(self.tab_boxes, text="📦 CAJAS")
        self.notebook.add(self.tab_engrave, text="🎨 GRABADOS")
        self.notebook.add(self.tab_stickers, text="🏷️ STICKERS")
        self.notebook.add(self.tab_upscale, text="🖼️ LONAS/UPSCALE")
        
        self.setup_boxes_tab()
        self.setup_engrave_tab()
        self.setup_stickers_tab()
        self.setup_upscale_tab()

    # ==========================================
    # MODULO 1: CAJAS (Box Generator PRO)
    # ==========================================
    def setup_boxes_tab(self):
        frame = self.tab_boxes
        
        # Mapeo Español -> Inglés
        self.box_map = {
            "Caja Cerrada (ClosedBox)": "ClosedBox",
            "Caja Flexible (FlexBox)": "FlexBox",
            "Bandeja Divisoria (TrayLayout)": "TrayLayout",
            "Caja Tipográfica (TypeTray)": "TypeTray",
            "Caja Regular (RegularBox)": "RegularBox",
            "Caja Corazón (HeartBox)": "HeartBox",
            "Caja Redonda (RoundBox)": "RoundBox",
            "Esfera (Sphere)": "Sphere",
            "Arcade (Arcade)": "Arcade",
            "Barril/Cava (Barrel)": "Barrel",
            "Cofre Tesoro (TreasureChest)": "TreasureChest",
            "Caja con Bisagra (HingeBox)": "HingeBox"
        }
        
        # Presets
        self.presets = {
            "Taza 11oz (Individual)": {"x": "85", "y": "85", "h": "100", "thickness": "3.0", "type": "ClosedBox"},
            "Taza 15oz (Individual)": {"x": "95", "y": "95", "h": "115", "thickness": "3.0", "type": "ClosedBox"},
            "Kit 2 Tazas (Orejas Fuera)": {"x": "170", "y": "85", "h": "100", "thickness": "3.0", "type": "DisplayBox"}
        }

        # UI Cajas
        tk.Label(frame, text="CONFIGURACIÓN TÉCNICA", bg="#121212", fg="#00ff00", font=("Consolas", 14, "bold")).pack(pady=10)
        
        input_frame = tk.Frame(frame, bg="#121212")
        input_frame.pack()

        # Tipo
        ttk.Label(input_frame, text="Tipo:").grid(row=0, column=0, sticky="w", pady=5)
        self.combo_box_type = ttk.Combobox(input_frame, values=list(self.box_map.keys()) + list(self.presets.keys()), state="readonly", width=30)
        self.combo_box_type.current(0)
        self.combo_box_type.grid(row=0, column=1, sticky="e", pady=5)
        self.combo_box_type.bind("<<ComboboxSelected>>", self.on_box_type_select)

        # Medidas
        self.box_entries = {}
        labels = [("Largo (X):", "x", "100"), ("Ancho (Y):", "y", "100"), ("Alto (h):", "h", "50"), ("Grosor:", "thickness", "3.0")]
        for i, (txt, key, val) in enumerate(labels, 1):
            ttk.Label(input_frame, text=txt).grid(row=i, column=0, sticky="w", pady=5)
            e = ttk.Entry(input_frame)
            e.insert(0, val)
            e.grid(row=i, column=1, sticky="e", pady=5)
            self.box_entries[key] = e

        # Materiales
        tk.Label(input_frame, text="Material:").grid(row=5, column=0, sticky="w", pady=5)
        self.combo_material = ttk.Combobox(input_frame, values=[
            "MDF 2.5mm (Económico)", 
            "Multiplay 4mm (Madera)", 
            "Acrílico Transparente 3mm", 
            "Acrílico Color 3mm", 
            "Acrílico 6mm (Grueso)"
        ], state="readonly", width=30)
        self.combo_material.current(0)
        self.combo_material.grid(row=5, column=1, sticky="e", pady=5)
        self.combo_material.bind("<<ComboboxSelected>>", self.update_material_cost)

        # Cotizador Cajas
        self.create_cost_frame(frame, "box")

        # Botón
        tk.Button(frame, text="GENERAR DXF + COTIZACIÓN", command=self.generate_box, bg="#00aa00", fg="white", font=("Arial", 12, "bold")).pack(pady=20)

    def on_box_type_select(self, event):
        sel = self.combo_box_type.get()
        if sel in self.presets:
            d = self.presets[sel]
            for k in ["x", "y", "h", "thickness"]:
                self.box_entries[k].delete(0, tk.END); self.box_entries[k].insert(0, d[k])
                
    def update_material_cost(self, event):
        mat_name = self.combo_material.get()
        cost = "110" # Default
        
        # Intentar obtener de la nube/db
        try:
            materials = nexus_db.db.get_materials() # Esto ya usa caché/nube
            # Buscar coincidencia parcial
            for m_name, m_data in materials.items():
                if m_name in mat_name or mat_name in m_name:
                    cost = str(m_data.get('cost_per_sheet', 110))
                    break
        except: pass
        
        self.cost_entries_box["material_cost"].delete(0, tk.END)
        self.cost_entries_box["material_cost"].insert(0, cost)

    def generate_sales_note(self, item, price):
        """Genera un texto listo para copiar a WhatsApp"""
        ts = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        note = (f"*COTIZACIÓN NEXUS* 📅 {ts}\n"
                f"--------------------------------\n"
                f"📦 *Producto:* {item}\n"
                f"💰 *Precio:* ${price:.2f} MXN\n"
                f"--------------------------------\n"
                f"✅ _Precio válido por 24 horas_")
        
        # Copiar al portapapeles
        self.root.clipboard_clear()
        self.root.clipboard_append(note)
        messagebox.showinfo("Nota Generada", "La nota de venta se copió al portapapeles.\n¡Pégala en WhatsApp!")

    def generate_box(self):
        sel = self.combo_box_type.get()
        box_type = self.presets[sel]["type"] if sel in self.presets else self.box_map.get(sel, "ClosedBox")
        params = {k: v.get() for k, v in self.box_entries.items()}
        
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        f_dxf = f"{box_type}_{params['x']}x{params['y']}x{params['h']}_{ts}.dxf"
        path_dxf = os.path.join(WATCH_DIR_BOXES, f_dxf)
        temp_svg = os.path.join(WATCH_DIR_BOXES, "temp.svg")

        # Generar SVG para calcular
        cmd_svg = [sys.executable, BOXES_SCRIPT, box_type, f"--x={params['x']}", f"--y={params['y']}", f"--h={params['h']}", f"--thickness={params['thickness']}", "--format=svg", f"--output={temp_svg}"]
        
        env = os.environ.copy()
        env["PYTHONPATH"] = PYTHON_PATH_BOXES + os.pathsep + env.get("PYTHONPATH", "")

        try:
            subprocess.run(cmd_svg, env=env, capture_output=True)
            len_mm = self.get_svg_length(temp_svg)
            price = self.calculate_price(len_mm, "box")
            if os.path.exists(temp_svg): os.remove(temp_svg)

            # Generar DXF Final
            cmd_dxf = [sys.executable, BOXES_SCRIPT, box_type, f"--x={params['x']}", f"--y={params['y']}", f"--h={params['h']}", f"--thickness={params['thickness']}", "--format=dxf", f"--output={path_dxf}"]
            subprocess.run(cmd_dxf, env=env, capture_output=True)
            
            # Auto-Nota
            self.generate_sales_note(f"Caja {sel} ({params['x']}x{params['y']}x{params['h']})", price)
            
            os.startfile(WATCH_DIR_BOXES)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ==========================================
    # MODULO 2: GRABADOS (Engrave Generator)
    # ==========================================
    def setup_engrave_tab(self):
        frame = self.tab_engrave
        
        tk.Label(frame, text="CONFIGURACIÓN GRABADO", bg="#121212", fg="#00ff00", font=("Consolas", 14, "bold")).pack(pady=10)
        
        # Selección Imagen
        self.img_path = tk.StringVar()
        img_frame = tk.Frame(frame, bg="#121212")
        img_frame.pack(pady=10)
        ttk.Entry(img_frame, textvariable=self.img_path, width=40).pack(side="left", padx=5)
        tk.Button(img_frame, text="📂 Cargar Imagen", command=self.load_image, bg="#444", fg="white").pack(side="left")

        # Opciones
        opts_frame = tk.Frame(frame, bg="#121212")
        opts_frame.pack(pady=10)
        
        ttk.Label(opts_frame, text="Modo:").grid(row=0, column=0, sticky="w", pady=5)
        self.engrave_mode = ttk.Combobox(opts_frame, values=["Relleno (Raster)", "Lineal (Vector)", "Invertido"], state="readonly")
        self.engrave_mode.current(0)
        self.engrave_mode.grid(row=0, column=1, pady=5)
        
        self.eng_entries = {}
        labels = [("Ancho (mm):", "width", "100"), ("Alto (mm):", "height", "100")]
        for i, (txt, key, val) in enumerate(labels, 1):
            ttk.Label(opts_frame, text=txt).grid(row=i, column=0, sticky="w", pady=5)
            e = ttk.Entry(opts_frame)
            e.insert(0, val)
            e.grid(row=i, column=1, pady=5)
            self.eng_entries[key] = e

        # Cotizador Grabado
        self.create_cost_frame(frame, "engrave")

        tk.Button(frame, text="PROCESAR GRABADO (.DXF)", command=self.process_engrave, bg="#00aa00", fg="white", font=("Arial", 12, "bold")).pack(pady=20)

    def load_image(self):
        f = filedialog.askopenfilename(filetypes=[("Imagenes", "*.jpg *.png *.bmp *.jpeg")])
        if f: self.img_path.set(f)

    def process_engrave(self):
        img = self.img_path.get()
        if not img or not os.path.exists(img):
            messagebox.showerror("Error", "Selecciona una imagen válida")
            return

        mode = self.engrave_mode.get()
        w = float(self.eng_entries["width"].get())
        h = float(self.eng_entries["height"].get())
        
        # Simulación de proceso (conversión real a DXF requeriría librerías pesadas)
        # Aquí movemos la imagen a la carpeta y calculamos precio basado en área
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"GRABADO_{mode}_{w}x{h}_{ts}.jpg" # Guardamos referencia visual
        dest = os.path.join(WATCH_DIR_ENGRAVE, fname)
        shutil.copy(img, dest)
        
        # Calculo precio (Area * densidad)
        # Estimamos tiempo basado en área para Raster
        area_cm2 = (w/10) * (h/10)
        minutes_est = area_cm2 * 0.5 # 0.5 min por cm2 aprox en raster
        
        rate = float(self.cost_entries_engrave["machine_cost"].get())
        price = minutes_est * rate * (1 + float(self.cost_entries_engrave["margin"].get())/100)
        
        messagebox.showinfo("Grabado Listo", f"Archivo en cola: {fname}\nEstimación Tiempo: {minutes_est:.1f} min\nPrecio Sugerido: ${price:.2f}")
        os.startfile(WATCH_DIR_ENGRAVE)

    # ==========================================
    # MODULO 3: STICKERS (Planillas)
    # ==========================================
    def setup_stickers_tab(self):
        frame = self.tab_stickers
        
        tk.Label(frame, text="GENERADOR DE PLANILLAS STICKERS", bg="#121212", fg="#00ff00", font=("Consolas", 14, "bold")).pack(pady=10)
        
        # Selección Imagen Sticker
        self.sticker_img_path = tk.StringVar()
        img_frame = tk.Frame(frame, bg="#121212")
        img_frame.pack(pady=10)
        ttk.Entry(img_frame, textvariable=self.sticker_img_path, width=40).pack(side="left", padx=5)
        tk.Button(img_frame, text="📂 Cargar Sticker", command=self.load_sticker_image, bg="#444", fg="white").pack(side="left")

        # Configuración Planilla
        opts_frame = tk.Frame(frame, bg="#121212")
        opts_frame.pack(pady=10)
        
        # Tipo de Material/Planilla
        ttk.Label(opts_frame, text="Material:").grid(row=0, column=0, sticky="w", pady=5)
        self.sticker_material = ttk.Combobox(opts_frame, values=[
            "Papel (30x40 cm) - Cameo",
            "Vinil (60x100 cm)",
            "Vinil Transparente/Sublimable (2x A4) - Cameo"
        ], state="readonly", width=40)
        self.sticker_material.current(0)
        self.sticker_material.grid(row=0, column=1, pady=5)

        # Opciones de Corte
        ttk.Label(opts_frame, text="Acabado:").grid(row=1, column=0, sticky="w", pady=5)
        self.sticker_cut = ttk.Combobox(opts_frame, values=["Sin Suaje (Solo Impresión)", "Con Suaje (Corte)"], state="readonly", width=40)
        self.sticker_cut.current(1)
        self.sticker_cut.grid(row=1, column=1, pady=5)

        # Cantidad de Planillas
        ttk.Label(opts_frame, text="Cantidad Planillas:").grid(row=2, column=0, sticky="w", pady=5)
        self.sticker_qty = ttk.Entry(opts_frame, width=10)
        self.sticker_qty.insert(0, "1")
        self.sticker_qty.grid(row=2, column=1, sticky="w", pady=5)

        # Precio Manual (Vinil Grande)
        ttk.Label(opts_frame, text="Precio Vinil 60x100 ($):").grid(row=3, column=0, sticky="w", pady=5)
        self.sticker_price_vinyl = ttk.Entry(opts_frame, width=10)
        self.sticker_price_vinyl.insert(0, "150.00") # Default estimado
        self.sticker_price_vinyl.grid(row=3, column=1, sticky="w", pady=5)

        tk.Button(frame, text="GENERAR PLANILLA (.DXF)", command=self.process_stickers, bg="#00aa00", fg="white", font=("Arial", 12, "bold")).pack(pady=30)

    def load_sticker_image(self):
        f = filedialog.askopenfilename(filetypes=[("Imagenes", "*.jpg *.png *.bmp *.jpeg")])
        if f: self.sticker_img_path.set(f)

    def process_stickers(self):
        img_path = self.sticker_img_path.get()
        if not img_path or not os.path.exists(img_path):
            messagebox.showerror("Error", "Selecciona una imagen válida")
            return

        material = self.sticker_material.get()
        cut_type = self.sticker_cut.get()
        qty = int(self.sticker_qty.get())
        
        # --- DIMENSIONES REALES ---
        # Papel Cameo: 33x48 cm (Tabloide Rebasado) -> Area segura ~30x40 para marcas
        # Vinil Grande: 60x100 cm
        
        if "Papel" in material or "Transparente" in material:
            # CAMEO MODE (33x48cm Reales)
            # Area util con marcas: Aprox 29x44 cm
            PAGE_W_MM = 330
            PAGE_H_MM = 480
            SAFE_MARGIN = 20 # Margen para marcas
            USABLE_W = PAGE_W_MM - (SAFE_MARGIN * 2)
            USABLE_H = PAGE_H_MM - (SAFE_MARGIN * 2)
            has_marks = True
            
            # Precios
            base_price = 75.0 if "Sin Suaje" in cut_type else 95.0
            
        elif "Vinil (60x100" in material:
            # PLOTTER GRANDE (60x100cm)
            PAGE_W_MM = 600
            PAGE_H_MM = 1000
            USABLE_W = 580
            USABLE_H = 980
            has_marks = False
            
            # Precio Manual
            try: base_price = float(self.sticker_price_vinyl.get())
            except: base_price = 0.0

        # --- GENERACIÓN DE PLANILLA (PDF SIMULADO) ---
        # Usamos PIL para crear una imagen gigante con los stickers repetidos
        try:
            sticker = Image.open(img_path)
            # Redimensionar sticker si es necesario (ej. 5x5cm = 500px a 100dpi aprox)
            # Aquí asumimos que el usuario ya sabe q pedo, o lo redimensionamos a un estándar 5cm si es gigante
            # Por ahora lo dejamos tal cual, pero calculamos cuántos caben
            
            # Convertir mm a pixels (aprox 300 DPI) -> 1 mm = 11.8 px
            DPI_SCALE = 5 # Escala baja para preview rapido, 11.8 para print
            
            page_px = (int(PAGE_W_MM * DPI_SCALE), int(PAGE_H_MM * DPI_SCALE))
            canvas = Image.new("RGB", page_px, "white")
            
            # Tamaño Sticker (leemos del archivo, asumimos 300dpi si no tiene info)
            s_w, s_h = sticker.size
            # Si es muy grande (>1000px), lo bajamos a algo manejable visualmente para el ejemplo
            # En prod real, respetaríamos DPI. Aquí forzamos que mida aprox 5cm (50mm) de ancho para test
            TARGET_STICKER_MM = 50
            scale_factor = (TARGET_STICKER_MM * DPI_SCALE) / s_w
            new_size = (int(s_w * scale_factor), int(s_h * scale_factor))
            sticker_small = sticker.resize(new_size)
            
            s_w, s_h = sticker_small.size
            
            # Grid
            cols = int(USABLE_W * DPI_SCALE / (s_w + 10)) # +10px gap
            rows = int(USABLE_H * DPI_SCALE / (s_h + 10))
            
            count = 0
            start_x = int(SAFE_MARGIN * DPI_SCALE) if has_marks else 10
            start_y = int(SAFE_MARGIN * DPI_SCALE) if has_marks else 10
            
            for r in range(rows):
                for c in range(cols):
                    x = start_x + c * (s_w + 10)
                    y = start_y + r * (s_h + 10)
                    canvas.paste(sticker_small, (x, y))
                    count += 1
            
            # Dibujar Marcas Cameo (Simuladas: Cuadros negros en esquinas)
            if has_marks:
                mark_size = int(10 * DPI_SCALE) # 1cm
                draw = ImageDraw.Draw(canvas)
                # Top Left (Square)
                draw.rectangle([SAFE_MARGIN, SAFE_MARGIN, SAFE_MARGIN+mark_size, SAFE_MARGIN+mark_size], fill="black")
                # Top Right (Corner)
                tr_x = page_px[0] - SAFE_MARGIN - mark_size
                draw.rectangle([tr_x, SAFE_MARGIN, tr_x+mark_size, SAFE_MARGIN+mark_size], fill="black")
                # Bottom Left (Corner)
                bl_y = page_px[1] - SAFE_MARGIN - mark_size
                draw.rectangle([SAFE_MARGIN, bl_y, SAFE_MARGIN+mark_size, bl_y+mark_size], fill="black")

            # Guardar PDF
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_name = f"PLANILLA_{qty}x_{'CAMEO' if has_marks else 'PLOTTER'}_{ts}.pdf"
            pdf_path = os.path.join(WATCH_DIR_STICKERS, pdf_name)
            canvas.save(pdf_path, "PDF", resolution=100.0) # Low res demo
            
            price_total = base_price * qty
            
            msg = (f"✅ Planilla Generada: {pdf_name}\n"
                   f"🖨️ Tamaño Hoja: {PAGE_W_MM/10} x {PAGE_H_MM/10} cm\n"
                   f"✂️ Marcas de Corte: {'SI (Cameo)' if has_marks else 'NO'}\n"
                   f"🏷️ Stickers por Hoja: {count}\n"
                   f"📦 Total Stickers: {count * qty}\n"
                   f"💰 PRECIO TOTAL: ${price_total:.2f}")
                   
            messagebox.showinfo("Producción Lista", msg)
            os.startfile(WATCH_DIR_STICKERS)
            
        except Exception as e:
             messagebox.showerror("Error Generando Planilla", str(e))

    # ==========================================
    # MODULO 4: LONAS / UPSCALE
    # ==========================================
    def setup_upscale_tab(self):
        frame = self.tab_upscale
        
        tk.Label(frame, text="OPTIMIZADOR DE LONAS E IMÁGENES", bg="#121212", fg="#00ff00", font=("Consolas", 14, "bold")).pack(pady=10)
        
        # Selección Imagen
        self.lona_img_path = tk.StringVar()
        img_frame = tk.Frame(frame, bg="#121212")
        img_frame.pack(pady=10)
        ttk.Entry(img_frame, textvariable=self.lona_img_path, width=40).pack(side="left", padx=5)
        tk.Button(img_frame, text="📂 Cargar Imagen", command=self.load_lona_image, bg="#444", fg="white").pack(side="left")

        # Configuración Lona
        opts_frame = tk.Frame(frame, bg="#121212")
        opts_frame.pack(pady=10)
        
        # Medidas Finales (Metros)
        ttk.Label(opts_frame, text="Ancho Final (mts):").grid(row=0, column=0, sticky="w", pady=5)
        self.lona_w = ttk.Entry(opts_frame, width=10)
        self.lona_w.insert(0, "1.0")
        self.lona_w.grid(row=0, column=1, pady=5)

        ttk.Label(opts_frame, text="Alto Final (mts):").grid(row=1, column=0, sticky="w", pady=5)
        self.lona_h = ttk.Entry(opts_frame, width=10)
        self.lona_h.insert(0, "1.0")
        self.lona_h.grid(row=1, column=1, pady=5)

        # Resolución Objetivo (DPI)
        ttk.Label(opts_frame, text="Calidad (DPI):").grid(row=2, column=0, sticky="w", pady=5)
        self.lona_dpi = ttk.Combobox(opts_frame, values=["72 DPI (Lonas Lejanas)", "100 DPI (Estándar)", "150 DPI (Alta)", "300 DPI (Foto/Sticker)"], state="readonly")
        self.lona_dpi.current(1)
        self.lona_dpi.grid(row=2, column=1, pady=5)

        tk.Button(frame, text="OPTIMIZAR Y ESCALAR", command=self.process_lona, bg="#00aa00", fg="white", font=("Arial", 12, "bold")).pack(pady=30)

        # Precio Lona
        ttk.Label(opts_frame, text="Precio por m² ($):").grid(row=3, column=0, sticky="w", pady=5)
        self.lona_price = ttk.Entry(opts_frame, width=10)
        self.lona_price.insert(0, "150.00")
        self.lona_price.grid(row=3, column=1, pady=5)
        
        self.lbl_lona_status = tk.Label(frame, text="", bg="#121212", fg="#888")
        self.lbl_lona_status.pack()

    def load_lona_image(self):
        f = filedialog.askopenfilename(filetypes=[("Imagenes", "*.jpg *.png *.bmp *.jpeg *.tif *.tiff")])
        if f: self.lona_img_path.set(f)

    def process_lona(self):
        img_path = self.lona_img_path.get()
        if not img_path or not os.path.exists(img_path):
            messagebox.showerror("Error", "Selecciona una imagen válida")
            return

        try:
            target_w_m = float(self.lona_w.get())
            target_h_m = float(self.lona_h.get())
            dpi_str = self.lona_dpi.get().split()[0]
            target_dpi = int(dpi_str)
        except ValueError:
            messagebox.showerror("Error", "Revisa los números")
            return

        self.lbl_lona_status.config(text="Procesando imagen (esto puede tardar)...", fg="yellow")
        self.root.update()

        try:
            # 1. Abrir Imagen
            img = Image.open(img_path)
            orig_w, orig_h = img.size
            
            # 2. Calcular Pixeles Necesarios
            # 1 metro = 39.37 pulgadas
            pixels_w_needed = int(target_w_m * 39.37 * target_dpi)
            pixels_h_needed = int(target_h_m * 39.37 * target_dpi)
            
            # 3. Escalar (Upscaling Básico Lanczos)
            # NOTA: Para upscaling IA real necesitaríamos librerías pesadas (PyTorch/ESRGAN).
            # Por ahora usamos el mejor filtro bicúbico/Lanczos de PIL que mejora bastante.
            # Si la imagen es MUY pequeña, avisamos.
            
            ratio_w = pixels_w_needed / orig_w
            ratio_h = pixels_h_needed / orig_h
            
            # Advertencia de calidad si se estira demasiado (>4x)
            quality_warning = ""
            if ratio_w > 4 or ratio_h > 4:
                quality_warning = "\n⚠️ ADVERTENCIA: La imagen original es muy pequeña. Se verá pixeleada."
            
            # Resample
            final_img = img.resize((pixels_w_needed, pixels_h_needed), Image.Resampling.LANCZOS)
            
            # 4. Convertir a CMYK para impresión (Opcional, pero profecional)
            # PIL tiene soporte limitado CMYK, mejor guardar RGB con perfil o TIFF.
            # Guardamos como TIFF alta calidad o JPG máxima.
            
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            fname = f"LONA_{target_w_m}x{target_h_m}m_{target_dpi}dpi_{ts}.tif"
            out_path = os.path.join(WATCH_DIR_LONAS, fname)
            
            # Compresión LZW para TIFF es estándar en imprenta
            final_img.save(out_path, dpi=(target_dpi, target_dpi), compression="tiff_lzw")
            
            # Calcular Precio
            try: price_m2 = float(self.lona_price.get())
            except: price_m2 = 150.0
            total_price = (target_w_m * target_h_m) * price_m2

            self.lbl_lona_status.config(text="Listo.", fg="#00ff00")
            msg = (f"✅ Archivo Listo: {fname}\n"
                   f"📏 Dimensión: {pixels_w_needed}x{pixels_h_needed} px\n"
                   f"🖨️ Tamaño Impresión: {target_w_m}x{target_h_m} mts\n"
                   f"✨ Resolución: {target_dpi} DPI\n"
                   f"💰 PRECIO TOTAL: ${total_price:.2f}\n"
                   f"{quality_warning}")
            
            messagebox.showinfo("Lona Optimizada", msg)
            os.startfile(WATCH_DIR_LONAS)

        except Exception as e:
            self.lbl_lona_status.config(text="Error", fg="red")
            messagebox.showerror("Error Procesando", str(e))

    # ==========================================
    # UTILIDADES
    # ==========================================
    def create_cost_frame(self, parent, type_):
        f = tk.LabelFrame(parent, text="COTIZADOR", bg="#121212", fg="#00ff00")
        f.pack(pady=10, fill="x", padx=20)
        
        entries = {}
        # Precios default actualizados
        if type_ == "box":
            defaults = [("Velocidad:", "speed", "300"), ("Costo Min($):", "machine_cost", "2.50"), ("Material(Hoja):", "material_cost", "110"), ("Margen(%):", "margin", "30")]
        else:
            defaults = [("Velocidad:", "speed", "300"), ("Costo Min($):", "machine_cost", "2.50"), ("Material($):", "material_cost", "50"), ("Margen(%):", "margin", "30")]
        
        for i, (txt, k, v) in enumerate(defaults):
            tk.Label(f, text=txt, bg="#121212", fg="#ccc").grid(row=0, column=i*2)
            e = ttk.Entry(f, width=8)
            e.insert(0, v)
            e.grid(row=0, column=i*2+1)
            entries[k] = e
            
        if type_ == "box": self.cost_entries_box = entries
        else: self.cost_entries_engrave = entries

    def get_svg_length(self, path):
        try:
            with open(path, 'r') as f: c = f.read()
            paths = re.findall(r'd="([^"]+)"', c)
            total = 0
            for p in paths:
                nums = [float(x) for x in re.findall(r'[-+]?\d*\.\d+|[-+]?\d+', p)]
                if len(nums) >= 4:
                    for i in range(2, len(nums), 2):
                        total += math.sqrt((nums[i]-nums[i-2])**2 + (nums[i+1]-nums[i-1])**2)
            return total
        except: return 0

    def calculate_price(self, length, type_):
        entries = self.cost_entries_box if type_ == "box" else self.cost_entries_engrave
        speed = float(entries["speed"].get())
        rate = float(entries["machine_cost"].get())
        mat_cost = float(entries["material_cost"].get())
        margin = float(entries["margin"].get())
        
        mins = length / speed if speed > 0 else 0
        
        if type_ == "box":
            # Estimación muy "a ojo" del área basada en perímetro de corte (length)
            # Area aprox (mm2) ~ (length / 4)^2 (asumiendo cuadrado)
            # Hoja 1220x2440 = 2,976,800 mm2. Costo $110.
            # Costo por mm2 = 0.000037
            
            # Un corte de 2 metros (2000mm) para una caja chica...
            # Vamos a usar un factor de seguridad.
            estimated_area_mm2 = (length * 100) # Factor empírico
            proportional_cost = estimated_area_mm2 * (mat_cost / 2976800.0)
            
            # Ajuste solicitado: Cobrar parte porcentual + 5% del material
            material_price = proportional_cost * 1.05
            
            if material_price < 5: material_price = 5 # Mínimo $5 de material
        else:
            material_price = mat_cost # Grabado usa pieza fija o lo que ponga el user

        cost = (mins * rate) + material_price
        return cost * (1 + margin/100)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = NexusWorkshopGUI()
    app.run()
