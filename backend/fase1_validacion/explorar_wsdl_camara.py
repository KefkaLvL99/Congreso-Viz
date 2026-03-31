import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}

# Ver WSDL completo para listar todos los métodos
r = requests.get(
    "https://opendata.congreso.cl/wscamaradiputados.asmx?WSDL",
    headers=HEADERS, timeout=15
)
print(f"HTTP: {r.status_code} | {len(r.content)} bytes")

# Extraer nombres de operaciones del WSDL
soup = BeautifulSoup(r.content, "xml")
operaciones = soup.find_all("operation")
print(f"\nMétodos disponibles ({len(operaciones)}):")
for op in operaciones:
    print(f"  {op.get('name')}")

# También buscar en la página principal del webservice
r2 = requests.get(
    "https://opendata.congreso.cl/wscamaradiputados.asmx",
    headers=HEADERS, timeout=15
)
soup2 = BeautifulSoup(r2.content, "html.parser")
for tag in soup2.find_all(["script","style"]):
    tag.decompose()
print(f"\nPágina principal webservice:")
print(soup2.get_text(separator="\n", strip=True)[:2000])
