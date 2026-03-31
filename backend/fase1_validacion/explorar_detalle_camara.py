# ============================================================
# explorar_detalle_camara.py
# ============================================================

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}

def explorar_votacion(votacion_id):
    url = f"https://www.camara.cl/legislacion/sala_sesiones/votacion_detalle.aspx?prmIdVotacion={votacion_id}"
    print(f"\nURL: {url}")
    r = requests.get(url, headers=HEADERS, timeout=20)
    print(f"HTTP: {r.status_code} | {len(r.content)} bytes")

    soup = BeautifulSoup(r.content, "html.parser")
    for tag in soup.find_all(["script", "style"]):
        tag.decompose()

    texto = soup.get_text(separator="\n", strip=True)
    lineas = [l for l in texto.split("\n") if len(l) > 3]

    print(f"\nContenido ({len(lineas)} líneas):")
    for l in lineas[:60]:
        print(f"  {l}")

    # Buscar tablas
    tablas = soup.find_all("table")
    print(f"\nTablas: {len(tablas)}")
    for i, tabla in enumerate(tablas[:3]):
        filas = tabla.find_all("tr")
        print(f"\n  Tabla {i+1}: {len(filas)} filas")
        for fila in filas[:5]:
            celdas = [td.get_text(strip=True) for td in fila.find_all(["td","th"])]
            if any(c for c in celdas):
                print(f"    {celdas}")

    # Buscar divs con datos
    print(f"\nDivs con clase relevante:")
    for div in soup.find_all("div", class_=True):
        clase = div.get("class", [])
        texto_div = div.get_text(strip=True)[:100]
        if texto_div and len(texto_div) > 10:
            print(f"  .{' .'.join(clase)}: {texto_div}")

# Probar con ID conocido
explorar_votacion(88519)

# Probar con IDs recientes
print("\n" + "=" * 60)
print("Probando IDs recientes")
print("=" * 60)
for vid in [88520, 88521, 88515, 88500]:
    url = f"https://www.camara.cl/legislacion/sala_sesiones/votacion_detalle.aspx?prmIdVotacion={vid}"
    r = requests.get(url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(r.content, "html.parser")
    for tag in soup.find_all(["script","style"]):
        tag.decompose()
    texto = soup.get_text(separator=" ", strip=True)
    # Buscar señales de datos reales
    tiene_datos = any(k in texto for k in ["Aprobado","Rechazado","Si","No","Diputado"])
    print(f"  ID {vid}: {r.status_code} | {len(r.content)} bytes | tiene_datos={tiene_datos}")
    if tiene_datos:
        lineas = [l for l in texto.split() if l]
        print(f"    Muestra: {' '.join(lineas[:20])}")
