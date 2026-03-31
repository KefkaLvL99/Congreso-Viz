# ============================================================
# scraper_gastos_senado.py
# ============================================================
# Carga gastos operacionales de senadores vigentes.
# Solo guarda registros de senadores que están en nuestra BD.
# ============================================================

import time
import requests
from datetime import datetime

HEADERS  = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}
URL_BASE = "https://web-back.senado.cl/api/transparency/expenses/senator-Operational-expenses"
PAUSA    = 0.3


def obtener_gastos_senadores_vigentes(senadores_vigentes: set,
                                       verbose: bool = True) -> list[dict]:
    """
    Descarga todos los gastos y filtra solo los de senadores vigentes.
    senadores_vigentes: set de apellidos paternos en mayúsculas para cruzar.
    """
    if verbose:
        print("  → Descargando gastos operacionales del Senado...")

    # Obtener total de páginas
    r = requests.get(URL_BASE, headers=HEADERS, timeout=20)
    r.raise_for_status()
    data       = r.json()
    meta       = data["data"]["meta"]["pagination"]
    total_pags = meta["pageCount"]
    total_regs = meta["total"]

    if verbose:
        print(f"    Total registros API: {total_regs} | Páginas: {total_pags}")

    gastos_vigentes = []
    no_encontrados  = set()

    for pagina in range(1, total_pags + 1):
        url = f"{URL_BASE}?page={pagina}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            r.raise_for_status()
            registros = r.json()["data"]["data"]

            for reg in registros:
                attr      = reg["attributes"]
                appaterno = attr["appaterno"].upper().strip()

                # Cruzar con senadores vigentes
                if appaterno in senadores_vigentes:
                    gastos_vigentes.append({
                        "ano":       attr["ano"],
                        "mes":       attr["mes"],
                        "categoria": attr["gastos_operacionales"],
                        "monto":     attr["monto"],
                        "appaterno": attr["appaterno"],
                        "apmaterno": attr.get("apmaterno", ""),
                        "nombre_api":attr["nombre"],
                    })
                else:
                    no_encontrados.add(appaterno)

            if verbose and pagina % 20 == 0:
                print(f"    Página {pagina}/{total_pags} — vigentes: {len(gastos_vigentes)}")

            time.sleep(PAUSA)

        except Exception as e:
            if verbose:
                print(f"    ⚠️  Error página {pagina}: {e}")

    if verbose:
        print(f"  ✅ Gastos de senadores vigentes: {len(gastos_vigentes)}")
        if no_encontrados:
            print(f"    (Senadores históricos ignorados: {len(no_encontrados)})")

    return gastos_vigentes


if __name__ == "__main__":
    # Prueba rápida con algunos apellidos conocidos
    vigentes = {"BIANCHI", "WALKER", "FLORES", "MACAYA", "NUNEZ", "NÚÑEZ",
                "PROVOSTE", "OSSANDÓN", "OSSANDON", "MOREIRA"}

    print("Prueba rápida (solo página 1):")
    r = requests.get(URL_BASE, headers=HEADERS, timeout=20)
    registros = r.json()["data"]["data"]
    encontrados = [reg for reg in registros
                   if reg["attributes"]["appaterno"].upper() in vigentes]
    print(f"Página 1: {len(registros)} registros | {len(encontrados)} de senadores vigentes")
    if encontrados:
        attr = encontrados[0]["attributes"]
        print(f"Ejemplo: {attr['nombre']} {attr['appaterno']} | "
              f"{attr['gastos_operacionales']} | ${attr['monto']:,} | {attr['ano']}/{attr['mes']}")
