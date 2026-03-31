import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}

url = "https://www.camara.cl/legislacion/sala_sesiones/asistencia_resumen.aspx"
r = requests.get(url, headers=HEADERS, timeout=20)
print(f"HTTP: {r.status_code} | {len(r.content)} bytes")

soup = BeautifulSoup(r.content, "html.parser")
for tag in soup.find_all(["script","style"]):
    tag.decompose()

# Ver estructura general
print("\nTablas encontradas:", len(soup.find_all("table")))
print("Forms encontrados:", len(soup.find_all("form")))
print("Selects encontrados:", len(soup.find_all("select")))

# Ver selects (filtros disponibles)
for sel in soup.find_all("select"):
    print(f"\n  Select name='{sel.get('name')}' id='{sel.get('id')}':")
    for opt in sel.find_all("option")[:10]:
        print(f"    value='{opt.get('value')}' → {opt.get_text(strip=True)}")

# Ver texto principal
texto = soup.get_text(separator="\n", strip=True)
lineas = [l for l in texto.split("\n") if len(l) > 5]
print(f"\nPrimeras 50 líneas:")
for l in lineas[:50]:
    print(f"  {l}")

# Ver tablas con datos
for i, tabla in enumerate(soup.find_all("table")):
    filas = tabla.find_all("tr")
    if len(filas) > 2:
        print(f"\nTabla {i+1}: {len(filas)} filas")
        for fila in filas[:5]:
            celdas = [td.get_text(strip=True) for td in fila.find_all(["td","th"])]
            if any(c for c in celdas):
                print(f"  {celdas}")
