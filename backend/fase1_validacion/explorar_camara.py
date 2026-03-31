# ============================================================
# FASE 1 - Explorador de endpoints con parámetros (Cámara)
# ============================================================
# Los endpoints de la Cámara requieren parámetros en la URL.
# Este script primero obtiene la legislatura actual, luego
# usa ese dato para consultar los demás endpoints.
# ============================================================

import requests
import xml.etree.ElementTree as ET
from lxml import etree

TIMEOUT = 15

# ── FUNCIONES UTILITARIAS ────────────────────────────────────

def get_xml(url, usar_lxml=False):
    """Descarga y parsea XML de una URL. Retorna (root, raw_text) o (None, error)."""
    try:
        r = requests.get(url, timeout=TIMEOUT)
        if r.status_code != 200:
            return None, f"HTTP {r.status_code}"
        if usar_lxml:
            parser = etree.XMLParser(recover=True)
            root = etree.fromstring(r.content, parser=parser)
        else:
            root = ET.fromstring(r.content)
        return root, r.text
    except ET.ParseError as e:
        return None, f"XML inválido: {e}"
    except Exception as e:
        return None, f"Error: {e}"

def imprimir_nodo(nodo, nivel=0, max_nivel=4, usar_lxml=False):
    """Imprime árbol XML con indentación."""
    indent = "  " * nivel
    texto = nodo.text.strip() if nodo.text and nodo.text.strip() else ""
    texto_corto = texto[:60] + "..." if len(texto) > 60 else texto
    linea = f"{indent}<{nodo.tag}>"
    if texto_corto:
        linea += f"  → '{texto_corto}'"
    print(linea)
    if nivel < max_nivel:
        for hijo in nodo:
            imprimir_nodo(hijo, nivel + 1, max_nivel, usar_lxml)

def seccion(titulo):
    print("\n" + "═" * 60)
    print(f"  {titulo}")
    print("═" * 60)

# ── PASO 1: Obtener legislatura actual ───────────────────────

seccion("PASO 1 — Legislatura actual")

URL_LEGISLATURA = "https://opendata.camara.cl/pages/legislatura_actual.aspx"
root, raw = get_xml(URL_LEGISLATURA)

id_legislatura = None

if root is None:
    print(f"  ❌ Error: {raw}")
else:
    print("  Estructura completa del XML:")
    imprimir_nodo(root, nivel=1, max_nivel=5)

    # Busca el tag que contenga el ID de la legislatura
    # Probamos nombres comunes
    for tag in ["Id", "ID", "id", "NumeroLegislatura", "NUMERO", "Numero"]:
        nodo = root.find(f".//{tag}")
        if nodo is not None and nodo.text:
            id_legislatura = nodo.text.strip()
            print(f"\n  ✅ ID legislatura encontrado en <{tag}>: {id_legislatura}")
            break

    if not id_legislatura:
        print("\n  ⚠️  No se encontró ID automáticamente.")
        print("  XML crudo (primeros 800 caracteres):")
        print(raw[:800])

# ── PASO 2: Diputados vigentes ───────────────────────────────

seccion("PASO 2 — Diputados vigentes (con y sin parámetro)")

# Intento 1: sin parámetro
print("\n  [A] Sin parámetro:")
root_a, _ = get_xml("https://opendata.camara.cl/pages/diputados_vigentes.aspx")
if root_a is not None:
    hijos = list(root_a)
    print(f"  Nodo raíz: <{root_a.tag}> | Hijos: {len(hijos)}")
    imprimir_nodo(root_a, nivel=1, max_nivel=3)

# Intento 2: con legislatura si la tenemos
if id_legislatura:
    print(f"\n  [B] Con ?prmNumeroLegislatura={id_legislatura}:")
    url_b = f"https://opendata.camara.cl/pages/diputados_vigentes.aspx?prmNumeroLegislatura={id_legislatura}"
    root_b, _ = get_xml(url_b)
    if root_b is not None:
        hijos_b = list(root_b)
        print(f"  Nodo raíz: <{root_b.tag}> | Hijos: {len(hijos_b)}")
        imprimir_nodo(root_b, nivel=1, max_nivel=4)

# Intento 3: con prmPeriodo (otro parámetro común en la Cámara)
print(f"\n  [C] Con ?prmPeriodo=2022-2026:")
url_c = "https://opendata.camara.cl/pages/diputados_vigentes.aspx?prmPeriodo=2022-2026"
root_c, _ = get_xml(url_c)
if root_c is not None:
    hijos_c = list(root_c)
    print(f"  Nodo raíz: <{root_c.tag}> | Hijos: {len(hijos_c)}")
    imprimir_nodo(root_c, nivel=1, max_nivel=3)

# ── PASO 3: Sesiones con parser tolerante ───────────────────

seccion("PASO 3 — Sesiones de sala (parser tolerante lxml)")

URL_SESIONES = "https://opendata.camara.cl/pages/sesiones.aspx"
r = requests.get(URL_SESIONES, timeout=TIMEOUT)

print(f"  HTTP: {r.status_code}")
print(f"  Encoding declarado: {r.encoding}")
print(f"  Tamaño respuesta: {len(r.content)} bytes")

# Intentamos con lxml recover=True
parser = etree.XMLParser(recover=True)
try:
    root_ses = etree.fromstring(r.content, parser=parser)
    hijos_ses = list(root_ses)
    print(f"\n  ✅ lxml pudo parsear. Nodo raíz: <{root_ses.tag}> | Hijos: {len(hijos_ses)}")

    print("\n  Estructura:")
    imprimir_nodo(root_ses, nivel=1, max_nivel=4, usar_lxml=True)

    print(f"\n  Primeros 2 registros:")
    for i, hijo in enumerate(hijos_ses[:2]):
        print(f"\n  Registro #{i+1}:")
        imprimir_nodo(hijo, nivel=2, max_nivel=5, usar_lxml=True)

except Exception as e:
    print(f"  ❌ lxml también falló: {e}")
    # Mostramos el raw alrededor de la línea 47 donde falló
    lineas = r.text.split("\n")
    print(f"\n  Contexto del error (líneas 44-50):")
    for i, linea in enumerate(lineas[43:50], start=44):
        print(f"  L{i:03d}: {linea}")

# ── PASO 4: Votaciones por boletín (ejemplo) ─────────────────

seccion("PASO 4 — Votaciones por boletín (ejemplo con boletín conocido)")

# Usamos un boletín conocido reciente como ejemplo
BOLETIN_EJEMPLO = "16456-07"
url_vot = f"https://opendata.camara.cl/pages/votacion_boletin.aspx?prmNumeroBoletín={BOLETIN_EJEMPLO}"
url_vot2 = f"https://opendata.camara.cl/pages/votacion_boletin.aspx?prmNumeroBoletin={BOLETIN_EJEMPLO}"

print(f"\n  Consultando boletín: {BOLETIN_EJEMPLO}")

for intento, url in enumerate([url_vot, url_vot2], 1):
    root_v, raw_v = get_xml(url)
    if root_v is not None:
        hijos_v = list(root_v)
        print(f"\n  ✅ Intento {intento} funcionó. Nodo: <{root_v.tag}> | Hijos: {len(hijos_v)}")
        imprimir_nodo(root_v, nivel=1, max_nivel=4)
        break
    else:
        print(f"  ❌ Intento {intento}: {raw_v}")

print("\n\n  Exploración completada.")
