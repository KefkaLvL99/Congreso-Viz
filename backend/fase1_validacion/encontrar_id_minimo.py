import requests
from bs4 import BeautifulSoup
import time

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}

def tiene_datos(vid):
    url = f"https://www.camara.cl/legislacion/sala_sesiones/votacion_detalle.aspx?prmIdVotacion={vid}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        if len(r.content) < 60000:
            return False, None
        soup = BeautifulSoup(r.content, "html.parser")
        for ficha in soup.find_all(class_="datos-ficha"):
            dato = ficha.find(class_="dato")
            info = ficha.find(class_="info")
            if dato and info and "Fecha" in dato.get_text():
                return True, info.get_text(strip=True)
        return True, "sin fecha"
    except:
        return False, None

# Buscar hacia atrás desde 88440 (sabemos que 88440+ funciona)
# Encontrar el primer ID que falla
print("Buscando límite inferior de IDs válidos...\n")

# Primero confirmar desde dónde funciona
for vid in range(88440, 88420, -1):
    ok, fecha = tiene_datos(vid)
    print(f"  ID {vid}: {'✅ ' + (fecha or '') if ok else '❌ vacio'}")
    time.sleep(0.3)

print("\nAhora buscando hacia atrás en saltos de 100...")
for vid in range(88400, 85000, -100):
    ok, fecha = tiene_datos(vid)
    if ok:
        print(f"  ID {vid}: ✅ {fecha}")
    else:
        print(f"  ID {vid}: ❌")
    time.sleep(0.3)
