# ============================================================
# FASE 1 - Explorador de estructura XML
# ============================================================
# Muestra el XML crudo de cada endpoint para entender
# cómo están organizados los datos antes de parsearlos.
# ============================================================

import requests
import xml.etree.ElementTree as ET
from lxml import etree   # parser tolerante para XML mal formado

# ── ENDPOINTS A EXPLORAR ─────────────────────────────────────
# Puedes comentar los que no quieras ver en un momento dado

ENDPOINTS = {
    "Legislatura actual (Cámara)":
        "https://opendata.camara.cl/pages/legislatura_actual.aspx",

    "Diputados vigentes (Cámara)":
        "https://opendata.camara.cl/pages/diputados_vigentes.aspx",

    "Sesiones de sala (Cámara) [parser tolerante]":
        "https://opendata.camara.cl/pages/sesiones.aspx",

    "Comisiones vigentes (Cámara)":
        "https://opendata.camara.cl/pages/comisiones_vigentes.aspx",

    "Senadores vigentes (Senado)":
        "https://tramitacion.senado.cl/wspublico/senadores_vigentes.php",

    "Comisiones vigentes (Senado)":
        "https://tramitacion.senado.cl/wspublico/comisiones.php",
}

# Cuántos registros mostrar por endpoint (para no inundar la terminal)
MUESTRA_MAX = 2

# ── FUNCIONES ────────────────────────────────────────────────

def explorar_con_etree(contenido):
    """Parser estándar — para XML bien formado."""
    root = ET.fromstring(contenido)
    return root

def explorar_con_lxml(contenido):
    """Parser tolerante — para XML con caracteres especiales o errores menores."""
    parser = etree.XMLParser(recover=True)
    root = etree.fromstring(contenido, parser=parser)
    return root

def imprimir_arbol(nodo, nivel=0, max_nivel=3):
    """
    Imprime recursivamente la estructura del XML con indentación.
    Solo baja hasta max_nivel para no mostrar demasiado.
    """
    indent = "  " * nivel
    texto = nodo.text.strip() if nodo.text and nodo.text.strip() else ""
    atributos = dict(nodo.attrib) if nodo.attrib else {}

    # Construye la línea de descripción del nodo
    descripcion = f"{indent}<{nodo.tag}>"
    if atributos:
        descripcion += f"  atributos: {atributos}"
    if texto:
        # Trunca textos muy largos
        descripcion += f"  → '{texto[:60]}'" + ("..." if len(texto) > 60 else "")

    print(descripcion)

    if nivel < max_nivel:
        for hijo in nodo:
            imprimir_arbol(hijo, nivel + 1, max_nivel)

def explorar_endpoint(nombre, url):
    print("\n" + "═" * 60)
    print(f"  {nombre}")
    print(f"  {url}")
    print("═" * 60)

    try:
        r = requests.get(url, timeout=15)
        contenido = r.content

        # ── Intenta parser estándar primero ──
        usar_lxml = "tolerante" in nombre.lower()

        if usar_lxml:
            print("  ⚠️  Usando parser tolerante (lxml) por XML mal formado\n")
            root = explorar_con_lxml(contenido)
            # lxml usa bytes, necesitamos iterar distinto
            hijos = list(root)
        else:
            root = explorar_con_etree(contenido)
            hijos = list(root)

        print(f"  Nodo raíz   : <{root.tag}>")
        print(f"  Hijos directos: {len(hijos)}")

        # ── Muestra la estructura del árbol ──
        print("\n  ESTRUCTURA DEL XML:")
        print("  " + "─" * 40)
        imprimir_arbol(root, nivel=1, max_nivel=4)

        # ── Muestra registros de muestra ──
        print(f"\n  PRIMEROS {MUESTRA_MAX} REGISTRO(S) COMPLETO(S):")
        print("  " + "─" * 40)
        for i, hijo in enumerate(hijos[:MUESTRA_MAX]):
            print(f"\n  Registro #{i+1}:")
            imprimir_arbol(hijo, nivel=2, max_nivel=5)

    except Exception as e:
        print(f"  ❌ Error: {e}")


# ── EJECUCIÓN PRINCIPAL ──────────────────────────────────────

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   Explorador XML - APIs Congreso Nacional Chile          ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print("  Objetivo: entender la estructura de cada respuesta XML\n")

    for nombre, url in ENDPOINTS.items():
        explorar_endpoint(nombre, url)

    print("\n\n  Exploración completada.")
    print("  Revisa la estructura de cada endpoint antes de continuar.")
