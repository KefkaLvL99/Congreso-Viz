# ============================================================
# cargar_gastos_senado.py
# ============================================================
# Match preciso: apellido_paterno + apellido_materno + nombre
# ============================================================

import sys
import time
import requests
import unicodedata

sys.path.insert(0, ".")

from database import SessionLocal, engine
from models import Base, Senador, GastoSenador

HEADERS  = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}
URL_BASE = "https://web-back.senado.cl/api/transparency/expenses/senator-Operational-expenses"


def norm(texto: str) -> str:
    """Sin tildes, sin espacios extra, mayúsculas."""
    if not texto:
        return ""
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto.upper().strip())
        if unicodedata.category(c) != 'Mn'
    )


Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Mapa clave precisa → senador_id
# Clave: "APELLIDO_PATERNO|APELLIDO_MATERNO|NOMBRE" normalizado
senadores = db.query(Senador).all()
mapa = {}
for s in senadores:
    if not s.apellido_paterno:
        continue
    ap  = norm(s.apellido_paterno)
    am  = norm(s.apellido_materno or "")
    nom = norm(s.nombre or "")

    # Clave completa
    mapa[f"{ap}|{am}|{nom}"] = s.id
    # Clave sin nombre (por si el nombre varía)
    mapa[f"{ap}|{am}"] = s.id

print(f"Senadores vigentes: {len(senadores)}")
print(f"Claves generadas: {len(mapa)}")
print("\nEjemplos de claves:")
for k in list(mapa.keys())[:8]:
    print(f"  {k} → {mapa[k]}")

# Total páginas
r = requests.get(URL_BASE, headers=HEADERS, timeout=20)
meta       = r.json()["data"]["meta"]["pagination"]
total_pags = meta["pageCount"]
print(f"\nTotal páginas API: {total_pags}")

# Limpiar gastos existentes
db.query(GastoSenador).delete()
db.commit()
print("Gastos anteriores eliminados.\n")

total_insertados = 0
no_match         = set()

for pagina in range(1, total_pags + 1):
    url = f"{URL_BASE}?page={pagina}"
    try:
        r2        = requests.get(url, headers=HEADERS, timeout=20)
        registros = r2.json()["data"]["data"]

        for reg in registros:
            attr = reg["attributes"]
            ap   = norm(attr["appaterno"])
            am   = norm(attr.get("apmaterno") or "")
            nom  = norm(attr["nombre"])

            # Buscar match preciso
            senador_id = (
                mapa.get(f"{ap}|{am}|{nom}") or
                mapa.get(f"{ap}|{am}")
            )

            if senador_id:
                db.add(GastoSenador(
                    senador_id  = senador_id,
                    ano         = attr["ano"],
                    mes         = attr["mes"],
                    categoria   = attr["gastos_operacionales"],
                    monto       = attr["monto"],
                    appaterno   = attr["appaterno"],
                    apmaterno   = attr.get("apmaterno", ""),
                    nombre_api  = attr["nombre"],
                ))
                total_insertados += 1
            else:
                no_match.add(f"{attr['appaterno']} {attr.get('apmaterno','')} {attr['nombre']}")

        if pagina % 10 == 0:
            db.commit()
            print(f"  Página {pagina}/{total_pags} — insertados: {total_insertados}")

        time.sleep(0.3)

    except Exception as e:
        db.rollback()
        print(f"  ⚠️  Error página {pagina}: {e}")

db.commit()
db.close()

print(f"\n✅ Total gastos insertados: {total_insertados}")
print(f"Sin match (históricos): {len(no_match)}")
print(f"Muestra sin match: {sorted(no_match)[:10]}")
