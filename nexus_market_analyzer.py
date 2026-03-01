"""
NEXUS Market Analyzer
Analiza precios de MercadoLibre México con IA (Groq)
- Scraping web ML (no requiere API key)
- Estadísticas: min, max, promedio, mediana, top vendidos
- Groq analiza estrategia de precio
"""

import httpx
import json
import os
import re
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()
GROQ_KEY = os.getenv("GROQ_API_KEY", "")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}

# ---------- ML SCRAPING (sin auth) ----------

async def buscar_ml(query: str, limite: int = 20, categoria: str = None) -> dict:
    """
    Busca productos en MercadoLibre México scrapeando resultados web.
    """
    # ML embedding JSON in search pages — usar API con token si disponible, si no scrape
    ml_token = os.getenv("ML_ACCESS_TOKEN", "")
    if ml_token:
        return await _buscar_ml_api(query, limite, ml_token)
    return await _buscar_ml_scrape(query, limite)


async def _buscar_ml_api(query: str, limite: int, token: str) -> dict:
    """Busca via ML API oficial con access token"""
    params = {"q": query, "limit": min(limite, 50)}
    url = "https://api.mercadolibre.com/sites/MLM/search"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            url, params=params,
            headers={"Authorization": f"Bearer {token}"}
        )
        if resp.status_code != 200:
            return {"ok": False, "error": f"ML API {resp.status_code} — Token inválido o vencido"}
        data = resp.json()

    resultados = []
    for item in data.get("results", []):
        resultados.append({
            "id": item.get("id"),
            "titulo": item.get("title"),
            "precio": item.get("price"),
            "moneda": item.get("currency_id"),
            "vendidos": item.get("sold_quantity", 0),
            "condicion": item.get("condition"),
            "envio_gratis": item.get("shipping", {}).get("free_shipping", False),
            "link": item.get("permalink"),
            "thumbnail": item.get("thumbnail"),
        })

    return {
        "ok": True,
        "query": query,
        "total_ml": data.get("paging", {}).get("total", 0),
        "resultados": resultados,
        "fuente": "api",
    }


async def _buscar_ml_scrape(query: str, limite: int) -> dict:
    """
    Scraping de ML search page — extrae JSON embebido en la página
    """
    url = f"https://listado.mercadolibre.com.mx/{quote_plus(query)}"
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.get(url, headers=HEADERS)

        if resp.status_code != 200:
            return {"ok": False, "error": f"ML web {resp.status_code}"}

        html = resp.text

        # Extraer JSON de resultados embebido en __PRELOADED_STATE__
        resultados = []

        # Método 1: buscar prices en HTML via regex patterns
        # ML embeds item data in script tags as JSON
        pattern_items = re.findall(
            r'"price"\s*:\s*(\d+(?:\.\d+)?)'
            r'.*?"title"\s*:\s*"([^"]{10,})"',
            html, re.DOTALL
        )

        # Método 2: buscar data-price y data-title attributes
        prices_raw = re.findall(r'class="[^"]*price[^"]*"[^>]*>\s*\$\s*([\d,]+)', html)
        prices_raw2 = re.findall(r'"price":(\d+(?:\.\d+)?)', html)
        titles_raw = re.findall(r'"title":"([^"]{15,120})"', html)

        precios_encontrados = []
        for p in prices_raw2[:limite]:
            try:
                val = float(p)
                if val > 100:  # filtrar precios irreales
                    precios_encontrados.append(val)
            except:
                pass

        # Parsear __PRELOADED_STATE__ si existe
        preloaded = re.search(r'window\.__PRELOADED_STATE__\s*=\s*(\{.+?\});\s*</script>', html, re.DOTALL)
        if preloaded:
            try:
                state = json.loads(preloaded.group(1))
                items = (state.get("initialState", {})
                         .get("results", state.get("results", [])))
                for item in items[:limite]:
                    precio = item.get("price", item.get("prices", {}).get("prices", [{}])[0].get("amount", 0))
                    resultados.append({
                        "id": item.get("id", ""),
                        "titulo": item.get("title", ""),
                        "precio": float(precio) if precio else 0,
                        "moneda": "MXN",
                        "vendidos": item.get("sold_quantity", 0),
                        "condicion": item.get("condition", ""),
                        "envio_gratis": item.get("shipping", {}).get("free_shipping", False),
                        "link": item.get("permalink", ""),
                        "thumbnail": item.get("thumbnail", ""),
                    })
            except Exception:
                pass

        # Si no pudo parsear el state completo, construir resultados simples
        if not resultados:
            titles = [t for t in titles_raw if len(t) > 15][:limite]
            for i, precio in enumerate(precios_encontrados[:limite]):
                resultados.append({
                    "id": f"scraped_{i}",
                    "titulo": titles[i] if i < len(titles) else f"Producto {i+1}",
                    "precio": precio,
                    "moneda": "MXN",
                    "vendidos": 0,
                    "condicion": "new",
                    "envio_gratis": False,
                    "link": url,
                    "thumbnail": "",
                })

        # Estimar total desde el HTML
        total_match = re.search(r'"total"\s*:\s*(\d+)', html)
        total = int(total_match.group(1)) if total_match else len(resultados)

        return {
            "ok": True,
            "query": query,
            "total_ml": total,
            "resultados": resultados,
            "fuente": "scrape",
        }

    except Exception as e:
        return {"ok": False, "error": f"Error scraping: {str(e)}"}


