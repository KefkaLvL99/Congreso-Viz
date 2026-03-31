import requests
from bs4 import BeautifulSoup
import time

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}

def analizar_votacion(vid):
    url = f"https://www.camara.cl/legislacion/sala_sesiones/votacion_detalle.aspx?prmIdVotacion={vid}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        size = len(r.content)
        
        # Página de error tiene ~50241 bytes exactos
        # Página con datos tiene >60000 bytes
        if size < 60000:
            return None, size, "vacio"
        
        soup = BeautifulSoup(r.content, "html.parser")
        
        # Buscar fecha
        fecha = None
        for ficha in soup.find_all(class_="datos-ficha"):
            dato = ficha.find(class_="dato")
            info = ficha.find(class_="info")
            if dato and info and "Fecha" in dato.get_text():
                fecha = info.get_text(strip=True)
                break
        
        # Buscar materia/título
        titulo = None
        for ficha in soup.find_all(class_="datos-ficha"):
            info = ficha.find(class_="info")
            dato = ficha.find(class_="dato")
            if dato and info and "Materia" in dato.get_text():
                titulo = info.get_text(strip=True)[:50]
                break

        return fecha, size, titulo or "sin titulo"
    except Exception as e:
        return None, 0, f"error: {e}"

# Estrategia: encontrar IDs válidos cerca de cada rango
# Sabemos que 88519 es válido (marzo 2026)
# Sabemos que 88491 es válido (marzo 2026)
# Buscamos hacia atrás en saltos de 1000 para encontrar la distribución

print("Mapeando IDs válidos por rango:\n")
print(f"{'ID':>8} {'Bytes':>8} {'Fecha':<20} {'Título'}")
print("-" * 80)

# Probar cada 500 IDs desde 88000 hacia atrás hasta 55000
ids_validos = []
for vid in range(88000, 54000, -2000):
    fecha, size, info = analizar_votacion(vid)
    estado = "✅" if fecha else "❌"
    print(f"{vid:>8} {size:>8} {fecha or '-':<20} {info[:40]}")
    if fecha:
        ids_validos.append((vid, fecha))
    time.sleep(0.5)

print(f"\nIDs válidos encontrados: {len(ids_validos)}")
for vid, fecha in ids_validos:
    print(f"  ID {vid}: {fecha}")
