import requests
from bs4 import BeautifulSoup
import time

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}

def get_fecha_votacion(vid):
    url = f"https://www.camara.cl/legislacion/sala_sesiones/votacion_detalle.aspx?prmIdVotacion={vid}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        if len(r.content) < 60000:
            return None
        soup = BeautifulSoup(r.content, "html.parser")
        for ficha in soup.find_all(class_="datos-ficha"):
            dato = ficha.find(class_="dato")
            info = ficha.find(class_="info")
            if dato and "Fecha" in dato.get_text() and info:
                return info.get_text(strip=True)
        return None
    except:
        return None

# Sabemos: 88519 = 25 marzo 2026
# Estimamos ~5000 votaciones/año → 2020 ≈ 88519 - (6 * 5000) = 58519
# Probemos puntos clave

puntos = [55000, 60000, 65000, 68000, 70000, 72000, 74000, 76000, 78000, 80000]

print("Buscando ID de enero 2020 (búsqueda binaria):\n")
for vid in puntos:
    fecha = get_fecha_votacion(vid)
    print(f"  ID {vid:6d}: {fecha or 'sin datos'}")
    time.sleep(0.4)