# ---------- ESTADÍSTICAS ----------

def calcular_estadisticas(resultados: list) -> dict:
    precios = [r["precio"] for r in resultados if r.get("precio") and r["precio"] > 100]
    if not precios:
        return {"min": 0, "max": 0, "promedio": 0, "mediana": 0, "count": 0}

    precios_sorted = sorted(precios)
    n = len(precios_sorted)
    mediana = (precios_sorted[n // 2] if n % 2 != 0
               else (precios_sorted[n // 2 - 1] + precios_sorted[n // 2]) / 2)

    vendidos = [r.get("vendidos", 0) for r in resultados if r.get("precio", 0) > 100]
    top_vendidos = sorted(
        [r for r in resultados if r.get("precio", 0) > 100],
        key=lambda x: x.get("vendidos", 0), reverse=True
    )[:5]

    return {
        "min": min(precios),
        "max": max(precios),
        "promedio": round(sum(precios) / n, 2),
        "mediana": round(mediana, 2),
        "count": n,
        "total_vendidos": sum(vendidos),
        "top_vendidos": top_vendidos,
        "con_envio_gratis": sum(1 for r in resultados if r.get("envio_gratis")),
    }


# ---------- ANÁLISIS IA ----------

async def analizar_con_ia(query: str, stats: dict, mi_precio: float = None, contexto: str = "") -> dict:
    if not GROQ_KEY:
        return {"ok": False, "error": "GROQ_API_KEY no configurada"}

    top_str = json.dumps(
        [{"titulo": t["titulo"][:60], "precio": t["precio"], "vendidos": t["vendidos"]}
         for t in stats.get("top_vendidos", [])],
        ensure_ascii=False, indent=2
    )

    prompt = f"""Eres experto en estrategia de precios para MercadoLibre México.

Producto: "{query}"
{f'Contexto: {contexto}' if contexto else ''}

Mercado (MXN):
- Mínimo: ${stats['min']:,.0f}
- Máximo: ${stats['max']:,.0f}
- Promedio: ${stats['promedio']:,.0f}
- Mediana: ${stats['mediana']:,.0f}
- Competidores analizados: {stats['count']}
- Vendidos (muestra): {stats.get('total_vendidos', 0)}
- Con envío gratis: {stats.get('con_envio_gratis', 0)}/{stats['count']}

{f'Mi precio: ${mi_precio:,.0f} MXN' if mi_precio else ''}

Top más vendidos:
{top_str}

Responde SOLO en JSON (sin markdown):
{{
  "posicion_mercado": "Por debajo del promedio | Competitivo | Por encima del promedio",
  "precio_recomendado": numero,
  "precio_con_envio_gratis": numero,
  "estrategia": "2-3 oraciones con estrategia concreta y accionable",
  "titulo_ml_sugerido": "título optimizado ML 60-70 chars",
  "palabras_clave": ["kw1","kw2","kw3","kw4","kw5"],
  "advertencias": ["advertencia importante si existe"],
  "oportunidad": "texto corto sobre oportunidad detectada"
}}"""

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.4,
                    "max_tokens": 800,
                },
            )
        if resp.status_code != 200:
            return {"ok": False, "error": f"Groq {resp.status_code}"}

        content = resp.json()["choices"][0]["message"]["content"].strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        analisis = json.loads(content)
        analisis["ok"] = True
        return analisis
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ---------- PIPELINE COMPLETO ----------

async def analisis_completo(query: str, mi_precio: float = None, limite: int = 30, contexto: str = "") -> dict:
    busqueda = await buscar_ml(query, limite)
    if not busqueda["ok"]:
        return busqueda

    stats = calcular_estadisticas(busqueda["resultados"])

    if stats["count"] == 0:
        return {
            "ok": False,
            "error": "No se encontraron precios en ML para esa búsqueda. Intenta con términos más generales.",
        }

    ia = await analizar_con_ia(query, stats, mi_precio, contexto)

    return {
        "ok": True,
        "query": query,
        "mi_precio": mi_precio,
        "stats": stats,
        "ia": ia,
        "resultados": busqueda["resultados"][:15],
        "total_encontrados": busqueda["total_ml"],
        "fuente": busqueda.get("fuente", "scrape"),
    }
