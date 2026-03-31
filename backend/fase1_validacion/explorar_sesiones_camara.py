import requests
from lxml import etree

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}
BASE = "https://opendata.congreso.cl/wscamaradiputados.asmx"

# Primero obtener la legislatura actual
print("1. Legislatura actual:")
r = requests.get(f"{BASE}/getLegislaturaActual", headers=HEADERS, timeout=15)
print(f"   HTTP: {r.status_code} | {len(r.content)} bytes")
print(f"   {r.text[:500]}")

# Obtener sesiones de 2026
print("\n2. Sesiones 2026:")
r2 = requests.get(f"{BASE}/getSesiones?prmAnno=2026", headers=HEADERS, timeout=15)
print(f"   HTTP: {r2.status_code} | {len(r2.content)} bytes")
print(f"   {r2.text[:800]}")

# Intentar con legislatura
print("\n3. Sesiones por legislatura:")
r3 = requests.get(f"{BASE}/getSesiones?prmLegislaturaId=1", headers=HEADERS, timeout=15)
print(f"   HTTP: {r3.status_code} | {len(r3.content)} bytes")
print(f"   {r3.text[:500]}")

# Detalle de sesión
print("\n4. Detalle sesión ID=1:")
r4 = requests.get(f"{BASE}/getSesionDetalle?prmSesionId=1", headers=HEADERS, timeout=15)
print(f"   HTTP: {r4.status_code} | {len(r4.content)} bytes")
print(f"   {r4.text[:800]}")
