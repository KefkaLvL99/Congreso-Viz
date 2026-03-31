# ============================================================
# explorar_votaciones.py
# ============================================================
# Explora los endpoints disponibles para obtener votaciones
# del Senado y la Cámara de Diputados.
# ============================================================

import requests
import xml.etree.ElementTree as ET
from lxml import etree
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}
TIMEOUT = 15

def get_xml(url):
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    print(f"  HTTP: {r.status_code} | {len(r.content)} bytes")
    try:
        parser = etree.XMLParser(recover=True)
        root = etree.fromstring(r.content, parser=parser)
        return root, r
    except:
        return None, r

def imprimir_nodo(nodo, nivel=0, max_nivel=4):
    indent = "  " * nivel
    texto = nodo.text.strip() if nodo.text and nodo.text.strip() else ""
    texto_corto = texto[:60] + "..." if len(texto) > 60 else texto
    linea = f"{indent}<{nodo.tag}>"
    if texto_corto:
        linea += f"  → '{texto_corto}'"
    print(linea)
    if nivel < max_nivel:
        for hijo in nodo:
            imprimir_nodo(hijo, nivel + 1, max_nivel)

# ── ENDPOINT 1: Votaciones por boletín (Senado) ───────────────
print("=" * 55)
print("ENDPOINT 1 — Votaciones por boletín (Senado)")
print("=" * 55)
# Usamos boletín 16456 como ejemplo reciente
url = "https://tramitacion.senado.cl/wspublico/invoca_votacion.html?boletin=16456"
print(f"URL: {url}")
root, r = get_xml(url)
if root is not None:
    hijos = list(root)
    print(f"  Nodo raíz: <{root.tag}> | Hijos: {len(hijos)}")
    print("\n  Estructura:")
    imprimir_nodo(root, nivel=1, max_nivel=5)
else:
    print("  No es XML, mostrando texto:")
    print(r.text[:500])

# ── ENDPOINT 2: Tramitación por fecha (proyectos recientes) ──
print("\n" + "=" * 55)
print("ENDPOINT 2 — Proyectos con movimiento reciente")
print("=" * 55)
from datetime import datetime, timedelta
fecha = (datetime.now() - timedelta(days=7)).strftime("%d/%m/%Y")
url2 = f"https://tramitacion.senado.cl/wspublico/tramitacion.php?fecha={fecha}"
print(f"URL: {url2}")
root2, r2 = get_xml(url2)
if root2 is not None:
    hijos2 = list(root2)
    print(f"  Nodo raíz: <{root2.tag}> | Hijos: {len(hijos2)}")
    print("\n  Primeros 2 registros:")
    for hijo in hijos2[:2]:
        imprimir_nodo(hijo, nivel=2, max_nivel=5)
else:
    print("  No es XML:")
    print(r2.text[:300])

# ── ENDPOINT 3: Votaciones sala Cámara ───────────────────────
print("\n" + "=" * 55)
print("ENDPOINT 3 — Votaciones sala Cámara (scraping)")
print("=" * 55)
url3 = "https://www.camara.cl/legislacion/sala_sesiones/votaciones.aspx"
print(f"URL: {url3}")
r3 = requests.get(url3, headers=HEADERS, timeout=TIMEOUT)
print(f"  HTTP: {r3.status_code} | {len(r3.content)} bytes")
soup = BeautifulSoup(r3.content, "html.parser")
for tag in soup.find_all(["script", "style"]):
    tag.decompose()
texto3 = soup.get_text(separator="\n", strip=True)
# Mostrar solo las primeras líneas relevantes
lineas = [l for l in texto3.split("\n") if len(l) > 10]
print("\n  Primeras 30 líneas de contenido:")
for linea in lineas[:30]:
    print(f"  {linea}")

