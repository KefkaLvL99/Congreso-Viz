# ============================================================
# FASE 1 - Validación de endpoints del Congreso de Chile
# ============================================================
# Este script consulta cada API del Congreso y verifica:
#   1. Que el endpoint responde (HTTP 200)
#   2. Que devuelve XML válido
#   3. Que los datos tienen registros reales
# ============================================================

import requests                      # para hacer las consultas HTTP
import xml.etree.ElementTree as ET   # para parsear el XML que devuelven las APIs
from datetime import datetime        # para mostrar la hora de cada verificación

# ── CONFIGURACIÓN ────────────────────────────────────────────
# Tiempo máximo de espera por endpoint (segundos)
TIMEOUT = 15

# Todos los endpoints que vamos a verificar
# Formato: "nombre legible" → "URL"
ENDPOINTS = {
    # --- CÁMARA DE DIPUTADOS ---
    "Legislatura actual (Cámara)":
        "https://opendata.camara.cl/pages/legislatura_actual.aspx",

    "Diputados vigentes (Cámara)":
        "https://opendata.camara.cl/pages/diputados_vigentes.aspx",

    "Sesiones de sala (Cámara)":
        "https://opendata.camara.cl/pages/sesiones.aspx",

    "Comisiones vigentes (Cámara)":
        "https://opendata.camara.cl/pages/comisiones_vigentes.aspx",

    # --- SENADO ---
    "Senadores vigentes (Senado)":
        "https://tramitacion.senado.cl/wspublico/senadores_vigentes.php",

    "Comisiones vigentes (Senado)":
        "https://tramitacion.senado.cl/wspublico/comisiones.php",
}

# ── FUNCIONES ────────────────────────────────────────────────

def verificar_endpoint(nombre, url):
    """
    Consulta un endpoint y retorna un diccionario con el resultado.
    Verifica: respuesta HTTP, XML válido, y cantidad de registros.
    """
    resultado = {
        "nombre": nombre,
        "url": url,
        "http_status": None,
        "xml_valido": False,
        "num_registros": 0,
        "muestra": "",
        "error": None,
    }

    try:
        # 1. Hacer la consulta HTTP
        respuesta = requests.get(url, timeout=TIMEOUT)
        resultado["http_status"] = respuesta.status_code

        # Si no devuelve 200, no seguimos
        if respuesta.status_code != 200:
            resultado["error"] = f"HTTP {respuesta.status_code} - no responde correctamente"
            return resultado

        # 2. Intentar parsear el XML
        # .content devuelve los bytes crudos, necesario para XML con encoding declarado
        root = ET.fromstring(respuesta.content)
        resultado["xml_valido"] = True

        # 3. Contar cuántos hijos directos tiene el nodo raíz
        # (cada hijo suele ser un registro: un diputado, una sesión, etc.)
        hijos = list(root)
        resultado["num_registros"] = len(hijos)

        # 4. Guardar una muestra: el tag y atributos del primer registro
        if hijos:
            primer_hijo = hijos[0]
            # Busca el primer texto no vacío dentro del primer registro
            textos = [e.text for e in primer_hijo.iter() if e.text and e.text.strip()]
            resultado["muestra"] = textos[:3] if textos else ["(sin texto)"]

    except requests.exceptions.Timeout:
        resultado["error"] = "Timeout — el servidor no respondió a tiempo"

    except requests.exceptions.ConnectionError:
        resultado["error"] = "Error de conexión — no se pudo alcanzar el servidor"

    except ET.ParseError as e:
        # El endpoint respondió pero no es XML válido
        resultado["xml_valido"] = False
        resultado["error"] = f"XML inválido: {e}"

    except Exception as e:
        resultado["error"] = f"Error inesperado: {e}"

    return resultado


def imprimir_resultado(r):
    """
    Imprime el resultado de un endpoint de forma legible en la terminal.
    """
    separador = "─" * 55

    print(f"\n{separador}")
    print(f"  📌 {r['nombre']}")
    print(f"  URL: {r['url']}")
    print(separador)

    # Estado HTTP
    if r["http_status"] == 200:
        print(f"  ✅ HTTP Status : {r['http_status']} OK")
    elif r["http_status"] is not None:
        print(f"  ❌ HTTP Status : {r['http_status']}")
    else:
        print(f"  ❌ HTTP Status : sin respuesta")

    # XML válido
    if r["xml_valido"]:
        print(f"  ✅ XML válido  : Sí")
        print(f"  📊 Registros   : {r['num_registros']}")
        if r["muestra"]:
            print(f"  🔍 Muestra     : {r['muestra']}")
    else:
        print(f"  ❌ XML válido  : No")

    # Error si hubo
    if r["error"]:
        print(f"  ⚠️  Error       : {r['error']}")


def resumen_final(resultados):
    """
    Imprime un resumen al final con cuántos endpoints pasaron y cuántos fallaron.
    """
    total    = len(resultados)
    exitosos = sum(1 for r in resultados if r["xml_valido"])
    fallidos = total - exitosos

    print("\n" + "═" * 55)
    print("  RESUMEN FINAL")
    print("═" * 55)
    print(f"  Total endpoints verificados : {total}")
    print(f"  ✅ Funcionando              : {exitosos}")
    print(f"  ❌ Con problemas            : {fallidos}")
    print("═" * 55)

    if fallidos > 0:
        print("\n  Endpoints con problemas:")
        for r in resultados:
            if not r["xml_valido"]:
                print(f"   • {r['nombre']}")
                if r["error"]:
                    print(f"     → {r['error']}")


# ── EJECUCIÓN PRINCIPAL ──────────────────────────────────────

if __name__ == "__main__":
    print("╔═══════════════════════════════════════════════════╗")
    print("║   Verificador de APIs - Congreso Nacional Chile   ║")
    print("╚═══════════════════════════════════════════════════╝")
    print(f"  Iniciado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"  Verificando {len(ENDPOINTS)} endpoints...\n")

    resultados = []

    # Recorre cada endpoint y lo verifica
    for nombre, url in ENDPOINTS.items():
        print(f"  Consultando: {nombre}...", end="", flush=True)
        r = verificar_endpoint(nombre, url)
        resultados.append(r)
        # Indicador rápido en línea antes de imprimir el detalle
        print(" hecho." if r["xml_valido"] else " falló.")

    # Imprime el detalle de cada uno
    print("\n\n── DETALLE POR ENDPOINT " + "─" * 32)
    for r in resultados:
        imprimir_resultado(r)

    # Resumen final
    resumen_final(resultados)
