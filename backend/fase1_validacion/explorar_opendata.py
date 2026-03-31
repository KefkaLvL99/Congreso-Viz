import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}

print("=" * 60)
print("1. camara.cl/transparencia/datosAbiertos.aspx")
print("=" * 60)
r = requests.get("https://www.camara.cl/transparencia/datosAbiertos.aspx", headers=HEADERS, timeout=15)
soup = BeautifulSoup(r.content, "html.parser")
for tag in soup.find_all(["script","style"]): tag.decompose()

# Buscar links a APIs o archivos de datos
print("\nLinks a datos:")
for a in soup.find_all("a", href=True):
    href = a["href"]
    texto = a.get_text(strip=True)
    if any(k in href.lower() or k in texto.lower() 
           for k in ["api", "xml", "json", "csv", "datos", "ws", "service", "open", "votacion", "asistencia"]):
        print(f"  {texto[:60]} → {href}")

print("\nTexto relevante:")
texto = soup.get_text(separator="\n", strip=True)
lineas = [l for l in texto.split("\n") if len(l) > 10]
for l in lineas[:40]:
    print(f"  {l}")

print("\n" + "=" * 60)
print("2. opendata.congreso.cl")
print("=" * 60)
r2 = requests.get("https://opendata.congreso.cl/", headers=HEADERS, timeout=15)
soup2 = BeautifulSoup(r2.content, "html.parser")
for tag in soup2.find_all(["script","style"]): tag.decompose()

print("\nLinks a datos:")
for a in soup2.find_all("a", href=True):
    href = a["href"]
    texto = a.get_text(strip=True)
    if texto and len(texto) > 3:
        print(f"  {texto[:60]} → {href}")

print("\nTexto:")
texto2 = soup2.get_text(separator="\n", strip=True)
lineas2 = [l for l in texto2.split("\n") if len(l) > 10]
for l in lineas2[:40]:
    print(f"  {l}")
