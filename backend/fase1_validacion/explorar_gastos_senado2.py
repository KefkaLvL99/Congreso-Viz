import requests
from bs4 import BeautifulSoup
import re
import json

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}

url = "https://www.senado.cl/transparencia/gastos-operacionales-senadores"
r = requests.get(url, headers=HEADERS, timeout=20)
print(f"HTTP: {r.status_code} | {len(r.content)} bytes")

soup = BeautifulSoup(r.content, "html.parser")

# Buscar tablas
tablas = soup.find_all("table")
print(f"Tablas: {len(tablas)}")
for i, t in enumerate(tablas[:2]):
    filas = t.find_all("tr")
    print(f"\n  Tabla {i+1}: {len(filas)} filas")
    for fila in filas[:5]:
        celdas = [td.get_text(strip=True) for td in fila.find_all(["td","th"])]
        if any(c for c in celdas):
            print(f"    {celdas}")

# Buscar datos JSON embebidos en scripts
scripts = soup.find_all("script")
print(f"\nScripts: {len(scripts)}")
for i, s in enumerate(scripts):
    contenido = s.string or ""
    if any(k in contenido for k in ["gasto", "parlamentario", "monto", "asignacion"]):
        print(f"\n  Script {i} ({len(contenido)} chars):")
        print(f"  {contenido[:500]}")

# Buscar selects con opciones de año/mes
selects = soup.find_all("select")
print(f"\nSelects: {len(selects)}")
for sel in selects:
    opts = sel.find_all("option")
    print(f"  {sel.get('name') or sel.get('id')}: {[o.get_text(strip=True) for o in opts[:10]]}")

# Buscar API calls en el HTML
apis = re.findall(r'(https?://[^\s"\']+(?:api|json|xml|gastos)[^\s"\']*)', r.text)
print(f"\nPosibles APIs encontradas:")
for api in set(apis[:10]):
    print(f"  {api}")

# Buscar fetch/ajax en scripts
fetches = re.findall(r'fetch\(["\']([^"\']+)["\']', r.text)
print(f"\nFetch calls:")
for f in fetches[:10]:
    print(f"  {f}")
