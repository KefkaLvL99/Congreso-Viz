import requests
from lxml import etree
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}

print("=" * 60)
print("1. Asistencia Cámara")
print("=" * 60)
# Necesita sesionId — probemos con sesiones recientes
urls_asistencia = [
    "https://opendata.camara.cl/camaradiputados/pages/sala/retornarSesionAsistencia.aspx?prmSesionId=4761",
    "https://opendata.camara.cl/camaradiputados/pages/sala/retornarSesionAsistencia.aspx?prmSesionId=4758",
    "https://opendata.camara.cl/camaradiputados/pages/sala/retornarSesionAsistencia.aspx?prmSesionId=4759",
]
parser = etree.XMLParser(recover=True)
for url in urls_asistencia:
    r = requests.get(url, headers=HEADERS, timeout=15)
    print(f"\n{url}")
    print(f"  HTTP: {r.status_code} | {len(r.content)} bytes")
    print(f"  {r.text[:300]}")

print("\n" + "=" * 60)
print("2. Últimas leyes publicadas")
print("=" * 60)
r2 = requests.get("https://www.leychile.cl/Consulta/obtxml?opt=3&cantidad=10", headers=HEADERS, timeout=15)
print(f"HTTP: {r2.status_code} | {len(r2.content)} bytes")
print(r2.text[:1000])
