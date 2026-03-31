# ============================================================
# scraper_votaciones_camara.py
# ============================================================

import re
import time
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CongresViz/1.0; datos publicos)"}
URL_DETALLE = "https://www.camara.cl/legislacion/sala_sesiones/votacion_detalle.aspx?prmIdVotacion={id}"
PAUSA   = 0.3
TIMEOUT = 8

ID_RECIENTE_CONOCIDO = 88519

MESES = {
    "enero":"01","febrero":"02","marzo":"03","abril":"04",
    "mayo":"05","junio":"06","julio":"07","agosto":"08",
    "septiembre":"09","octubre":"10","noviembre":"11","diciembre":"12"
}


def _parsear_fecha(texto: str) -> str:
    partes = texto.lower().strip().split()
    if len(partes) == 3:
        return f"{partes[0].zfill(2)}/{MESES.get(partes[1],'01')}/{partes[2]}"
    return texto


def _extraer_nombres(tabla) -> list[str]:
    """Extrae nombres simples (con coma) desde una tabla."""
    nombres = []
    for td in tabla.find_all("td"):
        nombre = td.get_text(strip=True)
        if nombre and len(nombre) > 3 and "," in nombre:
            nombres.append(nombre)
    return nombres


def _separar_pareos(texto_td: str) -> list[str]:
    """
    Separa pareos concatenados.
    'Bello Campos, María FranciscaconGonzález Villarroel, Mauro'
    → ['Bello Campos, María Francisca', 'González Villarroel, Mauro']

    El separador es 'con' seguido de letra mayúscula.
    """
    # Dividir en 'con' seguido de mayúscula o letra con tilde
    partes = re.split(r'con(?=[A-ZÁÉÍÓÚÑÜ])', texto_td)
    nombres = []
    for parte in partes:
        parte = parte.strip()
        if parte and "," in parte and len(parte) > 5:
            nombres.append(parte)
    return nombres


