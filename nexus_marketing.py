"""
nexus_marketing.py — Generador de guiones y campañas de marketing.
Usa marketing_db.json para hooks/CTAs y precios_base.json para productos reales.
Integra Groq IA si hay API key, fallback a templates si no.
"""
import os
import json
import random
import datetime

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DB_PATH    = os.path.join(BASE_DIR, "CONFIG", "marketing_db.json")
PRECIOS_PATH = os.path.join(BASE_DIR, "CONFIG", "precios_base.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "TALLER", "MARKETING_STUDIO")

class MarketingManager:
    def __init__(self):
        self.db      = self._load_json(DB_PATH,    default={"hooks": {}, "ctas": [], "hashtags": {}})
        self.precios = self._load_json(PRECIOS_PATH, default={})
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    def _load_json(self, path, default=None):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default or {}

    def _precio_producto(self, nombre_lower: str) -> str:
        """Busca precio en precios_base.json para mencionarlo en el guion."""
        for item in self.precios.get("sublimacion_personalizacion", []):
            if any(w in item.get("nombre", "").lower() for w in nombre_lower.split() if len(w) > 3):
                p = item.get("precio_subli") or item.get("precio_laser") or item.get("precio_dtf") or 0
                if p:
                    return f"Desde ${p:.0f} pesos."
        if "laser" in nombre_lower or "corte" in nombre_lower or "mdf" in nombre_lower:
            cpm = self.precios.get("laser", {}).get("costo_minuto", 8)
            return f"Corte desde ${cpm * 5:.0f} pesos (5 min)."
        if "retrofit" in nombre_lower or "led" in nombre_lower:
            retro = self.precios.get("retrofit", [])
            if retro:
                return f"Desde ${retro[0]['precio']:.0f} pesos."
        return ""

    def generate_script(self, producto_nombre: str, tipo: str = "laser") -> tuple:
        """Genera guion de 3 actos para Reels/TikTok."""
        hook_type = random.choice(["curiosidad", "dolor", "oferta"])
        hook  = random.choice(self.db["hooks"].get(hook_type, ["Mira esto que hicimos."]))
        cta   = random.choice(self.db.get("ctas", ["Manda mensaje para cotizar."]))
        tags  = self.db.get("hashtags", {}).get(tipo, "#hechoenmexico #viral")
        precio_txt = self._precio_producto(producto_nombre.lower())

        body = (
            f"Este es nuestro {producto_nombre}. "
            f"Fabricado con precisión en nuestro taller. "
            + (f"{precio_txt} " if precio_txt else "")
            + "Personalizado para ti."
        )

        script = f"""
=== GUION REEL/TIKTOK ===
Producto: {producto_nombre}
Generado: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}

[ESCENA 1 — 3 seg — Primer plano del producto]
VOZ: {hook}

[ESCENA 2 — 5 seg — Proceso de fabricación]
VOZ: {body}

[ESCENA 3 — 3 seg — Producto terminado]
VOZ: {cta}

[CAPTION SUGERIDO]
{hook} {tags}

[HASHTAGS]
{tags}
"""
        return script, f"{hook} {body} {cta}"

    def generate_script_with_ai(self, producto_nombre: str, tipo: str = "laser") -> tuple:
        """Genera guion con Groq IA si hay API key. Fallback a templates."""
        groq_key = os.environ.get("GROQ_API_KEY", "")
        if not groq_key:
            return self.generate_script(producto_nombre, tipo)
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            precio_txt = self._precio_producto(producto_nombre.lower())
            tags = self.db.get("hashtags", {}).get(tipo, "#hechoenmexico")
            prompt = (
                f"Crea un guion corto de 3 escenas para un Reel de TikTok/Instagram "
                f"sobre: '{producto_nombre}'. "
                f"{'Precio referencia: ' + precio_txt if precio_txt else ''} "
                f"Usa hashtags: {tags}. "
                f"Tono: emprendedor mexicano, auténtico, no corporativo. "
                f"Máximo 100 palabras total. Formato: [Escena 1] texto [Escena 2] texto [Escena 3] texto."
            )
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300
            )
            ai_script = resp.choices[0].message.content.strip()
            return ai_script, ai_script
        except Exception as e:
            print(f"[MARKETING] Groq falló ({e}), usando template.")
            return self.generate_script(producto_nombre, tipo)

    def create_campaign_files(self, producto_nombre: str, tipo: str = "laser", use_ai: bool = True) -> tuple:
        """Genera carpeta de campaña con guion listo."""
        if use_ai:
            script_text, speech_text = self.generate_script_with_ai(producto_nombre, tipo)
        else:
            script_text, speech_text = self.generate_script(producto_nombre, tipo)

        ts     = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        folder = os.path.join(OUTPUT_DIR, f"CAMPAÑA_{producto_nombre.replace(' ','_')}_{ts}")
        os.makedirs(folder, exist_ok=True)

        with open(os.path.join(folder, "GUION.txt"), "w", encoding="utf-8") as f:
            f.write(script_text)

        print(f"[MARKETING] Campaña creada: {folder}")
        return folder, speech_text

manager = MarketingManager()
