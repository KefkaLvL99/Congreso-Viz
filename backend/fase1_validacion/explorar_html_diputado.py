# ============================================================
# explorar_html_diputado.py
# ============================================================
# Muestra el HTML crudo de la sección de datos del diputado
# para identificar los tags y clases exactas a parsear.
# ============================================================

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0; datos publicos)"
}

url = "https://www.camara.cl/diputados/detalle/mociones.aspx?prmID=1009"
r = requests.get(url, headers=HEADERS, timeout=20)
soup = BeautifulSoup(r.content, "html.parser")

# Buscar el contenedor principal de datos del diputado
# Probamos diferentes selectores comunes
print("── Buscando contenedor principal ──")

for selector in ["#contenido", "#main", ".diputado", ".perfil",
                 ".parlamentario", "#ctl00_ContentPlaceHolder1",
                 ".datos-diputado", ".info-parlamentario"]:
    elemento = soup.select_one(selector)
    if elemento:
        print(f"\n✅ Encontrado: {selector}")
        print(elemento.get_text(separator="\n", strip=True)[:500])
        break

# Buscar directamente los spans/divs que contienen Región y Partido
print("\n\n── Contexto HTML alrededor de Región ──")
for tag in soup.find_all(string=lambda t: t and "Región:" in t):
    padre = tag.parent
    abuelo = padre.parent if padre else None
    if abuelo:
        print(abuelo.prettify()[:600])
        break

print("\n── Contexto HTML alrededor de Partido ──")
for tag in soup.find_all(string=lambda t: t and "Partido:" in t):
    padre = tag.parent
    abuelo = padre.parent if padre else None
    if abuelo:
        print(abuelo.prettify()[:600])
        break

print("\n── Contexto HTML alrededor de Email ──")
for tag in soup.find_all(string=lambda t: t and "Email" in t):
    padre = tag.parent
    abuelo = padre.parent if padre else None
    if abuelo:
        print(abuelo.prettify()[:400])
        break

# Mostrar todos los divs con id que contengan datos
print("\n── Divs con ID relevantes ──")
for div in soup.find_all(["div", "section"], id=True):
    texto = div.get_text(strip=True)
    if any(k in texto for k in ["Región", "Partido", "Distrito"]):
        print(f"\nID: {div.get('id')}")
        print(div.prettify()[:800])
        break
