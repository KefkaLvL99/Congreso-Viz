# ============================================================
# scraper_diputados.py
# ============================================================
# Extrae la lista completa de diputados desde el sitio oficial
# de la Cámara de Diputadas y Diputados de Chile.
#
# Estrategia:
#   1. Obtiene todos los IDs y nombres desde la página principal
#   2. Por cada diputado, visita su perfil para obtener
#      región, distrito, partido, bancada y email
#   3. Retorna una lista de diccionarios lista para guardar en BD
#
# Uso:
#   from scraper_diputados import obtener_diputados
#   diputados = obtener_diputados()
# ============================================================

import re
import time
import requests
from bs4 import BeautifulSoup

# ── CONFIGURACIÓN ────────────────────────────────────────────

URL_LISTADO = "https://www.camara.cl/diputados/diputados.aspx"
URL_PERFIL  = "https://www.camara.cl/diputados/detalle/mociones.aspx?prmID={id}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0; datos publicos)"
}

# Pausa entre requests para no saturar el servidor
PAUSA_SEGUNDOS = 0.5
TIMEOUT = 15


# ── FUNCIONES ────────────────────────────────────────────────

def obtener_ids_desde_listado() -> list[dict]:
    """
    Extrae todos los IDs y nombres de diputados desde la página principal.
    Filtra falsos positivos (boletines de ley que también tienen prmID).
    Retorna lista de dicts con {id, nombre_raw}
    """
    r = requests.get(URL_LISTADO, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, "html.parser")

    ids_vistos = set()
    diputados = []

    for link in soup.find_all("a", href=True):
        href = link["href"]
        match = re.search(r"prmID=(\d+)", href)
        if not match:
            continue

        pid   = match.group(1)
        nombre = link.get_text(strip=True)

        # Filtrar:
        # - IDs ya vistos
        # - Sin nombre
        # - Nombres que parecen boletines (contienen "-" como "14077-18")
        # - Nombres muy cortos o que son tratamientos solos ("Sr.", "Sra.")
        if (pid in ids_vistos
                or not nombre
                or re.match(r"^\d+-\d+$", nombre)
                or nombre in ("Sr.", "Sra.", "")):
            continue

        # Limpiar prefijos de tratamiento
        nombre_limpio = re.sub(r"^(Sr\.|Sra\.)\s*", "", nombre).strip()

        if len(nombre_limpio) < 4:
            continue

        ids_vistos.add(pid)
        diputados.append({
            "id":        pid,
            "nombre_raw": nombre_limpio,
        })

    return diputados


def parsear_nombre(nombre_raw: str) -> dict:
    """
    Intenta separar apellido y nombre desde el formato del sitio.
    El listado usa 'Apellido, Nombre' pero los perfiles usan 'Nombre Apellido'.
    Retorna dict con nombre, apellido_paterno, nombre_completo.
    """
    if "," in nombre_raw:
        # Formato "Apellido, Nombre"
        partes = nombre_raw.split(",", 1)
        apellido = partes[0].strip()
        nombre   = partes[1].strip() if len(partes) > 1 else ""
        nombre_completo = f"{nombre} {apellido}".strip()
    else:
        # Formato "Nombre Apellido Apellido"
        partes = nombre_raw.split()
        nombre  = partes[0] if partes else nombre_raw
        apellido = " ".join(partes[1:]) if len(partes) > 1 else ""
        nombre_completo = nombre_raw

    return {
        "nombre":          nombre,
        "apellido_paterno": apellido,
        "nombre_completo": nombre_completo,
    }


