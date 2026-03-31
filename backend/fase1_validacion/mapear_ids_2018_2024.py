import requests
from bs4 import BeautifulSoup
import time

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}

def get_fecha(vid):
    url = f"https://www.camara.cl/legislacion/sala_sesiones/votacion_detalle.aspx?prmIdVotacion={vid}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        if len(r.content) < 60000:
            return None
        soup = BeautifulSoup(r.content, "html.parser")
        for ficha in soup.find_all(class_="datos-ficha"):
            dato = ficha.find(class_="dato")
            info = ficha.find(class_="info")
            if dato and info and "Fecha" in dato.get_text():
                return info.get_text(strip=True)
        return "sin fecha"
    except:
        return None

print("Mapeando IDs 2018-2024 (saltos de 500):\n")
ids_validos = []
for vid in range(82000, 50000, -500):
    fecha = get_fecha(vid)
    if fecha:
        print(f"  ID {vid:>8}  ✅ {fecha}")
        ids_validos.append((vid, fecha))
    else:
        print(f"  ID {vid:>8}  ❌")
    time.sleep(0.4)

print(f"\nResumen: {len(ids_validos)} IDs válidos")
for vid, fecha in ids_validos:
    print(f"  ID {vid}: {fecha}")
