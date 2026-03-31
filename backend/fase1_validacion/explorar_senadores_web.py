# ============================================================
# explorar_senadores_web.py
# ============================================================
# Explora el sitio web del Senado para obtener los 50 senadores
# con nombre, partido, región y circunscripción.
# ============================================================

import requests
from bs4 import BeautifulSoup

URL = "https://www.senado.cl/senadoras-y-senadores/listado-de-senadoras-y-senadores"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0; datos publicos)"}

print("Consultando sitio del Senado...")
r = requests.get(URL, headers=HEADERS, timeout=20)
print(f"HTTP: {r.status_code} | {len(r.content)} bytes\n")

soup = BeautifulSoup(r.content, "html.parser")

# Buscar tarjetas de senadores
senadores = []

# Buscar por estructura: h3 con nombre + li con circunscripción y partido
for card in soup.find_all("a", href=True):
    h3 = card.find("h3")
    if not h3:
        continue

    nombre = h3.get_text(strip=True)
    if not nombre or len(nombre) < 5:
        continue

    # Buscar circunscripción y partido dentro de la card
    items = card.find_all("li")
    circunscripcion = None
    region          = None
    partido         = None

    for li in items:
        h4 = li.find("h4")
        if not h4:
            continue
        label = h4.get_text(strip=True)
        # El texto después del h4
        texto_completo = li.get_text(strip=True)
        valor = texto_completo.replace(label, "").strip()

        if "Circunscripción" in label:
            circunscripcion = label.replace("Circunscripción", "").strip()
            region = valor
        elif "Partido" in label:
            partido = label.replace("Partido", "").strip()

    if nombre and partido:
        senadores.append({
            "nombre":          nombre,
            "circunscripcion": circunscripcion,
            "region":          region,
            "partido":         partido,
        })

print(f"Senadores encontrados: {len(senadores)}\n")
for s in senadores[:10]:
    print(f"  {s['nombre']}")
    print(f"    Partido: {s['partido']} | Región: {s['region']} | Circ: {s['circunscripcion']}")
