import requests
import json

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}

# Probar el endpoint exacto que encontramos
bases = [
    "https://web-back.senado.cl",
    "https://www.senado.cl",
    "https://api.senado.cl",
]

endpoint = "/api/transparency/expenses/senator-Operational-expenses"

for base in bases:
    url = base + endpoint
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        print(f"\n{url}")
        print(f"HTTP: {r.status_code} | {len(r.content)} bytes")
        if r.status_code == 200:
            print(r.text[:1000])
        else:
            print(r.text[:200])
    except Exception as e:
        print(f"\n{url} → Error: {e}")

# Probar con parámetros
print("\n\nCon parámetros:")
params_probar = [
    "?anio=2024&mes=1",
    "?year=2024&month=1",
    "?anio=2024",
    "?periodo=2024-01",
]
for p in params_probar:
    url = f"https://web-back.senado.cl{endpoint}{p}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        print(f"\n{url}")
        print(f"HTTP: {r.status_code} | {len(r.content)} bytes | {r.text[:300]}")
    except Exception as e:
        print(f"Error: {e}")
