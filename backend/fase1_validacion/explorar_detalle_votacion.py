# ============================================================
# explorar_detalle_votacion.py
# ============================================================
# Explora el nodo DETALLE_VOTACION para ver cómo están
# registrados los votos individuales de cada parlamentario.
# ============================================================

import requests
from lxml import etree
from datetime import datetime, timedelta

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0)"}

# Consultar proyectos recientes
fecha = (datetime.now() - timedelta(days=7)).strftime("%d/%m/%Y")
url = f"https://tramitacion.senado.cl/wspublico/tramitacion.php?fecha={fecha}"

print(f"Consultando: {url}")
r = requests.get(url, timeout=30, headers=HEADERS)
print(f"HTTP: {r.status_code} | {len(r.content)} bytes\n")

parser = etree.XMLParser(recover=True)
root = etree.fromstring(r.content, parser=parser)

# Buscar la primera votación que tenga DETALLE_VOTACION con contenido
encontrado = False
for proyecto in root.iter("proyecto"):
    boletin_nodo = proyecto.find("descripcion/boletin")
    titulo_nodo  = proyecto.find("descripcion/titulo")
    boletin = boletin_nodo.text.strip() if boletin_nodo is not None and boletin_nodo.text else "?"
    titulo  = titulo_nodo.text.strip()[:60]  if titulo_nodo  is not None and titulo_nodo.text  else "?"

    nodo_vots = proyecto.find("votaciones")
    if nodo_vots is None:
        continue

    for vot in nodo_vots.iter("votacion"):
        detalle = vot.find("DETALLE_VOTACION")
        if detalle is None:
            continue

        hijos = list(detalle)
        if len(hijos) == 0:
            continue

        # Encontramos una votación con detalle
        print(f"✅ Votación con detalle encontrada:")
        print(f"   Boletín : {boletin}")
        print(f"   Título  : {titulo}")

        tema = vot.find("TEMA")
        fecha_vot = vot.find("FECHA")
        si   = vot.find("SI")
        no   = vot.find("NO")
        print(f"   Fecha   : {fecha_vot.text if fecha_vot is not None else '?'}")
        print(f"   SI/NO   : {si.text if si is not None else '?'} / {no.text if no is not None else '?'}")
        print(f"\n   Estructura de DETALLE_VOTACION ({len(hijos)} hijos):")

        # Mostrar estructura completa del detalle
        def imprimir(nodo, nivel=0):
            indent = "  " * nivel
            texto = nodo.text.strip() if nodo.text and nodo.text.strip() else ""
            texto_corto = texto[:50] + "..." if len(texto) > 50 else texto
            linea = f"{indent}<{nodo.tag}>"
            if texto_corto:
                linea += f"  → '{texto_corto}'"
            print(linea)
            for hijo in nodo:
                imprimir(hijo, nivel + 1)

        imprimir(detalle, nivel=2)

        # Mostrar primeros 3 registros individuales
        print(f"\n   Primeros 3 votos individuales:")
        for i, hijo in enumerate(hijos[:3]):
            print(f"\n   Voto #{i+1}:")
            imprimir(hijo, nivel=3)

        encontrado = True
        break

    if encontrado:
        break

if not encontrado:
    print("No se encontró DETALLE_VOTACION con contenido en los últimos 7 días")
    print("Probando con 30 días atrás...")

    fecha2 = (datetime.now() - timedelta(days=30)).strftime("%d/%m/%Y")
    url2 = f"https://tramitacion.senado.cl/wspublico/tramitacion.php?fecha={fecha2}"
    r2 = requests.get(url2, timeout=30, headers=HEADERS)
    root2 = etree.fromstring(r2.content, parser=parser)

    for proyecto in root2.iter("proyecto"):
        nodo_vots = proyecto.find("votaciones")
        if nodo_vots is None:
            continue
        for vot in nodo_vots.iter("votacion"):
            detalle = vot.find("DETALLE_VOTACION")
            if detalle is None:
                continue
            hijos = list(detalle)
            if len(hijos) > 0:
                print(f"\n✅ Encontrado en consulta -30d")
                def imprimir(nodo, nivel=0):
                    indent = "  " * nivel
                    texto = nodo.text.strip() if nodo.text and nodo.text.strip() else ""
                    texto_corto = texto[:50] + "..." if len(texto) > 50 else texto
                    print(f"{indent}<{nodo.tag}>  → '{texto_corto}'" if texto_corto else f"{indent}<{nodo.tag}>")
                    for hijo in nodo:
                        imprimir(hijo, nivel + 1)
                imprimir(detalle, nivel=1)
                for i, hijo in enumerate(hijos[:3]):
                    print(f"\n  Voto #{i+1}:")
                    imprimir(hijo, nivel=2)
                break
        else:
            continue
        break