def obtener_perfil(diputado_id: str) -> dict:
    """
    Visita el perfil individual de un diputado y extrae:
    región, distrito, período, partido, bancada y email.
    """
    url = URL_PERFIL.format(id=diputado_id)
    datos = {
        "region":     None,
        "distrito":   None,
        "periodo":    None,
        "partido":    None,
        "bancada":    None,
        "email":      None,
    }

    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code != 200:
            return datos

        soup = BeautifulSoup(r.content, "html.parser")

        # ── Extraer campos desde los <br> anidados ────────────
        # El HTML tiene la forma:
        #   Distrito: Nº 10 <br>
        #   Región: Región Metropolitana <br>
        #   Partido: UDI <br>
        texto_completo = soup.get_text(separator="\n")

        for linea in texto_completo.split("\n"):
            linea = linea.strip()
            if linea.startswith("Región:"):
                datos["region"] = linea.replace("Región:", "").strip()
            elif linea.startswith("Distrito:"):
                datos["distrito"] = linea.replace("Distrito:", "").strip()
            elif linea.startswith("Período:"):
                datos["periodo"] = linea.replace("Período:", "").strip()
            elif linea.startswith("Partido:"):
                datos["partido"] = linea.replace("Partido:", "").strip()
            elif linea.startswith("Bancada:"):
                datos["bancada"] = linea.replace("Bancada:", "").strip()

        # ── Extraer email (está protegido por Cloudflare) ─────
        # Cloudflare ofusca los emails con data-cfemail
        # Intentamos extraerlo del atributo o del texto visible
        email_span = soup.find("span", class_="__cf_email__")
        if email_span:
            # El texto visible suele ser el email real en scraping
            email_visible = email_span.get_text(strip=True)
            if "@" in email_visible:
                datos["email"] = email_visible

        # Si no lo encontramos con el span, buscamos en links mailto
        if not datos["email"]:
            for a in soup.find_all("a", href=True):
                if "mailto:" in a["href"]:
                    datos["email"] = a["href"].replace("mailto:", "").strip()
                    break

    except Exception as e:
        print(f"    ⚠️  Error perfil {diputado_id}: {e}")

    return datos


def obtener_diputados(verbose: bool = True) -> list[dict]:
    """
    Función principal — extrae todos los diputados con sus datos.
    verbose=True muestra progreso en terminal.
    Retorna lista de dicts lista para guardar en base de datos.
    """
    if verbose:
        print("Extrayendo IDs desde página principal...")

    base = obtener_ids_desde_listado()

    if verbose:
        print(f"Encontrados: {len(base)} diputados")
        print("Extrayendo perfiles individuales...\n")

    diputados = []

    for i, d in enumerate(base, 1):
        if verbose:
            print(f"  [{i:03d}/{len(base)}] {d['nombre_raw']}...", end=" ")

        # Parsear nombre
        nombre_data = parsear_nombre(d["nombre_raw"])

        # Obtener perfil
        perfil = obtener_perfil(d["id"])

        # Combinar todo
        diputado = {
            "id":              d["id"],
            "nombre_completo": nombre_data["nombre_completo"],
            "nombre":          nombre_data["nombre"],
            "apellido_paterno": nombre_data["apellido_paterno"],
            "region":          perfil["region"],
            "distrito":        perfil["distrito"],
            "periodo":         perfil["periodo"],
            "partido":         perfil["partido"],
            "bancada":         perfil["bancada"],
            "email":           perfil["email"],
            "url_perfil":      URL_PERFIL.format(id=d["id"]),
        }

        diputados.append(diputado)

        if verbose:
            partido = perfil["partido"] or "?"
            print(f"✅ {perfil['region'] or '?'} · {partido}")

        # Pausa para no saturar el servidor
        time.sleep(PAUSA_SEGUNDOS)

    if verbose:
        print(f"\nTotal diputados extraídos: {len(diputados)}")

    return diputados


# ── PRUEBA RÁPIDA (solo 3 diputados) ─────────────────────────
if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════╗")
    print("║   Scraper Diputados - Cámara de Chile            ║")
    print("╚══════════════════════════════════════════════════╝\n")

    # Para la prueba solo tomamos los primeros 3
    print("── PRUEBA con 3 diputados ──\n")

    base = obtener_ids_desde_listado()
    print(f"IDs encontrados: {len(base)}\n")

    for d in base[1:4]:  # saltamos el primero (suele ser el presidente)
        print(f"Procesando: {d['nombre_raw']} (ID {d['id']})")
        perfil = obtener_perfil(d["id"])
        nombre = parsear_nombre(d["nombre_raw"])
        print(f"  Nombre completo : {nombre['nombre_completo']}")
        print(f"  Región          : {perfil['region']}")
        print(f"  Distrito        : {perfil['distrito']}")
        print(f"  Partido         : {perfil['partido']}")
        print(f"  Bancada         : {perfil['bancada']}")
        print(f"  Email           : {perfil['email']}")
        print()
        time.sleep(0.5)

    print("Prueba completada. Si los datos se ven bien,")
    print("integrar en scheduler.py para sincronización completa.")
