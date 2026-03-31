import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}

url = "https://tramitacion.senado.cl/appsenado/templates/tramitacion/index.php?boletin_ini=11608-09"
r = requests.get(url, headers=HEADERS, timeout=20)
soup = BeautifulSoup(r.content, "html.parser")

# Extraer todas las tablas con datos
tablas = soup.find_all("table")
for i, tabla in enumerate(tablas):
    filas = tabla.find_all("tr")
    if len(filas) < 3:
        continue
    print(f"\n{'='*60}")
    print(f"Tabla {i+1}: {len(filas)} filas")
    print(f"ID: {tabla.get('id')} | Class: {tabla.get('class')}")
    print(f"{'='*60}")
    for fila in filas[:10]:
        celdas = [td.get_text(strip=True) for td in fila.find_all(["td","th"])]
        if any(c for c in celdas):
            print(f"  {celdas}")
    if len(filas) > 10:
        print(f"  ... ({len(filas)-10} filas más)")

# Ver si hay URLs con parámetros de fecha
print("\n\nProbando con parámetros de fecha:")
urls = [
    "https://tramitacion.senado.cl/appsenado/templates/tramitacion/index.php?boletin_ini=11608-09&fecha_ini=01/03/2026&fecha_fin=30/03/2026",
    "https://tramitacion.senado.cl/appsenado/templates/tramitacion/index.php?boletin_ini=16481-25",
    "https://tramitacion.senado.cl/appsenado/templates/tramitacion/index.php",
]
for u in urls:
    r2 = requests.get(u, headers=HEADERS, timeout=20)
    soup2 = BeautifulSoup(r2.content, "html.parser")
    tablas2 = [t for t in soup2.find_all("table") if len(t.find_all("tr")) > 3]
    boletines = []
    for t in tablas2:
        for fila in t.find_all("tr"):
            celdas = [td.get_text(strip=True) for td in fila.find_all(["td","th"])]
            if celdas and re.match(r'\d+-\d+', celdas[0]):
                boletines.append(celdas)
    print(f"\n{u}")
    print(f"  HTTP: {r2.status_code} | {len(r2.content)} bytes | boletines: {len(boletines)}")
    for b in boletines[:5]:
        print(f"    {b}")

import re
