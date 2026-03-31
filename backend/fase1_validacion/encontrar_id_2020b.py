import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}

# Buscar votaciones del boletín 13377-13
url = "https://opendata.congreso.cl/wscamaradiputados.asmx/getVotaciones_Boletin?prmBoletin=13377-13"
r = requests.get(url, headers=HEADERS, timeout=15)
print(f"HTTP: {r.status_code} | {len(r.content)} bytes")
print(r.text[:1000])

# También buscar directamente en la página de votaciones de ese proyecto
url2 = "https://www.camara.cl/legislacion/proyectosdeley/tramitacion.aspx?prmID=13917&prmBOLETIN=13377-13"
r2 = requests.get(url2, headers=HEADERS, timeout=15)
soup = BeautifulSoup(r2.content, "html.parser")

# Buscar links a votaciones
for a in soup.find_all("a", href=True):
    if "votacion" in a["href"].lower():
        print(f"Link votación: {a['href']} → {a.get_text(strip=True)[:50]}")
