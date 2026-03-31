import requests
from lxml import etree

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}
BASE = "https://opendata.congreso.cl/wscamaradiputados.asmx"

# Sesiones de la legislatura actual (ID=58)
print("Sesiones legislatura 58 (actual):")
r = requests.get(f"{BASE}/getSesiones?prmLegislaturaID=58", headers=HEADERS, timeout=15)
print(f"HTTP: {r.status_code} | {len(r.content)} bytes")
print(r.text[:1000])

# Probar legislaturas anteriores
print("\nLegislaturas disponibles:")
r2 = requests.get(f"{BASE}/getLegislaturas", headers=HEADERS, timeout=15)
print(f"HTTP: {r2.status_code} | {len(r2.content)} bytes")
print(r2.text[:2000])
