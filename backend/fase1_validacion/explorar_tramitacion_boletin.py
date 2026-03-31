import requests
from bs4 import BeautifulSoup
import re

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}

# Probar la URL que mencionas
url = "https://tramitacion.senado.cl/appsenado/templates/tramitacion/index.php?boletin_ini=11608-09"
r = requests.get(url, headers=HEADERS, timeout=20)
print(f"HTTP: {r.status_code} | {len(r.content)} bytes")

soup = BeautifulSoup(r.content, "html.parser")

# Buscar tablas
tablas = soup.find_all("table")
print(f"Tablas: {len(tablas)}")

# Buscar datos de votaciones en el HTML
for tabla in tablas[:3]:
    filas = tabla.find_all("tr")
    print(f"\nTabla con {len(filas)} filas:")
    for fila in filas[:5]:
        celdas = [td.get_text(strip=True) for td in fila.find_all(["td","th"])]
        if any(c for c in celdas):
            print(f"  {celdas}")

# Buscar APIs en scripts
apis = re.findall(r'(https?://[^\s"\']+)', r.text)
apis_senado = [a for a in apis if 'senado' in a and ('api' in a or 'json' in a or 'xml' in a or 'wspublico' in a)]
print(f"\nAPIs encontradas:")
for a in set(apis_senado[:10]):
    print(f"  {a}")

# Buscar fetch/ajax
fetches = re.findall(r'(?:fetch|ajax|XMLHttpRequest|axios)[^;]{0,200}', r.text)
print(f"\nFetch/Ajax calls:")
for f in fetches[:5]:
    print(f"  {f[:150]}")

# Buscar datos JSON embebidos
scripts = soup.find_all("script")
for s in scripts:
    if s.string and ('votacion' in s.string.lower() or 'sesion' in s.string.lower()):
        print(f"\nScript con datos relevantes ({len(s.string)} chars):")
        print(s.string[:500])
