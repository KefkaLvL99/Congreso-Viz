import requests
from lxml import etree
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}

print("=" * 60)
print("CÁMARA DE DIPUTADOS — Asistencia")
print("=" * 60)

urls_camara = [
    "https://opendata.congreso.cl/wscamaradiputados.asmx/getAsistencia?prmAnno=2026",
    "https://opendata.congreso.cl/wscamaradiputados.asmx/getAsistenciaDiputado?prmDiputadoId=1&prmAnno=2026",
    "https://www.camara.cl/diputados/diputados.aspx",
    "https://www.camara.cl/sala/asistencia.aspx",
    "https://www.camara.cl/sala/asistencia.aspx?prmAnno=2026",
]

for url in urls_camara:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.content, "html.parser")
        for tag in soup.find_all(["script","style"]):
            tag.decompose()
        texto = soup.get_text(separator=" ", strip=True)[:300]
        print(f"\n{url}")
        print(f"  HTTP: {r.status_code} | {len(r.content)} bytes")
        print(f"  Contenido: {texto[:200]}")
    except Exception as e:
        print(f"\n{url} → Error: {e}")

print("\n" + "=" * 60)
print("SENADO — Asistencia")
print("=" * 60)

urls_senado = [
    "https://tramitacion.senado.cl/wspublico/asistencia.php",
    "https://tramitacion.senado.cl/wspublico/asistencia.php?anio=2026",
    "https://tramitacion.senado.cl/wspublico/asistencia.php?fecha=01/03/2026",
    "https://www.senado.cl/senadoras-y-senadores/asistencia",
]

for url in urls_senado:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.content, "html.parser")
        for tag in soup.find_all(["script","style"]):
            tag.decompose()
        texto = soup.get_text(separator=" ", strip=True)[:300]
        print(f"\n{url}")
        print(f"  HTTP: {r.status_code} | {len(r.content)} bytes")
        print(f"  Contenido: {texto[:200]}")
    except Exception as e:
        print(f"\n{url} → Error: {e}")