def obtener_votacion_camara(votacion_id: int) -> dict | None:
    url = URL_DETALLE.format(id=votacion_id)
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code != 200 or len(r.content) < 60000:
            return None

        soup = BeautifulSoup(r.content, "html.parser")

        # Extraer metadata
        datos = {}
        for ficha in soup.find_all(class_="datos-ficha"):
            dato_tag = ficha.find(class_="dato")
            info_tag = ficha.find(class_="info")
            if dato_tag and info_tag:
                clave = dato_tag.get_text(strip=True).replace(":", "").strip()
                valor = info_tag.get_text(strip=True)
                datos[clave] = valor
            else:
                texto = ficha.get_text(strip=True)
                if ":" in texto:
                    p = texto.split(":", 1)
                    datos[p[0].strip()] = p[1].strip()

        if not datos:
            return None

        tablas = soup.find_all("table")

        # Tabla 0 — conteos
        votos_si = votos_no = abstenciones = pareos = 0
        if tablas:
            nums = [c for c in [td.get_text(strip=True)
                    for td in tablas[0].find_all("td")] if c.isdigit()]
            if len(nums) >= 4:
                votos_si, votos_no, abstenciones, pareos = map(int, nums[:4])
            elif len(nums) >= 1:
                votos_si = int(nums[0])

        # Tabla 1 — A favor
        nombres_si  = _extraer_nombres(tablas[1]) if len(tablas) > 1 else []

        # Tabla 2 — En contra
        nombres_no  = _extraer_nombres(tablas[2]) if len(tablas) > 2 else []

        # Tabla 3 — Abstenciones o Pareos
        nombres_abs   = []
        nombres_pareo = []

        if len(tablas) > 3:
            for td in tablas[3].find_all("td"):
                texto_td = td.get_text(strip=True)
                if not texto_td:
                    continue
                # Detectar pareo: contiene "con" entre dos nombres
                if re.search(r'con[A-ZÁÉÍÓÚÑÜ]', texto_td):
                    nombres_pareo.extend(_separar_pareos(texto_td))
                elif "," in texto_td and len(texto_td) > 5:
                    nombres_abs.append(texto_td)

        # Tabla 4 — Pareos adicionales
        if len(tablas) > 4:
            for td in tablas[4].find_all("td"):
                texto_td = td.get_text(strip=True)
                if not texto_td:
                    continue
                if re.search(r'con[A-ZÁÉÍÓÚÑÜ]', texto_td):
                    nombres_pareo.extend(_separar_pareos(texto_td))

        # Construir detalles
        detalles = (
            [{"parlamentario": n, "seleccion": "Si"}         for n in nombres_si]  +
            [{"parlamentario": n, "seleccion": "No"}         for n in nombres_no]  +
            [{"parlamentario": n, "seleccion": "Abstencion"} for n in nombres_abs] +
            [{"parlamentario": n, "seleccion": "Pareo"}      for n in nombres_pareo]
        )

        boletin   = datos.get("Proyecto De Ley", datos.get("Proyecto de Ley", "")).strip()
        titulo    = datos.get("Materia", "").strip()
        fecha_raw = datos.get("Fecha", "").strip()
        fecha     = _parsear_fecha(fecha_raw) if fecha_raw else ""
        sesion    = datos.get("Sesión", "").strip()
        tramite   = datos.get("Trámite", "").strip()
        tipo_vot  = datos.get("Tipo de Votación", "").strip()
        quorum    = datos.get("Quorum", datos.get("Quórum", "")).strip()
        res_raw   = datos.get("Resultado", "").strip()

        if "aprobado" in res_raw.lower():
            resultado = "Aprobado"
        elif "rechazado" in res_raw.lower():
            resultado = "Rechazado"
        else:
            resultado = "Aprobado" if votos_si > votos_no else "Rechazado"

        if not boletin and not titulo:
            return None

        return {
            "id":            f"CAM-{votacion_id}",
            "boletin":       boletin,
            "titulo":        titulo,
            "camara":        "C.Diputados",
            "etapa":         tramite,
            "estado":        None,
            "sesion":        sesion,
            "fecha":         fecha,
            "tema":          titulo,
            "tipo_votacion": tipo_vot,
            "votos_si":      votos_si,
            "votos_no":      votos_no,
            "abstenciones":  abstenciones,
            "pareos":        pareos,
            "quorum":        quorum,
            "resultado":     resultado,
            "detalles":      detalles,
        }

    except Exception:
        return None


def obtener_votaciones_recientes_camara(cantidad: int = 100,
                                         verbose: bool = True) -> list[dict]:
    if verbose:
        print(f"  → Scraping últimas {cantidad} votaciones Cámara...")

    resultados = []
    vid        = ID_RECIENTE_CONOCIDO
    intentos   = 0
    max_intentos = cantidad + 20

    while len(resultados) < cantidad and intentos < max_intentos:
        vot = obtener_votacion_camara(vid)
        if vot:
            resultados.append(vot)
        vid      -= 1
        intentos += 1
        time.sleep(PAUSA)

    if verbose:
        print(f"  ✅ Votaciones Cámara obtenidas: {len(resultados)}")

    return resultados


if __name__ == "__main__":
    print("Verificando separación de pareos...\n")
    v = obtener_votacion_camara(88519)
    if v:
        pareos = [d for d in v['detalles'] if d['seleccion'] == 'Pareo']
        print(f"Votación {v['id']} — pareos: {len(pareos)}")
        for p in pareos:
            print(f"  {p['parlamentario']}")

    # Probar con votación que tiene pareos concatenados
    v2 = obtener_votacion_camara(88491)
    if v2:
        pareos2 = [d for d in v2['detalles'] if d['seleccion'] == 'Pareo']
        print(f"\nVotación {v2['id']} — pareos: {len(pareos2)}")
        for p in pareos2:
            print(f"  {p['parlamentario']}")
