import requests
from lxml import etree
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}

urls = [
    "https://opendata.congreso.cl/wscamaradiputados.asmx/getVotacionesXAnno?prmAnno=2015",
    "https://opendata.congreso.cl/wscamaradiputados.asmx/getVotaciones?prmAnno=2015",
    "https://opendata.senado.cl/api/votaciones?anio=2015",
    "https://opendata.senado.cl/api/votaciones?fecha=2015",
    "https://tramitacion.senado.cl/wspublico/sesiones.php?anio=2015",
    "https://tramitacion.senado.cl/wspublico/sesiones.php",
]

for url in urls:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        print(f"\n{url}")
        print(f"  HTTP: {r.status_code} | {len(r.content)} bytes")
        print(f"  Primeros 300 chars: {r.text[:300]}")
    except Exception as e:
        print(f"\n{url}")
        print(f"  Error: {e}")
