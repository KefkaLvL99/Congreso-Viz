import requests
import json

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}

# Explorar el nodo senado_api que encontramos
print("1. Nodo senado_api:")
r = requests.get(
    "https://web-back.senado.cl/jsonapi/node/senado_api/87da6bc2-566d-4212-8b3d-be19d7057686",
    headers=HEADERS, timeout=15
)
print(f"HTTP: {r.status_code} | {len(r.content)} bytes")
if r.status_code == 200:
    data = r.json()
    print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])

# Probar endpoints de gastos directamente
print("\n2. Endpoints de gastos:")
urls = [
    "https://web-back.senado.cl/api/gastos-operacionales",
    "https://web-back.senado.cl/api/gastos-operacionales?anio=2024",
    "https://web-back.senado.cl/transparencia/gastos-operacionales-senadores/api",
    "https://web-back.senado.cl/api/transparencia/gastos",
    "https://www.senado.cl/api/gastos-operacionales",
]
for url in urls:
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        print(f"  {url}")
        print(f"  HTTP: {r.status_code} | {len(r.content)} bytes | {r.text[:200]}\n")
    except Exception as e:
        print(f"  {url} → Error: {e}\n")
