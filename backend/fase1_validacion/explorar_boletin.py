# ============================================================
# explorar_boletin.py
# ============================================================
# Explora qué información está disponible en la página
# del boletín del Senado para un proyecto específico.
# ============================================================

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}

# Probamos con el proyecto de desalinización (boletín 11608-09)
# que ya tenemos en la BD
BOLETIN = "11608-09"
url = f"https://www.senado.cl/appsenado/templates/tramitacion/index.php?boletin_ini={BOLETIN}"

print(f"Consultando: {url}")
r = requests.get(url, headers=HEADERS, timeout=20)
print(f"HTTP: {r.status_code} | {len(r.content)} bytes\n")

soup = BeautifulSoup(r.content, "html.parser")
for tag in soup.find_all(["script", "style"]):
    tag.decompose()

texto = soup.get_text(separator="\n", strip=True)
lineas = [l for l in texto.split("\n") if len(l) > 10]

print(f"Líneas de contenido: {len(lineas)}")
print("\nPrimeras 60 líneas:")
for l in lineas[:60]:
    print(f"  {l}")

# Buscar divs con contenido relevante
print("\n\nDivs con contenido:")
for div in soup.find_all("div", class_=True):
    clase = " ".join(div.get("class", []))
    texto_div = div.get_text(strip=True)
    if len(texto_div) > 100:
        print(f"\n.{clase}:")
        print(f"  {texto_div[:200]}")
