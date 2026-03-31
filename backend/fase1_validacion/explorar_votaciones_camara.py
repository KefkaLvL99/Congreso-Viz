# ============================================================
# explorar_votaciones_camara.py
# ============================================================
# Explora los endpoints de votaciones de la Cámara de Diputados
# ============================================================

import requests
from lxml import etree

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}
TIMEOUT = 15

def get_xml(url):
    print(f"\nURL: {url}")
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    print(f"HTTP: {r.status_code} | {len(r.content)} bytes | Content-Type: {r.headers.get('Content-Type','?')}")
    try:
        parser = etree.XMLParser(recover=True)
        root = etree.fromstring(r.content, parser=parser)
        print(f"Nodo raíz: <{root.tag}> | Hijos: {len(list(root))}")
        return root, r
    except Exception as e:
        print(f"No es XML: {e}")
        print(f"Primeros 300 chars: {r.text[:300]}")
        return None, r

def imprimir(nodo, nivel=0, max_nivel=4):
    indent = "  " * nivel
    texto = nodo.text.strip() if nodo.text and nodo.text.strip() else ""
    print(f"{indent}<{nodo.tag}>" + (f"  → '{texto[:60]}'" if texto else ""))
    if nivel < max_nivel:
        for hijo in nodo:
            imprimir(hijo, nivel+1, max_nivel)

print("=" * 60)
print("ENDPOINT 1 — Votaciones por año (Cámara)")
print("=" * 60)
root, r = get_xml("https://opendata.camara.cl/camaradiputados/v1/sala.votaciones?anyo=2025")
if root is not None:
    hijos = list(root)
    print(f"\nPrimeros 2 registros:")
    for h in hijos[:2]:
        imprimir(h, nivel=1, max_nivel=4)

print("\n" + "=" * 60)
print("ENDPOINT 2 — Votaciones año (formato alternativo)")
print("=" * 60)
root2, r2 = get_xml("https://opendata.camara.cl/camaradiputados/v1/sala.votaciones?prmAnyo=2025")
if root2 is not None:
    for h in list(root2)[:2]:
        imprimir(h, nivel=1, max_nivel=4)

print("\n" + "=" * 60)
print("ENDPOINT 3 — Detalle votación (ID de ejemplo)")
print("=" * 60)
root3, r3 = get_xml("https://opendata.camara.cl/camaradiputados/v1/sala.votacion_detalle?prmVotacionId=1")
if root3 is not None:
    for h in list(root3)[:2]:
        imprimir(h, nivel=1, max_nivel=5)

print("\n" + "=" * 60)
print("ENDPOINT 4 — Votacion detalle página aspx")
print("=" * 60)
root4, r4 = get_xml("https://opendata.camara.cl/pages/votacion_detalle.aspx?prmVotacionId=1")
if root4 is not None:
    for h in list(root4)[:2]:
        imprimir(h, nivel=1, max_nivel=5)
