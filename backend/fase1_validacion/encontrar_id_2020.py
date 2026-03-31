import requests
from bs4 import BeautifulSoup
import time

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}

def get_fecha_votacion(vid):
    url = f"https://www.camara.cl/legislacion/sala_sesiones/votacion_detalle.aspx?prmIdVotacion={vid}"
    r = requests.get(url, headers=HEADERS, timeout=8)
    if len(r.content) < 60000:
        return None
    soup = BeautifulSoup(r.content, "html.parser")
    for ficha in soup.find_all(class_="datos-ficha"):
        info = ficha.find(class_="info")
        dato = ficha.find(class_="dato")
        if dato and "Fecha" in dato.get_text():
            return info.get_text(strip=True) if info else None
    return None

# Búsqueda binaria para encontrar el ID de enero 2020
# Sabemos: ID ~88519 = marzo 2026
# Estimamos: ~1000 votaciones/año → enero 2020 ≈ 88519 - (6.2 * 1000) ≈ 82000

print("Buscando ID aproximado para enero 2020...")
print("(Búsqueda binaria — puede tomar 1-2 minutos)\n")

# Probar puntos de referencia
puntos = [70000, 75000, 78000, 80000, 82000, 83000, 84000, 85000]

for vid in puntos:
    fecha = get_fecha_votacion(vid)
    print(f"  ID {vid}: {fecha}")
    time.sleep(0.3)
