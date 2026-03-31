# ============================================================
# explorar_perfil_diputado.py
# ============================================================
# Explora el perfil individual de un diputado para entender
# qué datos podemos extraer de cada página.
# Usamos a Jorge Alessandri (ID 1009) como ejemplo.
# ============================================================

import requests
from bs4 import BeautifulSoup
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0; datos publicos)"
}

# ── PASO 1: Ver qué IDs hay en la página principal ────────────
print("=" * 55)
print("PASO 1 — Extrayendo IDs desde página principal")
print("=" * 55)

URL_LISTADO = "https://www.camara.cl/diputados/diputados.aspx"
r = requests.get(URL_LISTADO, headers=HEADERS, timeout=20)
soup = BeautifulSoup(r.content, "html.parser")

# Extraer todos los links a perfiles únicos
ids_vistos = set()
diputados_encontrados = []

for link in soup.find_all("a", href=True):
    href = link["href"]
    # Buscar links que contengan prmID
    match = re.search(r"prmID=(\d+)", href)
    if match:
        pid = match.group(1)
        nombre = link.get_text(strip=True)
        if pid not in ids_vistos and nombre:
            ids_vistos.add(pid)
            diputados_encontrados.append({
                "id": pid,
                "nombre": nombre,
                "url": href if href.startswith("http") else f"https://www.camara.cl{href}"
            })

print(f"IDs únicos encontrados: {len(ids_vistos)}")
print(f"Diputados con nombre: {len(diputados_encontrados)}")
print("\nPrimeros 5:")
for d in diputados_encontrados[:5]:
    print(f"  ID {d['id']}: {d['nombre']}")

# ── PASO 2: Explorar perfil individual ───────────────────────
print("\n" + "=" * 55)
print("PASO 2 — Explorando perfil individual (ID 1009)")
print("=" * 55)

# Hay dos URLs posibles para el perfil — probamos ambas
URLS_PERFIL = [
    "https://www.camara.cl/diputados/detalle/mociones.aspx?prmID=1009",
    "https://www.camara.cl/diputados/detalle/index.aspx?prmID=1009",
]

for url in URLS_PERFIL:
    print(f"\nProbando: {url}")
    rp = requests.get(url, headers=HEADERS, timeout=20)
    print(f"HTTP: {rp.status_code} | Tamaño: {len(rp.content)} bytes")

    if rp.status_code == 200:
        sp = BeautifulSoup(rp.content, "html.parser")

        # Eliminar scripts y estilos
        for tag in sp.find_all(["script", "style"]):
            tag.decompose()

        # Buscar datos clave
        texto = sp.get_text(separator="\n", strip=True)

        # Mostrar primeros 2000 chars del texto limpio
        print("\nTexto extraído (primeros 2000 chars):")
        print(texto[:2000])

        # Buscar campos específicos
        print("\nBuscando campos específicos:")
        for campo in ["Partido", "Región", "Distrito", "Comisión", "Email", "Teléfono"]:
            if campo.lower() in texto.lower():
                # Encontrar la línea que contiene el campo
                lineas = texto.split("\n")
                for i, linea in enumerate(lineas):
                    if campo.lower() in linea.lower() and len(linea) < 100:
                        # Mostrar esa línea y la siguiente
                        contexto = lineas[i:i+2]
                        print(f"  {campo}: {' | '.join(contexto)}")
                        break
        break
