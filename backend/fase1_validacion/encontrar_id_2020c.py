import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}

# Página de votaciones del proyecto
url = "https://www.camara.cl/legislacion/sala_sesiones/votaciones.aspx?prmID=13917&prmBOLETIN=13377-13"
r = requests.get(url, headers=HEADERS, timeout=15)
print(f"HTTP: {r.status_code} | {len(r.content)} bytes")

soup = BeautifulSoup(r.content, "html.parser")
for tag in soup.find_all(["script","style"]):
    tag.decompose()

# Buscar links con prmIdVotacion
for a in soup.find_all("a", href=True):
    if "prmIdVotacion" in a["href"] or "IdVotacion" in a["href"]:
        print(f"  {a['href']} → {a.get_text(strip=True)[:60]}")

# Buscar en el texto cualquier número de votacion
import re
texto = r.text
ids = re.findall(r'prmIdVotacion=(\d+)', texto)
print(f"\nIDs de votación encontrados: {ids[:20]}")

# También probar con boletín directamente en la pagina de votaciones
url2 = "https://www.camara.cl/legislacion/sala_sesiones/votacion_detalle.aspx?prmBoletin=13377-13"
r2 = requests.get(url2, headers=HEADERS, timeout=15)
print(f"\nPor boletín HTTP: {r2.status_code} | {len(r2.content)} bytes")
ids2 = re.findall(r'prmIdVotacion=(\d+)', r2.text)
print(f"IDs encontrados: {ids2[:10]}")
