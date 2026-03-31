# ============================================================
# explorar_votaciones_camara2.py
# ============================================================
# Explora la página de votaciones de sala de la Cámara
# para entender cómo extraer los datos via scraping.
# ============================================================

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}

# ── PASO 1: Ver la página principal de votaciones ────────────
print("=" * 60)
print("PASO 1 — Página principal de votaciones Cámara")
print("=" * 60)

url = "https://www.camara.cl/legislacion/sala_sesiones/votaciones.aspx"
r = requests.get(url, headers=HEADERS, timeout=20)
print(f"HTTP: {r.status_code} | {len(r.content)} bytes")

soup = BeautifulSoup(r.content, "html.parser")
for tag in soup.find_all(["script", "style"]):
    tag.decompose()

# Buscar tablas con votaciones
tablas = soup.find_all("table")
print(f"Tablas encontradas: {len(tablas)}")

# Buscar links a votaciones individuales
links_vot = []
for a in soup.find_all("a", href=True):
    href = a["href"]
    if "votacion" in href.lower() or "vot" in href.lower():
        texto = a.get_text(strip=True)
        if texto:
            links_vot.append({"texto": texto, "href": href})

print(f"Links con 'votacion': {len(links_vot)}")
for l in links_vot[:5]:
    print(f"  {l['texto']} → {l['href']}")

# Ver texto limpio de la página
texto = soup.get_text(separator="\n", strip=True)
lineas = [l for l in texto.split("\n") if len(l) > 5]
print(f"\nPrimeras 40 líneas de contenido:")
for l in lineas[:40]:
    print(f"  {l}")

# ── PASO 2: Probar con parámetro de fecha ───────────────────
print("\n" + "=" * 60)
print("PASO 2 — Intentar POST con fecha")
print("=" * 60)

# La Cámara usa ASP.NET con __VIEWSTATE — necesitamos extraerlo
viewstate = soup.find("input", {"name": "__VIEWSTATE"})
eventval  = soup.find("input", {"name": "__EVENTVALIDATION"})

print(f"__VIEWSTATE encontrado: {viewstate is not None}")
print(f"__EVENTVALIDATION encontrado: {eventval is not None}")

if viewstate:
    # Intentar POST con fecha
    data = {
        "__VIEWSTATE":       viewstate.get("value", ""),
        "__EVENTVALIDATION": eventval.get("value", "") if eventval else "",
        "txtFecha":          "01/03/2026",
    }
    r2 = requests.post(url, headers=HEADERS, data=data, timeout=20)
    print(f"\nPOST HTTP: {r2.status_code} | {len(r2.content)} bytes")

    soup2 = BeautifulSoup(r2.content, "html.parser")
    for tag in soup2.find_all(["script", "style"]):
        tag.decompose()

    tablas2 = soup2.find_all("table")
    print(f"Tablas en respuesta POST: {len(tablas2)}")

    for i, tabla in enumerate(tablas2[:3]):
        filas = tabla.find_all("tr")
        print(f"\n  Tabla {i+1}: {len(filas)} filas")
        for fila in filas[:3]:
            celdas = [td.get_text(strip=True) for td in fila.find_all(["td","th"])]
            if any(c for c in celdas):
                print(f"    {celdas}")
