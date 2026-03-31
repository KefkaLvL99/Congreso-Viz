import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}

# Probar con un diputado conocido (ID de ejemplo)
print("=" * 60)
print("CÁMARA — Gastos operacionales diputado")
print("=" * 60)

# ID 74 es un diputado de ejemplo que vimos en la búsqueda
url = "https://www.camara.cl/diputados/detalle/gastosoperacionales.aspx?prmId=74"
r = requests.get(url, headers=HEADERS, timeout=15)
print(f"HTTP: {r.status_code} | {len(r.content)} bytes")

soup = BeautifulSoup(r.content, "html.parser")
for tag in soup.find_all(["script","style"]):
    tag.decompose()

# Buscar tablas
tablas = soup.find_all("table")
print(f"Tablas: {len(tablas)}")
for i, t in enumerate(tablas[:3]):
    filas = t.find_all("tr")
    print(f"\n  Tabla {i+1}: {len(filas)} filas")
    for fila in filas[:5]:
        celdas = [td.get_text(strip=True) for td in fila.find_all(["td","th"])]
        if any(c for c in celdas):
            print(f"    {celdas}")

# Buscar divs con datos
texto = soup.get_text(separator="\n", strip=True)
lineas = [l for l in texto.split("\n") if len(l) > 5]
print(f"\nPrimeras 40 líneas:")
for l in lineas[:40]:
    print(f"  {l}")

print("\n" + "=" * 60)
print("SENADO — Gastos operacionales")
print("=" * 60)

url2 = "https://www.senado.cl/transparencia/gastos-operacionales-senadores"
r2 = requests.get(url2, headers=HEADERS, timeout=15)
print(f"HTTP: {r2.status_code} | {len(r2.content)} bytes")

soup2 = BeautifulSoup(r2.content, "html.parser")
for tag in soup2.find_all(["script","style"]):
    tag.decompose()

texto2 = soup2.get_text(separator="\n", strip=True)
lineas2 = [l for l in texto2.split("\n") if len(l) > 5]
print(f"Primeras 30 líneas:")
for l in lineas2[:30]:
    print(f"  {l}")

# Buscar links a archivos o datos
print("\nLinks relevantes:")
for a in soup2.find_all("a", href=True):
    href = a["href"]
    texto_a = a.get_text(strip=True)
    if any(k in href.lower() or k in texto_a.lower()
           for k in ["gasto", "xls", "csv", "pdf", "excel", "transparencia"]):
        print(f"  {texto_a} → {href}")
