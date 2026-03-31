# ============================================================
# explorar_diputados.py
# ============================================================
# Explora la estructura HTML del sitio de la Cámara
# para entender cómo extraer los datos de diputados.
# ============================================================

import requests
from bs4 import BeautifulSoup

URL = "https://www.camara.cl/diputados/diputados.aspx"

HEADERS = {
    # Nos identificamos como un navegador normal
    # Algunos sitios bloquean requests sin User-Agent
    "User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0; datos publicos)"
}

print("Consultando sitio de la Cámara...")
r = requests.get(URL, headers=HEADERS, timeout=20)
print(f"HTTP Status: {r.status_code}")
print(f"Tamaño respuesta: {len(r.content)} bytes\n")

soup = BeautifulSoup(r.content, "html.parser")

# ── ESTRATEGIA 1: Buscar tablas ───────────────────────────────
tablas = soup.find_all("table")
print(f"Tablas encontradas: {len(tablas)}")
for i, tabla in enumerate(tablas[:3]):
    filas = tabla.find_all("tr")
    print(f"  Tabla {i+1}: {len(filas)} filas")
    if filas:
        print(f"  Primera fila: {filas[0].get_text(strip=True)[:100]}")

# ── ESTRATEGIA 2: Buscar divs con clase relacionada a diputados
print("\nBuscando divs con clases relevantes...")
for clase in ["diputado", "parlamentario", "listado", "card", "item"]:
    elementos = soup.find_all(class_=lambda c: c and clase.lower() in c.lower())
    if elementos:
        print(f"  clase '{clase}': {len(elementos)} elementos")
        print(f"  Muestra: {elementos[0].get_text(strip=True)[:100]}")

# ── ESTRATEGIA 3: Buscar links a perfiles de diputados ────────
print("\nBuscando links a perfiles de diputados...")
links_diputados = soup.find_all("a", href=lambda h: h and "detalle" in h.lower())
print(f"  Links con 'detalle': {len(links_diputados)}")
if links_diputados:
    for link in links_diputados[:3]:
        print(f"  → {link.get_text(strip=True)} | {link['href']}")

# ── ESTRATEGIA 4: Buscar por texto de nombres ────────────────
print("\nBuscando estructura de nombres...")
# Buscamos elementos li o div que contengan nombres
items = soup.find_all(["li", "div", "tr"])
nombres_encontrados = []
for item in items:
    texto = item.get_text(strip=True)
    # Un nombre típico tiene entre 10 y 50 caracteres y no tiene etiquetas HTML complejas
    if 10 < len(texto) < 60 and len(item.find_all()) < 3:
        nombres_encontrados.append(texto)

print(f"  Posibles nombres encontrados: {len(nombres_encontrados)}")
for n in nombres_encontrados[:5]:
    print(f"  → {n}")

# ── ESTRATEGIA 5: Ver el HTML crudo de la sección principal ──
print("\nHTML de la sección principal (primeros 3000 chars del body):")
body = soup.find("body")
if body:
    # Elimina scripts y styles para ver solo el contenido
    for tag in body.find_all(["script", "style"]):
        tag.decompose()
    print(body.get_text(separator="\n", strip=True)[:3000])
