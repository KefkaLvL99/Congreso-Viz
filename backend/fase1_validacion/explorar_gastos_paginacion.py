import requests
import json

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}
BASE = "https://web-back.senado.cl/api/transparency/expenses/senator-Operational-expenses"

# Ver estructura completa del response
r = requests.get(BASE, headers=HEADERS, timeout=15)
data = r.json()

# Ver metadata
print("Claves raíz:", list(data.keys()))
print("Claves data:", list(data["data"].keys()) if isinstance(data["data"], dict) else "es lista")

if isinstance(data["data"], dict):
    print("\nMetadata:")
    for k, v in data["data"].items():
        if k != "data":
            print(f"  {k}: {v}")
    
    registros = data["data"]["data"]
    print(f"\nRegistros en este response: {len(registros)}")
    
    # Ver rango de fechas
    anios = set(r["attributes"]["ano"] for r in registros)
    meses = set(r["attributes"]["mes"] for r in registros)
    categorias = set(r["attributes"]["gastos_operacionales"] for r in registros)
    senadores = set(r["attributes"]["appaterno"] for r in registros)
    
    print(f"Años: {sorted(anios)}")
    print(f"Meses únicos: {sorted(meses)}")
    print(f"Categorías de gasto: {sorted(categorias)}")
    print(f"Total senadores únicos: {len(senadores)}")
    print(f"Algunos senadores: {sorted(senadores)[:10]}")

# Probar paginación
print("\n\nProbando paginación:")
params_pag = [
    "?page=1",
    "?page=2",
    "?page[number]=1&page[size]=100",
    "?pagination[page]=1",
    "?start=0&limit=100",
    "?offset=0&limit=100",
]
for p in params_pag:
    r2 = requests.get(BASE + p, headers=HEADERS, timeout=10)
    data2 = r2.json()
    regs = data2["data"]["data"] if isinstance(data2.get("data"), dict) else []
    primer_id = regs[0]["id"] if regs else "?"
    print(f"  {p}: {len(regs)} registros | primer_id={primer_id}")
